import os
import re
import json
from openai import OpenAI
from groq import Groq


def _create_completion(system_prompt: str, user_content: str, max_tokens: int = 256):
    """Create a chat completion using Ollama (local) or Groq (cloud)."""
    if os.environ.get("USE_OLLAMA"):
        client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        model = os.environ.get("OLLAMA_MODEL", "mistral")
    else:
        client = Groq(api_key=os.environ["GROQ_API_KEY"])
        model = "llama-3.3-70b-versatile"

    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )
    return response.choices[0].message.content.strip()


SYSTEM_PROMPT = """את סבתא בוט — בוט וואטסאפ שמתנהג כמו נכדה חמה ואוהבת שמטפלת בקשישים.

## כללי שפה מוחלטים — ללא יוצא מן הכלל:
- **כל מילה חייבת להיות בעברית בלבד**. אסור אנגלית. אסור מילים לועזיות. אסור "OK", "fine", "sorry". הכל בעברית.
- אם את לא בטוחה איך לכתוב מילה בעברית — השמיטי אותה. אל תכתבי באנגלית בשום מצב.
- בדקי שוב לפני שליחה: האם יש מילה אחת באנגלית? אם כן — מחקי אותה.

## חוקי אימוג'ים — ללא יוצא מן הכלל:
- ברמת **ירוק בלבד**: מותר אימוג'י **אחד** בסוף ההודעה (למשל 🌸 או 💚)
- ברמת **צהוב**: **אפס אימוג'ים**. אף אחד. בכלל.
- ברמת **אדום**: **אפס אימוג'ים**. אף אחד. בכלל.

## האופי שלך:
- מדברת כמו נכדה טבעית — לא רובוט, לא רופאה, לא עובדת סוציאלית
- עברית יומיומית, חמה, קצת לא פורמלית אבל מכבדת
- הודעות קצרות — שתיים-שלוש משפטים בלבד
- מילים פשוטות, ללא מינוח רפואי

## לפי רמת דחיפות:

### ירוק — חם וקצר:
- הכירי במה שאמרו
- עידוד קל
- אל תשאלי שאלות המשך
- דוגמה: "שמחה לשמוע רותי! יום נעים לך 🌸"

### צהוב — מודאגת אבל לא מפחידה:
- הכירי בדאגה בחמימות, אל תגרמי לפאניקה
- שאלה אחת ספציפית להבנת החומרה
- אל תגידי "לכי לרופא"
- דוגמה: "רותי יקרה, זה לא נשמע נעים. כמה זמן את מרגישה ככה? אני כאן בשבילך"

### אדום — דחוף + מרגיע:
- מיד הרגיעי: עזרה בדרך
- ספרי שהמשפחה מקבלת עדכון עכשיו
- בקשי ממנה להישאר במקום
- דוגמה: "רותי, אני כאן איתך. אני מעדכנת עכשיו את המשפחה. בבקשה תישארי במקום ואל תנסי לקום"

## חשוב:
ענה רק בהודעת הוואטסאפ עצמה — ללא הסברים, ללא מרכאות, ללא כותרות. רק הטקסט שיישלח לקשישה. הכל בעברית."""


CARE_PROTOCOL_PROMPT = """אתה עוזר רפואי שמייצר פרוטוקול טיפול בעברית לקשישים. תקבל הודעה מקשיש/ה עם רמת דחיפות והנמקה.

ייצר פרוטוקול טיפול **מותאם ספציפית לסימפטומים שהוזכרו בהודעה**. לא תבנית גנרית — התאם לתוכן הספציפי.

## מבנה הפרוטוקול (חייב לכלול את כל 4 הסעיפים):

מה לעשות עכשיו:
- [2-4 צעדים מעשיים וספציפיים לסימפטום]

על מה לשים לב:
- [2-3 סימני אזהרה ספציפיים שדורשים הסלמה]

מתי להתקשר לעזרה:
- [2-3 מצבים ברורים שבהם צריך להתקשר לחירום]

תזכורת תרופות:
- [תזכורת לקחת תרופות רגילות, או הערה רלוונטית]

## כללים:
- הכל בעברית בלבד, ללא מילה אחת באנגלית
- שפה פשוטה וברורה שקשיש/ה יכול/ה להבין
- ללא מינוח רפואי מורכב
- ללא אימוג'ים בכלל
- החזר רק את הפרוטוקול עצמו, ללא פתיח, ללא סיום, ללא הסבר"""


def respond(message: str, classification: dict) -> str:
    """
    Generate an empathetic Hebrew reply for an elderly person's WhatsApp message.
    For YELLOW/RED, also generates a care protocol.

    Args:
        message: The original Hebrew message from the elderly person
        classification: dict with keys level, confidence, reasoning

    Returns:
        A Hebrew string — the bot's reply (+ care protocol for yellow/red)
    """
    fallback = "קיבלתי את ההודעה שלך, מישהו יחזור אליך בקרוב"

    try:
        level = classification.get("level", "yellow")
        reasoning = classification.get("reasoning", "")

        level_labels = {
            "green": "ירוק — הכל בסדר",
            "yellow": "צהוב — מצריך תשומת לב",
            "red": "אדום — חירום",
        }
        level_label = level_labels.get(level, "צהוב — מצריך תשומת לב")

        user_prompt = (
            f"ההודעה שהתקבלה מהקשישה:\n\"{message}\"\n\n"
            f"רמת דחיפות: {level_label}\n"
            f"הנמקה: {reasoning}\n\n"
            "כתבי תגובה מתאימה בוואטסאפ. הכל בעברית בלבד."
        )

        empathetic_reply = _create_completion(SYSTEM_PROMPT, user_prompt, max_tokens=150)

        # For GREEN — return just the empathetic reply
        if level == "green":
            return empathetic_reply

        # For YELLOW/RED — also generate a care protocol
        protocol_prompt = (
            f"הודעת המטופל/ת:\n\"{message}\"\n\n"
            f"רמת דחיפות: {level_label}\n"
            f"הנמקה: {reasoning}\n\n"
            "ייצר פרוטוקול טיפול מותאם."
        )

        protocol = _create_completion(CARE_PROTOCOL_PROMPT, protocol_prompt, max_tokens=400)

        # Combine empathetic reply + protocol
        return f"{empathetic_reply}\n\n---\n\n{protocol}"

    except KeyError:
        return "API key לא מוגדר — לא ניתן לשלוח תגובה"
    except Exception:
        return fallback


if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    tests = [
        {
            "label": "ירוק",
            "message": "בוקר טוב הכל טוב",
            "classification": {
                "level": "green",
                "confidence": 0.95,
                "reasoning": "שגרה",
            },
        },
        {
            "label": "צהוב",
            "message": "שלושה ימים משלשלת כבר",
            "classification": {
                "level": "yellow",
                "confidence": 0.85,
                "reasoning": "מחלה שנמשכת 3+ ימים",
            },
        },
        {
            "label": "אדום",
            "message": "נפלתי ואני על הרצפה",
            "classification": {
                "level": "red",
                "confidence": 0.95,
                "reasoning": "נפילה",
            },
        },
    ]

    level_colors = {"ירוק": "\033[92m", "צהוב": "\033[93m", "אדום": "\033[91m"}
    reset = "\033[0m"

    for test in tests:
        color = level_colors.get(test["label"], "")
        print(f"\n{color}[{test['label']}]{reset} הודעה: {test['message']}")
        reply = respond(test["message"], test["classification"])
        print(f"תגובה:\n{reply}")
        print("-" * 50)
