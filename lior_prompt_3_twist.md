# ============================================
# LIOR — PROMPT 3: Claude (claude.ai)
# Task: Add medical JSON summary to classifier
# Time: 1:30–2:00 (after twist is revealed)
# ============================================
# Paste this in a new Claude chat with your working classifier.py attached:

I need to add a feature to my classifier. When the urgency level is RED, the classifier must ALSO return a structured medical summary that a nurse triage system can consume via API.

Take my existing classifier.py (attached) and add:

1. A new function: `extract_medical_summary(message: str, patient_id: str = "SVT-3201") -> dict`
2. Uses the same Anthropic API setup
3. Returns JSON like this:
```json
{
  "alert_level": "red",
  "patient_id": "SVT-3201",
  "symptoms": ["fall", "hip pain", "immobility"],
  "duration": "acute — just occurred",
  "severity": "high",
  "recommended_action": "dispatch emergency, possible hip fracture",
  "original_message": "<the Hebrew message>",
  "timestamp": "<ISO 8601 format>"
}
```

4. The `symptoms` field should be in ENGLISH (for the medical system)
5. The `recommended_action` should be in ENGLISH (for the medical system)
6. The `severity` is: "low" | "medium" | "high" | "critical"
7. The `duration` should describe onset: "acute", "X days", "chronic/ongoing"

Also modify the `classify()` function so that when level is "red", it automatically calls `extract_medical_summary()` and adds a "medical_summary" key to the returned dict.

So a red classification now returns:
```json
{
  "level": "red",
  "confidence": 0.95,
  "reasoning": "נפילה במטבח, כאבים חזקים, לא יכולה לקום",
  "medical_summary": {
    "alert_level": "red",
    "patient_id": "SVT-3201",
    "symptoms": ["fall", "hip pain", "immobility"],
    "duration": "acute — just occurred",
    "severity": "critical",
    "recommended_action": "dispatch emergency services, suspected hip fracture",
    "original_message": "נפלתי במטבח ואני לא יכולה לקום כואב לי מאוד הירך",
    "timestamp": "2026-03-16T21:30:00Z"
  }
}
```

Green and yellow classifications stay unchanged (no medical_summary key).

Test with the two RED test scenarios:
- "נפלתי במטבח ואני לא יכולה לקום, כואב לי מאוד הירך"
- "מאז שמשה נפטר אני לא רוצה להתעורר בבוקר, אין טעם"
