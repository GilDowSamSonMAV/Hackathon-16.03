import json
import re
from config import MODEL, get_client


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
        )
        text = response.choices[0].message.content.strip()
        return _extract_json(text)
    except json.JSONDecodeError:
        return {"level": "green", "confidence": 0.5, "reasoning": "לא הצלחתי לנתח את ההודעה"}
    except Exception as e:
        return {"level": "green", "confidence": 0.0, "reasoning": f"שגיאה: {str(e)}"}
