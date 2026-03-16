import json
from datetime import datetime

from config import MODEL, PATIENT_NAME, get_client


def create_alert(message: str, classification: dict, patient_id: str = "SVT-3201") -> dict:
    """Create a family alert dict for yellow/red classifications."""
    level = classification.get("level", "yellow")
    actions = {
        "yellow": "המשך מעקב — שלחו הודעה למטופל/ת לבדיקה",
        "red": "🚨 פעולה דחופה — צרו קשר מיידי עם המטופל/ת או שירותי חירום",
    }
    return {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "alert_level": level,
        "patient_id": patient_id,
        "patient_name": PATIENT_NAME,
        "message_snippet": message[:80] + ("..." if len(message) > 80 else ""),
        "reasoning": classification.get("reasoning", ""),
        "recommended_action": actions.get(level, actions["yellow"]),
    }


def create_medical_summary(message: str, classification: dict, patient_id: str = "SVT-3201") -> dict:
    """For RED alerts: extract structured medical info via Groq API."""
    client = get_client()

    system_prompt = """You are a medical information extractor. Given a Hebrew message from an elderly patient,
extract structured medical information. You must respond ONLY with valid JSON in this exact format:
{
  "alert_level": "red",
  "patient_id": "<given>",
  "patient_name": "<given>",
  "symptoms": ["symptom1", "symptom2"],
  "duration": "estimated duration or 'unknown'",
  "severity": "low|medium|high|critical",
  "recommended_action": "specific medical recommendation in Hebrew",
  "original_message": "<the original message>",
  "timestamp": "<current time>"
}"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=512,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Patient ID: {patient_id}\nPatient Name: {PATIENT_NAME}\nTimestamp: {datetime.now().isoformat()}\nMessage: {message}",
                },
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        text = response.choices[0].message.content.strip()
        return json.loads(text)
    except Exception:
        return {
            "alert_level": "red",
            "patient_id": patient_id,
            "patient_name": PATIENT_NAME,
            "symptoms": ["לא זוהו — נדרשת בדיקה ידנית"],
            "duration": "unknown",
            "severity": "high",
            "recommended_action": "צרו קשר מיידי עם המטופל/ת",
            "original_message": message,
            "timestamp": datetime.now().isoformat(),
        }
