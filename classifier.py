import json
from config import MODEL, get_client


def classify(message: str) -> dict:
    """Classify a Hebrew message into green/yellow/red urgency level."""
    client = get_client()

    system_prompt = """You are a medical triage classifier for elderly care check-in messages in Hebrew.
Analyze the message and classify it into one of three levels:
- "green": The person sounds fine, positive, normal daily activity.
- "yellow": Something is slightly concerning — mild complaints, loneliness, minor pain, confusion.
- "red": Urgent — severe pain, fall, breathing difficulty, chest pain, disorientation, cry for help.

You must respond ONLY with valid JSON in this exact format:
{"level": "green"|"yellow"|"red", "confidence": 0.0-1.0, "reasoning": "brief explanation in Hebrew"}"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=256,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        text = response.choices[0].message.content.strip()
        return json.loads(text)
    except json.JSONDecodeError:
        return {"level": "green", "confidence": 0.5, "reasoning": "לא הצלחתי לנתח את ההודעה"}
    except Exception as e:
        return {"level": "green", "confidence": 0.0, "reasoning": f"שגיאה: {str(e)}"}
