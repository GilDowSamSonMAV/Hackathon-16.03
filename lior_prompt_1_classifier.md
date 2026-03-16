# ============================================
# LIOR — PROMPT 1: Claude (claude.ai)
# Task: Build the classifier system prompt
# Time: 0:15–1:00
# ============================================
# Open claude.ai and paste this:

I'm building an AI classifier for an elderly care WhatsApp bot called "Savta". The classifier receives a Hebrew message from an elderly person and must classify it as green (fine), yellow (concerning), or red (urgent/emergency).

Write me a complete Python file called `classifier.py` that:

1. Uses the Anthropic Python SDK (import anthropic)
2. Has a function: `classify(message: str) -> dict`
3. Returns: `{"level": "green"|"yellow"|"red", "confidence": float 0-1, "reasoning": str in Hebrew}`
4. Uses model "claude-sonnet-4-20250514"
5. Reads ANTHROPIC_API_KEY from environment variable

## The system prompt must handle these nuances of elderly Hebrew speakers:

- They write VERY colloquially — no punctuation, spelling mistakes, shorthand
- "בסדר" can mean genuinely fine OR dismissive (context matters)
- Physical complaints that sound minor can be serious: "קצת כואב לי" from a 80-year-old = yellow
- Emotional distress is often understated: "אין טעם" = RED, not yellow
- Grumpy/annoyed tone ≠ distress: "תפסיק לשאול" while saying "אני בסדר" = green
- Falls are ALWAYS red regardless of "אבל אני בסדר" — elderly falls = potential fracture
- Not eating / not sleeping for multiple days = yellow minimum
- Any mention of deceased spouse + hopelessness = RED (emotional crisis)
- "לא רוצה להתעורר" / "אין טעם לחיים" = RED — even if said casually

## Few-shot examples to include in the system prompt (rephrase these, don't use verbatim):

GREEN examples:
- Morning greeting + took medication + going for walk → routine, green
- Annoyed at being asked + "I'm fine leave me alone" → grumpy but fine, green  
- "Watched TV, ate lunch, boring day" → uneventful, green
- "The grandkids visited yesterday, it was nice" → positive, green

YELLOW examples:
- Sleep problems for multiple nights + no appetite → declining pattern, yellow
- "I feel dizzy sometimes" → medical concern, yellow
- "I forgot to take my pills yesterday and today" → medication non-compliance, yellow
- "My neighbor hasn't visited in weeks, I'm alone" → social isolation, yellow

RED examples:
- Fell + can't get up + pain → medical emergency, red
- Deceased spouse + don't want to wake up + no point → emotional crisis, red
- "I can't breathe well" / chest pain → medical emergency, red
- "I haven't eaten in 3 days, I don't care" → severe neglect + apathy, red

## Output format — the LLM must respond ONLY with valid JSON:
```json
{
  "level": "green",
  "confidence": 0.92,
  "reasoning": "הודעה שגרתית, המטופלת לקחה תרופות ויוצאת לטייל"
}
```

## Important:
- Wrap the API call in try/except
- If API fails, return {"level": "yellow", "confidence": 0.0, "reasoning": "שגיאה בסיווג - ברירת מחדל"} (fail safe to yellow, not green)
- Parse the JSON response carefully — handle cases where the model adds markdown backticks around the JSON
- The function should work standalone: I should be able to run `python classifier.py` and test it

Add a `if __name__ == "__main__":` block at the bottom that tests with these 3 messages:
- "בוקר טוב הכל בסדר לקחתי כדורים"
- "לא ישנתי כבר 3 לילות אין לי כוח"  
- "נפלתי ואני על הרצפה כואב לי"

Print the result for each.
