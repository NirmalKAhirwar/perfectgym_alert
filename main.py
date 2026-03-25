import requests
import time
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# ==============================
# LOAD ENV
# ==============================
load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = ""


def get_chat_id():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    
    res = requests.get(url).json()

    if res["result"]:
        return res["result"][-1]["message"]["chat"]["id"]

    return None

if not TELEGRAM_CHAT_ID:
    TELEGRAM_CHAT_ID = get_chat_id()
    print("Detected Chat ID:", TELEGRAM_CHAT_ID)

print("✅ Environment variables loaded")

# ==============================
# CONFIG
# ==============================
TARGET_CLASS = "wetlanders"
URL = "https://cockburnarc.perfectgym.com.au/ClientPortal2/Groups/GroupsCalendar/GroupList"

CHECK_INTERVAL = 60  # 30 minutes
MAX_PAGES = 20

previous_vacancy_state = {}

os.makedirs("data", exist_ok=True)


def format_datetime(date_str):
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%A, %d %B %Y at %I:%M %p")
    except:
        return date_str  # fallback if parsing fails

# ==============================
# EMAIL (RESEND API)
# ==============================
def send_email(subject, body):
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": "onboarding@resend.dev",
                "to": EMAIL_RECEIVER,
                "subject": subject,
                "text": body
            }
        )

        if response.status_code in [200, 201]:
            print("📧 Email sent!")
        else:
            print("❌ Email failed:", response.text)

    except Exception as e:
        print("❌ Email error:", e)

# ==============================
# TELEGRAM ALERT
# ==============================
def send_telegram(message):
    global TELEGRAM_CHAT_ID

    try:
        # auto-fetch chat_id if not set
        if not TELEGRAM_CHAT_ID:
            TELEGRAM_CHAT_ID = get_chat_id()

            if not TELEGRAM_CHAT_ID:
                print("⚠️ No chat_id found. Ask user to message the bot.")
                return

            print(f"✅ Auto-detected chat_id: {TELEGRAM_CHAT_ID}")

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

        response = requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        })

        if response.status_code == 200:
            print("📱 Telegram sent!")
        else:
            print("❌ Telegram failed:", response.text)

    except Exception as e:
        print("❌ Telegram error:", e)

# ==============================
# FETCH DATA (PAGINATION)
# ==============================
def fetch_data():
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    all_data = []

    for page_number in range(1, MAX_PAGES + 1):
        payload = {
            "filterParams": {
                "clubId": 1,
                "vacancies": "1",
                "ageLimitId": None,
                "activityCategoryIds": [],
                "activityUserLevelIds": [],
                "daysOfWeek": [0],  # Sunday
                "semesterIds": [],
                "showSingleLesson": None,
                "date": None
            },
            "query": {
                "pageSize": 20,
                "pageNumber": page_number
            }
        }

        try:
            response = requests.post(URL, headers=headers, json=payload, timeout=10)

            if response.status_code != 200:
                print(f"❌ Error page {page_number}: {response.status_code}")
                break

            data = response.json().get("Data", [])

            if not data:
                print(f"✅ No more data at page {page_number}")
                break

            print(f"✅ Page {page_number}: {len(data)} records")
            all_data.extend(data)

            time.sleep(1)

        except Exception as e:
            print(f"❌ Fetch error page {page_number}:", e)
            break

    return all_data

# ==============================
# SAVE JSON
# ==============================
def save_json(data):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"data/response_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

    print(f"💾 Saved: {filename}")

def load_json(filename):
    with open(filename, "r") as f:
        return json.load(f)

# ==============================
# MONITOR LOGIC
# ==============================
def monitor():
    global previous_vacancy_state
    print(f"\n ⏱️ checking at {format_datetime(datetime.now().isoformat())}")

    # data = fetch_data() # fetching real data from API 
    data = load_json("data/response_2026-03-25_11-07-39.json")  # for testing 

    if not data:
        send_email("⚠️ Monitor Alert", "No data received from PerfectGym API")
        send_telegram("⚠️ Monitor Alert: No data received from PerfectGym API")
        return

    # save_json(data)
    
    found = False
    # x = 1/ 0 # to test error handling
    
    for item in data:
        name = item.get("Name", "").lower()

        if TARGET_CLASS in name:
            found = True

            booking = item.get("BookingIndicator", {})
            available = booking.get("Available", 0)

            sunday_dates = []
            for d in item.get("ClassDates", []):
                
                if d.get("Day") == "Sun" and d.get("Dates"):
                    sunday_dates.extend(d.get("Dates"))

            if not sunday_dates:
                continue

            for date in sunday_dates:
                key = f"{name}_{date}"
                formatted_date = format_datetime(date)
                prev = previous_vacancy_state.get(key, 0)

                print(f"➡️ {name} | {formatted_date} | Available: {available}")

                if available > 0 and prev == 0:
                    print("🔥 Vacancy detected!")

                    msg = f"""
                            🏊 Wetlanders Slot Available!

                            📌 Class: {name}
                            📅 Date: {formatted_date}
                            👥 Spots: {available}

                            👉 Book now!
                            """

                    send_email("🏊 Slot Available!", msg)
                    send_telegram(msg)

                previous_vacancy_state[key] = available

    if not found:
        print("❌ No Wetlanders classes found")

# ==============================
# MAIN LOOP
# ==============================
def main():
    print("🚀 Monitoring started...")

    while True:
        try:
            monitor()
        except Exception as e:
            print("❌ Critical error:", e)

            send_email("🚨 Monitor Crashed", str(e))
            send_telegram(f"🚨 Monitor crashed:\n{str(e)}")
            sys.exit("Stopping script")

        time.sleep(CHECK_INTERVAL)

# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    main()