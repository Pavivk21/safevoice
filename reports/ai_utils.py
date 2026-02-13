import openai
from django.conf import settings

openai.api_key = settings.OPENAI_API_KEY


def analyze_report(text):

    prompt = f"""
    Analyze this harassment report and classify it.

    Text: {text}

    Give:
    1. Severity (Low/Medium/High)
    2. Confidence (0-100)

    Format:
    Severity: X
    Confidence: Y
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    result = response["choices"][0]["message"]["content"]

    return result
