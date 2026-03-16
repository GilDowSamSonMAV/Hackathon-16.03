import json
import re
import time
from datetime import datetime

from config import MODEL, PATIENT_NAME, PATIENT_ID, get_client


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


def create_alert(message: str, classification: dict, patient_id: str = None) -> dict:
    """Create a family alert dict for yellow/red classifications."""
    if not patient_id:
        patient_id = PATIENT_ID
    if not classification or not isinstance(classification, dict):
        classification = {"level": "yellow", "confidence": 0, "reasoning": ""}

    level = classification.get("level", "yellow")
    if level not in ("yellow", "red"):
        level = "yellow"

    actions = {
        "yellow": "Follow up within 2 hours",
        "red": "Immediate family notification + consider emergency services",
    }

    msg = message or ""
    snippet = msg[:60] + ("..." if len(msg) > 60 else "")
    now = datetime.now()

    return {
        "timestamp": now.strftime("%d %b %Y, %H:%M"),
        "timestamp_iso": now.isoformat(),
        "alert_level": level,
        "patient_id": patient_id,
        "patient_name": PATIENT_NAME,
        "message_snippet": snippet,
        "reasoning": classification.get("reasoning", ""),
        "recommended_action": actions.get(level, actions["yellow"]),
    }


def create_medical_summary(message: str, classification: dict, patient_id: str = None) -> dict:
    """For RED alerts: extract structured medical info via local Ollama model."""
    if not patient_id:
        patient_id = PATIENT_ID
    if not message:
        message = "(empty message)"

    time.sleep(1)

    client = get_client()

    system_prompt = """You are a medical information extractor for an elderly care system.
Given a Hebrew message from an elderly patient, extract structured medical information.

You MUST respond with valid JSON matching this exact schema:
{
  "alert_level": "red",
  "patient_id": "<given patient ID>",
  "symptoms": ["symptom_in_english_1", "symptom_in_english_2"],
  "duration": "acute | X days | chronic | unknown",
  "severity": "low | medium | high | critical",
  "recommended_action": "specific recommendation in English",
  "original_message": "<the original Hebrew message>",
  "timestamp": "<ISO 8601 timestamp>"
}

Rules:
- Extract symptoms in ENGLISH from the Hebrew message
- Determine duration: acute (just happened), X days, chronic, or unknown
- Assess severity: low / medium / high / critical
- Recommend action in ENGLISH
- Return ONLY the JSON object, nothing else"""

    now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=512,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Patient ID: {patient_id}\nTimestamp: {now_iso}\nMessage: {message}",
                },
            ],
            temperature=0.2,
        )
        text = response.choices[0].message.content.strip()
        result = _extract_json(text)
        result.setdefault("alert_level", "red")
        result.setdefault("patient_id", patient_id)
        result.setdefault("symptoms", ["unknown"])
        result.setdefault("duration", "unknown")
        result.setdefault("severity", "unknown")
        result.setdefault("recommended_action", "manual review required")
        result.setdefault("original_message", message)
        result.setdefault("timestamp", now_iso)
        return result
    except Exception:
        return {
            "alert_level": "red",
            "patient_id": patient_id,
            "symptoms": ["extraction_failed"],
            "duration": "unknown",
            "severity": "unknown",
            "recommended_action": "manual review required",
            "original_message": message,
            "timestamp": now_iso,
        }
