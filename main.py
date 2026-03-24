import requests
import time
import json
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# ==============================
# LOAD ENV
# ==============================
load_dotenv()

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

# ==============================
# CONFIG
# ==============================
TARGET_CLASS = "wetlanders"
URL = "https://cockburnarc.perfectgym.com.au/ClientPortal2/Groups/GroupsCalendar/GroupList"

CHECK_INTERVAL = 60  # 30 minutes
MAX_PAGES = 20

previous_vacancy_state = {}

os.makedirs("data", exist_ok=True)

# ==============================
# EMAIL FUNCTION
# ==============================
def send_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
            server.send_message(msg)

        print("📧 Email sent!")

    except Exception as e:
        print("❌ Email failed:", e)

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
                "daysOfWeek": [0,5],  # Sunday
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
                print(f"❌ Error on page {page_number}: {response.status_code}")
                break

            data = response.json().get("Data", [])

            if not data:
                print(f"✅ No more data at page {page_number}")
                break

            print(f"✅ Page {page_number}: {len(data)} records")
            all_data.extend(data)

            time.sleep(1)  # prevent rate limiting

        except Exception as e:
            print(f"❌ Exception on page {page_number}: {e}")
            break

    return all_data

# ==============================
# SAVE JSON
# ==============================
def save_json(data):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"data/response_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"💾 Saved: {filename}")

# ==============================
# MONITOR LOGIC
# ==============================
def monitor():
    global previous_vacancy_state

    print("\n⏱️ Checking at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    data = fetch_data()

    if not data:
        send_email(
            subject="⚠️ Monitor Alert: No Data",
            body="No data returned from API. Possible issue."
        )
        return

    save_json(data)

    found_any = False

    for item in data:
        name = item.get("Name", "").lower()

        if TARGET_CLASS in name:
            found_any = True

            # ✅ Extract available spots correctly
            booking = item.get("BookingIndicator", {})
            available = booking.get("Available", 0)

            # ✅ Extract Sunday date only
            sunday_dates = []
            for d in item.get("ClassDates", []):
                if d.get("Day") == "Sun" and d.get("Dates"):
                    sunday_dates.extend(d.get("Dates"))

            # fallback if no date
            if not sunday_dates:
                sunday_dates = ["Unknown Date"]

            for date in sunday_dates:
                key = f"{name}_{date}"
                previous_available = previous_vacancy_state.get(key, 0)

                print(f"➡️ {name} | {date} | Available: {available}")

                # 🚨 ALERT (only when new spot appears)
                if available > 0 and previous_available == 0:
                    print("🔥 New vacancy detected!")

                    send_email(
                        subject="🏊 Swimming Spot Available!",
                        body=f"{name}\nDate: {date}\nAvailable Spots: {available}"
                    )

                previous_vacancy_state[key] = available

    if not found_any:
        print("❌ No Wetlanders class found")

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

            send_email(
                subject="🚨 Monitor Crashed",
                body=str(e)
            )

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()