import os
import json
import requests
from google import genai  # <--- NEW LIBRARY
from google.genai import types
from dotenv import load_dotenv
import monitor_sys

# --- CONFIGURATION ---
# Load environment variables from .env file
load_dotenv()

# Get secrets from environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Check loading of all necessary secrets
if not all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, GEMINI_API_KEY]):
    raise ValueError(
        "Missing required environment variables! "
        "Please ensure your .env file contains: "
        "TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, GEMINI_API_KEY"
    )


def ask_gemini(report_json):
    """
    Use the new google-genai SDK to analyze system report.
    Returns English response from Gemini AI.
    """
    try:
        # Initialize client (as in example from AI Studio)
        client = genai.Client(api_key=GEMINI_API_KEY)

        prompt_text = (
            f"You are a system administrator. Analyze this JSON system health report. "
            f"Briefly identify any issues (network, disk, RAM) and provide advice in English. "
            f"Data: {json.dumps(report_json)}"
        )

        # Request to model.
        # We use 'gemini-3-flash-preview' for fast responses.
        # For experimentation, you can try 'gemini-2.0-flash-exp'
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt_text
        )

        # In the new SDK, text is located here:
        return response.text

    except Exception as e:
        return f"Gemini Error (New SDK): {str(e)}"


def send_to_telegram(text_report, json_report):
    """
    Send report to Telegram bot with text message and JSON file attachment.
    """
    try:
        # 1. Send text message
        url_msg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url_msg, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": f"🤖 *Report:*\n{text_report}",
            "parse_mode": "Markdown"
        })

        # 2. Send JSON file
        temp_file = "temp_log.json"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(json_report, f, indent=4, ensure_ascii=False)

        url_doc = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
        with open(temp_file, "rb") as f:
            requests.post(url_doc, data={"chat_id": TELEGRAM_CHAT_ID}, files={"document": f})

        os.remove(temp_file)
        return True
    except Exception as e:
        print(f"Telegram Error: {e}")
        return False


def save_offline(report_data):
    """
    Save offline report to desktop as a text file.
    """
    desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
    # Remove colons from filename for compatibility
    timestamp = report_data['Time'].replace(":", "-")
    filename = os.path.join(desktop, f"System_Report_{timestamp}.txt")

    text = (
        f"OFFLINE REPORT\n"
        f"Time: {report_data['Time']}\n"
        f"IP: {report_data['Network'].get('IP')}\n"
        f"Internet: UNAVAILABLE\n"
        f"Disk: {report_data['Disk']['Percent']}%\n"
    )
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
    return filename


def run_process():
    """
    Main process: collect data, check network status, and send report.
    Returns status message.
    """
    # 1. Collect data
    data = monitor_sys.quickcheck()

    # 2. Check network
    if data['Network']['Status']:
        # ONLINE
        ai_response = ask_gemini(data)
        send_to_telegram(ai_response, data)
        return f"✅ STATUS: ONLINE\n\nGemini Response:\n{ai_response}"
    else:
        # OFFLINE
        path = save_offline(data)
        return f"❌ STATUS: OFFLINE\nData saved to desktop:\n{os.path.basename(path)}"