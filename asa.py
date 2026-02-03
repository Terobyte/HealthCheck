import os
from google import genai
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Получение ключа Gemini API из переменных окружения
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY_FALLBACK")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY_FALLBACK не найден в .env файле")

client = genai.Client(api_key=GEMINI_API_KEY)

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Tell me whos the biggest monkey in a jungle",
)

print(response.text)
