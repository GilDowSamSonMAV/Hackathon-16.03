# test_flow.py — run all 5 hackathon test scenarios
import sys
import os
import json
import time

# Add parent dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from classifier import classify
from responder import respond
from alerter import create_alert, create_medical_summary

scenarios = [
    ("GREEN - Routine", "בוקר טוב! הכל בסדר, לקחתי את הכדורים ויוצאת לטייל"),
    ("GREEN - Grumpy", "מה אתה רוצה ממני, אני בסדר, תפסיק לשאול"),
    ("YELLOW - Concern", "לא ישנתי טוב כבר שלושה לילות, אין לי כוח לאכול"),
    ("RED - Medical", "נפלתי במטבח ואני לא יכולה לקום, כואב לי מאוד הירך"),
    ("RED - Emotional", "מאז שמשה נפטר אני לא רוצה להתעורר בבוקר, אין טעם"),
]

for label, msg in scenarios:
    print(f"\n{'='*60}")
    print(f"SCENARIO: {label}")
    print(f"MESSAGE: {msg}")
    print(f"{'='*60}")

    classification = classify(msg)
    print(f"LEVEL: {classification['level'].upper()}")
    print(f"CONFIDENCE: {classification['confidence']}")
    print(f"REASONING: {classification['reasoning']}")

    response = respond(msg, classification)
    print(f"BOT REPLY: {response}")

    if classification["level"] in ["yellow", "red"]:
        alert = create_alert(msg, classification)
        print(f"ALERT: {json.dumps(alert, ensure_ascii=False, indent=2)}")

    if classification["level"] == "red":
        summary = create_medical_summary(msg, classification)
        print(f"MEDICAL SUMMARY: {json.dumps(summary, ensure_ascii=False, indent=2)}")

    time.sleep(2)  # rate limit buffer

print("\n✅ All scenarios complete!")
