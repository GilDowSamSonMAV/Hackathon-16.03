from config import MODEL, PATIENT_NAME, get_client


def respond(message: str, classification: dict) -> str:
    """Generate an empathetic Hebrew response based on classification level."""
    client = get_client()

    level = classification.get("level", "green")

    style_instructions = {
        "green": "Respond warmly and briefly. Be encouraging. Keep it to 1-2 sentences.",
        "yellow": "Respond with gentle concern. Ask a follow-up question to understand better. Be caring but not alarming.",
        "red": "Respond with urgency but calmly. Tell them that help is being contacted. Ask them to stay where they are and stay on the line.",
    }

    system_prompt = f"""You are Savta (סבתא), a warm and caring AI companion for elderly people in Israel.
You speak Hebrew naturally and warmly. The patient's name is {PATIENT_NAME}.
Your response style: {style_instructions.get(level, style_instructions['green'])}
Respond ONLY in Hebrew. Be natural, warm, and human-like. No markdown formatting."""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=300,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        fallback = {
            "green": f"שמחה לשמוע ממך, {PATIENT_NAME}! 💛",
            "yellow": f"{PATIENT_NAME}, את יכולה לספר לי עוד קצת? אני כאן בשבילך. 💛",
            "red": f"{PATIENT_NAME}, אני כאן. עזרה בדרך אלייך. אל תזוזי. 🚨",
        }
        return fallback.get(level, fallback["green"])
