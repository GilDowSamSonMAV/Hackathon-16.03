import os
from dotenv import load_dotenv
import openai

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
MODEL = os.getenv("MODEL", "mistral")
PATIENT_ID = "SVT-3201"
PATIENT_NAME = "רותי כהן"


def get_client() -> openai.OpenAI:
    return openai.OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
