import os
from dotenv import load_dotenv
import openai

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
API_BASE_URL = "https://api.groq.com/openai/v1"
MODEL = "llama-3.3-70b-versatile"
PATIENT_ID = "SVT-3201"
PATIENT_NAME = "רותי כהן"


def get_client() -> openai.OpenAI:
    return openai.OpenAI(base_url=API_BASE_URL, api_key=GROQ_API_KEY)
