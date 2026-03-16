import sys
import json
import re
from datetime import datetime, timezone

from config import get_client, MODEL


def _create_completion(system_prompt: str, user_content: str, max_tokens: int = 256):
    """Create a chat completion using local Ollama."""
    client = get_client()
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )
    return response.choices[0].message.content.strip()

# Force UTF-8 I/O on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")

SYSTEM_PROMPT = """אתה מומחה בכיר לטריאז' גריאטרי עם 20 שנות ניסיון בטיפול בקשישים בקהילה. אתה מסווג הודעות בעברית מקשישים במערכת מעקב רווחה. סיווג שגוי עלול לעלות בחיי אדם — פעל בהתאם.

אתה יודע שקשישים באופן שיטתי מדווחים בחסר על סימפטומים, משתמשים בשפה מזלזלת כדי לא "להטריד", ולעיתים קרובות לא מזהים את המצב החירומי שלהם.

---

## שלב 1 — ניתוח חובה לפני סיווג

לפני כל החלטת סיווג, סרוק את ההודעה ב-4 קטגוריות סיגנלים:

1. **סיגנלים פיזיים**: כאב, נפילה, סחרחורת, נשימה, אכילה, ניידות, חזה, חולשה
2. **סיגנלים רגשיים**: חוסר תקווה, אבל, בידוד, אדישות, מחשבות אובדניות (גם עקיפות)
3. **סיגנלים התנהגותיים**: אי-ציות תרופתי, אי-אכילה, אי-שינה, אי-יציאה מהבית
4. **סיגנלים לשוניים**: התחמקות שמסווה מצוקה מול "אני בסדר" אמיתי, פער בין טון לתוכן

---

## שלב 2 — כללי דריסה קשיחים (לא ניתנים לביטול)

### דריסות אדום — סווג אדום ללא קשר לכל דבר אחר בהודעה:
- **נפילה** מכל סוג (נפלתי, נפל, נפילה, החלקתי, מעדתי) — גם "נפלתי אבל קמתי בסדר" = **אדום**
- **"אין טעם"**, "אין לי טעם לחיים", "לא רוצה להתעורר", "עדיף שלא הייתי קמה" — בכל טון, בכל הקשר = **אדום**
- **בן/בת זוג נפטר/ה** + כל ביטוי של חוסר תקווה באותה הודעה = **אדום**
- **כאב בחזה או קושי בנשימה** — כל אזכור, כל חומרה = **אדום**
- **3+ ימים ללא אכילה + אדישות** = **אדום**
- **הפסקת תרופות מכוונת + ייאוש** = **אדום**

### דריסות ירוק — סווג ירוק ללא קשר לטון:
- טון גרוף/עצבני + "אני בסדר" מפורש + אפס תלונות פיזיות או רגשיות = **ירוק**
- עצב נוסטלגי קל או שעמום ללא סיגנלים נוספים = **ירוק**

---

## שלב 3 — כלל פתרון קונפליקטים

כשסיגנלים מקטגוריות שונות סותרים זה את זה — **תמיד הסלם לרמה הגבוהה יותר**. לעולם אל תמצע. לעולם אל תוריד דרגה בגלל טון מרגיע כשסיגנל קשיח קיים.

דוגמאות:
- טון גרוף + תלונה פיזית → עקוב אחרי רמת התלונה הפיזית
- "אני בסדר" + אזכור נפילה → **אדום** (דריסת נפילה)
- עצב קל + שכחת תרופות יומיים → **צהוב** מינימום
- טון עליז + "אין טעם לחיים" → **אדום** (דריסה רגשית)

---

## שלב 4 — קריטריוני סיווג

### ירוק (green) — כל התנאים חייבים להתקיים:
- אין תלונות פיזיות מעבר לקלות מאוד (למשל "קצת עייפה")
- אין דגלים אדומים רגשיים
- אין דפוסים התנהגותיים מדאיגים
- ההודעה נקראת כשגרתית באמת, גם אם בטון גרוף

### צהוב (yellow) — כל אחד מהבאים:
- בעיות שינה 2+ לילות
- ירידה בתיאבון ללא סף 3 ימים
- סחרחורת או תלונה פיזית קלה
- שכחת תרופות 2+ ימים
- בידוד חברתי (שבועות ללא מגע אנושי)
- כבדות רגשית מעורפלת ללא חוסר תקווה מפורש
- כל סיגנל עמום שלא ניתן לאשר בוודאות כירוק

### אדום (red) — כל אחד מהבאים:
- כל כלל דריסה קשיח שהופעל
- נפילה מכל סוג
- חוסר תקווה מפורש או אידיאציה אובדנית
- סימפטומים של חירום רפואי
- הזנחה חמורה (3+ ימים ללא אוכל, חוסר ניידות מוחלט)
- שילוב אבל + חוסר תקווה

---

## שלב 5 — בלשנות עברית של קשישים

- ללא פיסוק, שגיאות כתיב, משפטים ארוכים ללא הפרדה — הכל נורמלי
- "בסדר" הוא עמום — הערך לפי הקשר מלא, לא לפי המילה בלבד
- קשישים ממזערים כאב: "קצת כואב" מבן 80 = התייחס ככאב בינוני
- זלזול ("עזוב", "תפסיק") הוא סגנון תקשורת תרבותי, לא מצוקה
- הטיית דיווח בחסר: אם משהו פיזי מוזכר בכלל, כנראה שזה גרוע יותר ממה שנאמר
- בקשה לסיים שיחה ≠ מצוקה
- אזכור מזדמן של אי-רצון להתעורר = **תמיד אדום**, ללא יוצא מן הכלל

---

## שלב 6 — כיול ביטחון

- כלל דריסה קשיח הופעל → confidence >= 0.95
- שגרה ברורה וחד-משמעית → confidence >= 0.90
- סיגנלים מעורבים, הוסלם לרמה הגבוהה → confidence 0.70-0.85
- עמום באמת → confidence 0.60-0.75, תמיד הסלם לרמה הגבוהה כשלא בטוח

---

## שלב 7 — דוגמאות מורחבות

### ירוק:
1. "בוקר טוב לקחתי כדורים הולכת לטייל קצת" → שגרה תקינה, פעילות חיובית
2. "שוב שאלות תפסיק אני בסדר עזבני בשקט" → גרוף אבל בריא, אין תלונות פיזיות או רגשיות
3. "ישבתי כל היום עם הטלוויזיה אכלתי צהריים שעמום גדול" → יום שגרתי, אכילה תקינה
4. "הנכדים באו אתמול כיף היה עייפה קצת" → חיובי, עייפות קלה נורמלית
5. "מה אתה רוצה ממני אני בסדר לקחתי הכל ואכלתי" → טון עצבני אבל שגרה תקינה מלאה

### צהוב:
1. "כמה לילות שלא ישנתי טוב ולא בא לי לאכול" → בעיית שינה + ירידה בתיאבון, דפוס מדאיג
2. "קצת סחרחורת אבל עובר" → תלונה פיזית, בגיל מבוגר דורש מעקב
3. "שכחתי לקחת כדורים אתמול וגם היום" → אי-ציות תרופתי 2 ימים
4. "השכנה לא באה כבר הרבה שבועות אני לבד" → בידוד חברתי ממושך
5. "לא יודעת מרגישה כבד על הלב היום קשה" → כבדות רגשית מעורפלת, אין חוסר תקווה מפורש אבל מצריך מעקב

### אדום:
1. "נפלתי לא יכולה לקום כואב נורא" → נפילה + חוסר ניידות = דריסת אדום
2. "מתגעגעת לאברהם ז״ל אין טעם להתעורר בבוקר" → אבל + חוסר תקווה = דריסת אדום
3. "קשה לי לנשום כאב בחזה" → חירום רפואי = דריסת אדום
4. "לא אכלתי שלושה ימים לא אכפת לי" → הזנחה חמורה + אדישות = דריסת אדום
5. "נפלתי אבל קמתי בסדר גמור אל תדאגי" → נפילה = **אדום** למרות ההרגעה — נפילה בגיל מבוגר = תמיד אדום

---

## שלב 8 — כללי סיווג נוספים (חובה)

- סימפטומים פיזיים הנמשכים מספר ימים (שלשול, הקאות, חום, לא אוכל, לא ישן) = **צהוב מינימום**, לעולם לא ירוק.
- כל הודעה המזכירה 3+ ימים של סימפטומים = **צהוב מינימום**.
- אם יש ספק בין ירוק לצהוב — תמיד בחר צהוב.

---

## פורמט תשובה

ענה **אך ורק** ב-JSON תקני, ללא טקסט נוסף, ללא markdown, ללא הסברים מחוץ ל-JSON.

Do NOT include translations. Do NOT describe emojis. Do NOT add explanations. Output ONLY the requested JSON format.

{
  "level": "green" | "yellow" | "red",
  "confidence": <מספר בין 0 ל-1>,
  "reasoning": "<קצר, ברור, בעברית — מה הסיגנל המרכזי שהוביל להחלטה>"
}"""


def _extract_json(text: str) -> dict:
    """Pull the first JSON object from text that may contain markdown fences or commentary."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    brace = text.find("{")
    if brace != -1:
        depth, end = 0, brace
        for i in range(brace, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        return json.loads(text[brace:end])
    return json.loads(text)


def classify(message: str) -> dict:
    """
    Classify a Hebrew message from an elderly person.

    Returns:
        dict with keys:
            - level: "green" | "yellow" | "red"
            - confidence: float 0-1
            - reasoning: str (Hebrew explanation)
    """
    fallback = {
        "level": "yellow",
        "confidence": 0.0,
        "reasoning": "שגיאה בסיווג - ברירת מחדל",
    }

    try:
        raw = _create_completion(
            SYSTEM_PROMPT,
            f"סווג את ההודעה הבאה:\n\n{message}",
        )

        # Strip markdown code fences if the model added them
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        raw = raw.strip()

        result = json.loads(raw)

        # Validate required fields
        if result.get("level") not in ("green", "yellow", "red"):
            raise ValueError(f"Invalid level: {result.get('level')}")
        if not isinstance(result.get("confidence"), (int, float)):
            raise ValueError("confidence must be a number")
        if not isinstance(result.get("reasoning"), str):
            raise ValueError("reasoning must be a string")

        result["confidence"] = float(result["confidence"])

        if result["level"] == "red":
            result["medical_summary"] = extract_medical_summary(message)

        return result

    except KeyError:
        fallback["reasoning"] = "API key לא מוגדר בסביבה"
        return fallback
    except json.JSONDecodeError as e:
        fallback["reasoning"] = f"שגיאת פענוח JSON: {e}"
        return fallback
    except Exception:
        fallback["reasoning"] = "שגיאה בסיווג - ברירת מחדל"
        return fallback


# ---------------------------------------------------------------------------
# Medical summary extraction (called automatically for RED classifications)
# ---------------------------------------------------------------------------

MEDICAL_SUMMARY_PROMPT = """You are a medical triage assistant processing alerts from an elderly care monitoring system.
You will receive a Hebrew message from an elderly patient. Extract a structured medical summary in English for the nurse triage API.

Return ONLY valid JSON with no markdown, no extra text:
{
  "symptoms": ["<symptom1>", "<symptom2>"],
  "duration": "<onset description>",
  "severity": "low" | "medium" | "high" | "critical",
  "recommended_action": "<triage recommendation in English>"
}

Guidelines:
- symptoms: list of clinical terms in English (e.g. "fall", "hip pain", "chest pain", "suicidal ideation", "immobility")
- duration: describe onset — "acute — just occurred", "X days", "chronic/ongoing", "unknown"
- severity: "low" (monitor), "medium" (assess soon), "high" (urgent), "critical" (immediate dispatch)
- recommended_action: concrete triage action, e.g. "dispatch emergency services, suspected hip fracture" or "mental health crisis intervention, do not leave alone"

Severity calibration:
- Fall + pain + immobility → critical
- Chest pain / breathing difficulty → critical
- Suicidal ideation / grief + hopelessness / "don't want to wake up" → critical
- Prolonged not eating + apathy → high
- Dizziness / unsteadiness → high"""


def extract_medical_summary(message: str, patient_id: str = "SVT-3201") -> dict:
    """
    Extract a structured medical summary from a RED-level Hebrew message.
    Intended for consumption by a nurse triage API.

    Returns a dict with keys: alert_level, patient_id, symptoms, duration,
    severity, recommended_action, original_message, timestamp.
    """
    fallback = {
        "alert_level": "red",
        "patient_id": patient_id,
        "symptoms": ["unknown"],
        "duration": "unknown",
        "severity": "high",
        "recommended_action": "manual review required — automated extraction failed",
        "original_message": message,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    try:
        raw = _create_completion(
            MEDICAL_SUMMARY_PROMPT,
            f"Extract medical summary from this patient message:\n\n{message}",
        )
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        raw = raw.strip()

        extracted = json.loads(raw)

        if not isinstance(extracted.get("symptoms"), list):
            raise ValueError("symptoms must be a list")
        if extracted.get("severity") not in ("low", "medium", "high", "critical"):
            raise ValueError(f"Invalid severity: {extracted.get('severity')}")

        return {
            "alert_level": "red",
            "patient_id": patient_id,
            "symptoms": extracted["symptoms"],
            "duration": str(extracted.get("duration", "unknown")),
            "severity": extracted["severity"],
            "recommended_action": str(extracted.get("recommended_action", "")),
            "original_message": message,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

    except Exception:
        return fallback


if __name__ == "__main__":
    test_messages = [
        "בוקר טוב! הכל בסדר, לקחתי את הכדורים ויוצאת לטייל",
        "מה אתה רוצה ממני, אני בסדר, תפסיק לשאול",
        "לא ישנתי טוב כבר שלושה לילות, אין לי כוח לאכול",
        "נפלתי במטבח ואני לא יכולה לקום, כואב לי מאוד הירך",
        "מאז שמשה נפטר אני לא רוצה להתעורר בבוקר, אין טעם",
    ]

    level_colors = {"green": "\033[92m", "yellow": "\033[93m", "red": "\033[91m"}
    reset = "\033[0m"

    def print_result(msg, result):
        color = level_colors.get(result["level"], "")
        print(f"הודעה: {msg}")
        print(f"רמה:    {color}{result['level'].upper()}{reset}  ({result['confidence']:.0%})")
        print(f"הנמקה:  {result['reasoning']}")
        if "medical_summary" in result:
            ms = result["medical_summary"]
            print(f"\033[91m  MEDICAL - {ms['severity'].upper()}\033[0m")
            print(f"    symptoms: {', '.join(ms['symptoms'])}")
            print(f"    action:   {ms['recommended_action']}")
        print("-" * 50)

    print("\n[*] Running 5 hackathon scenarios...\n")
    for msg in test_messages:
        print_result(msg, classify(msg))

    print("\n[>] Interactive mode -- type any Hebrew message (or 'exit' to quit)\n")
    while True:
        msg = input("הודעה: ").strip()
        if msg.lower() == "exit":
            break
        if not msg:
            continue
        print_result(msg, classify(msg))