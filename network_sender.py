import os
import json
import requests
from google import genai  # <--- НОВАЯ БИБЛИОТЕКА
from google.genai import types
from dotenv import load_dotenv
import monitor_sys

# --- НАСТРОЙКИ ---
# Загрузка переменных окружения из .env файла
load_dotenv()

# Получение секретов из переменных окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Проверка загрузки всех необходимых секретов
if not all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, GEMINI_API_KEY]):
    raise ValueError(
        "Отсутствуют необходимые переменные окружения! "
        "Пожалуйста, убедитесь, что ваш .env файл содержит: "
        "TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, GEMINI_API_KEY"
    )


def ask_gemini(report_json):
    """
    Используем новый SDK google-genai
    """
    try:
        # Инициализация клиента (как в примере из AI Studio)
        client = genai.Client(api_key=GEMINI_API_KEY)

        prompt_text = (
            f"Ты системный администратор. Проанализируй этот JSON отчет о состоянии ПК. "
            f"Кратко укажи на проблемы (сеть, диск, RAM) и дай совет на русском языке. "
            f"Данные: {json.dumps(report_json)}"
        )

        # Запрос к модели.
        # Мы используем 'gemini-1.5-flash', так как это самая стабильная версия.
        # Если вы хотите экспериментов, можно попробовать 'gemini-2.0-flash-exp'
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt_text
        )

        # В новом SDK текст находится здесь:
        return response.text

    except Exception as e:
        return f"Ошибка Gemini (New SDK): {str(e)}"


def send_to_telegram(text_report, json_report):
    try:
        # 1. Отправка текста
        url_msg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url_msg, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": f"🤖 *Report:*\n{text_report}",
            "parse_mode": "Markdown"
        })

        # 2. Отправка JSON файла
        temp_file = "temp_log.json"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(json_report, f, indent=4, ensure_ascii=False)

        url_doc = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
        with open(temp_file, "rb") as f:
            requests.post(url_doc, data={"chat_id": TELEGRAM_CHAT_ID}, files={"document": f})

        os.remove(temp_file)
        return True
    except Exception as e:
        print(f"Ошибка Telegram: {e}")
        return False


def save_offline(report_data):
    desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
    # Убираем двоеточия из имени файла для совместимости
    timestamp = report_data['Time'].replace(":", "-")
    filename = os.path.join(desktop, f"System_Report_{timestamp}.txt")

    text = (
        f"ОТЧЕТ (ОФФЛАЙН)\n"
        f"Время: {report_data['Time']}\n"
        f"IP: {report_data['Network'].get('IP')}\n"
        f"Интернет: НЕДОСТУПЕН\n"
        f"Диск: {report_data['Disk']['Percent']}%\n"
    )
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
    return filename


def run_process():
    # 1. Сбор данных
    data = monitor_sys.quickcheck()

    # 2. Проверка сети
    if data['Network']['Status']:
        # ОНЛАЙН
        ai_response = ask_gemini(data)
        send_to_telegram(ai_response, data)
        return f"✅ СТАТУС: ОНЛАЙН\n\nОтвет Gemini:\n{ai_response}"
    else:
        # ОФФЛАЙН
        path = save_offline(data)
        return f"❌ СТАТУС: ОФФЛАЙН\nДанные сохранены на рабочем столе:\n{os.path.basename(path)}"