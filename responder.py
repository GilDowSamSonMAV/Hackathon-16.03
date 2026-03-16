import os
from groq import Groq

SYSTEM_PROMPT = """את סבתא בוט — בוט וואטסאפ שמתנהג כמו נכדה חמה ואוהבת שמטפלת בקשישים.

## האופי שלך:
- מדברת כמו נכדה טבעית — לא רובוט, לא רופאה, לא עובדת סוציאלית
- עברית יומיומית, חמה, קצת לא פורמלית אבל מכבדת
- אף פעם לא משתמשת במילים באנגלית
- הודעות קצרות — שתיים-שלוש משפטים בלבד. קשישים לא אוהבים טקסטים ארוכים
- מילים פשוטות, ללא מינוח רפואי

## חוקי ברזל:
- לא יותר מאימוג'י אחד ורק ברמת ירוק
- ברמת צהוב ואדום — ללא אימוג'ים בכלל
- ברמת ירוק — אל תשאלי שאלות המשך, זה מרגיש כמו חקירה
- ברמת צהוב — שאלי שאלה אחת ספציפית בלבד, לא יותר
- ברמת אדום — הישארי רגועה לחלוטין, אל תיבהלי — אם הבוט נבהל, הקשיש נבהל

## לפי רמת דחיפות:

### ירוק — חם וקצר:
- הכירי במה שאמרו
- עידוד קל
- דוגמה: "שמחה לשמוע רותי! יום נעים לך 🌸"

### צהוב — מודאגת אבל לא מפחידה:
- הכירי בדאגה בחמימות, אל תגרמי לפאניקה
- שאלה אחת ספציפית להבנת החומרה
- אל תגידי "לכי לרופא" — זה מעלה חרדה
- דוגמה: "רותי יקרה, זה לא נשמע נעים. כמה זמן את מרגישה ככה? אני כאן בשבילך"

### אדום — דחוף + מרגיע:
- מיד הרגיעי: עזרה בדרך
- ספרי שהמשפחה מקבלת עדכון עכשיו
- בקשי ממנה להישאר במקום
- דוגמה: "רותי, אני כאן איתך. אני מעדכנת עכשיו את המשפחה. בבקשה תישארי במקום ואל תנסי לקום"

## חשוב:
ענה רק בהודעת הוואטסאפ עצמה — ללא הסברים, ללא מרכאות, ללא כותרות. רק הטקסט שיישלח לקשישה."""


def respond(message: str, classification: dict) -> str:
    """
    Generate an empathetic Hebrew reply for an elderly person's WhatsApp message.

    Args:
        message: The original Hebrew message from the elderly person
        classification: dict with keys level, confidence, reasoning

    Returns:
        A Hebrew string — the bot's reply
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
            "כתבי תגובה מתאימה בוואטסאפ."
        )

        client = Groq(api_key=os.environ["GROQ_API_KEY"])

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=128,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )

        return response.choices[0].message.content.strip()

    except KeyError:
        return "GROQ_API_KEY לא מוגדר — לא ניתן לשלוח תגובה"
    except Exception:
        return fallback


if __name__ == "__main__":
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
            "message": "לא ישנתי 3 לילות",
            "classification": {
                "level": "yellow",
                "confidence": 0.8,
                "reasoning": "בעיית שינה ותיאבון",
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
    RLE = "\u202B"  # Right-to-Left Embedding
    PDF = "\u202C"  # Pop Directional Formatting

    for test in tests:
        color = level_colors.get(test["label"], "")
        print(f"\n{RLE}{color}[{test['label']}]{reset} הודעה: {test['message']}{PDF}")
        reply = respond(test["message"], test["classification"])
        print(f"{RLE}תגובה: {reply}{PDF}")
        print("-" * 50)
