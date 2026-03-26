import requests
import time
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
datetime.now(timezone.utc) 

# ==============================
# LOAD ENV
# ==============================
load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

TELEGRAM_CHAT_ID = None


def get_chat_id():
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        res = requests.get(url).json()

        if res.get("result"):
            return res["result"][-1]["message"]["chat"]["id"]

    except Exception as e:
        print("❌ chat_id fetch error:", e)

    return None

# ==============================
# CONFIG
# ==============================
TARGET_CLASS = "wetlanders"
URL = "https://cockburnarc.perfectgym.com.au/ClientPortal2/Groups/GroupsCalendar/GroupList"

CHECK_INTERVAL = 1800 # seconds
MAX_PAGES = 20

previous_vacancy_state = {}

daily_logs = []
LAST_SUMMARY_DATE = None


os.makedirs("data", exist_ok=True)

# ==============================
# UTIL
# ==============================
def now_gmt8():
    return datetime.now(timezone.utc) + timedelta(hours=8)

metrics = {
    "total_checks": 0,
    "wetlanders_found": 0,
    "vacancy_times": [],
    "start_time": now_gmt8().strftime("%A, %d %B %Y %I:%M:%S %p"),
}

def load_json(filename):
    with open(filename) as f:
        return json.load(f)

def format_datetime(date_str):
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%A, %d %B %Y at %I:%M %p")
    except:
        return date_str


def send_email(subject, html_body):
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
                "html": html_body
            }
        )

        if response.status_code in [200, 201]:
            print("📧 Email sent!")
        else:
            print("❌ Email failed:", response.text)

    except Exception as e:
        print("❌ Email error:", e)


def send_telegram(message):
    global TELEGRAM_CHAT_ID

    try:
        if not TELEGRAM_CHAT_ID:
            TELEGRAM_CHAT_ID = get_chat_id()

            if not TELEGRAM_CHAT_ID:
                print("⚠️ No chat_id found")
                return

            print("✅ chat_id detected:", TELEGRAM_CHAT_ID)

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

        res = requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        })

        if res.status_code == 200:
            print("📱 Telegram sent")
        else:
            print("❌ Telegram failed:", res.text)

    except Exception as e:
        print("❌ Telegram error:", e)


def fetch_data():
    headers = {"Content-Type": "application/json"}

    all_data = []

    for page in range(1, MAX_PAGES + 1):
        payload = {
            "filterParams": {
                "clubId": 1,
                "vacancies": "1",
                "daysOfWeek": [0]
            },
            "query": {
                "pageSize": 20,
                "pageNumber": page
            }
        }

        try:
            res = requests.post(URL, headers=headers, json=payload, timeout=10)

            if res.status_code != 200:
                break

            data = res.json().get("Data", [])

            if not data:
                break

            all_data.extend(data)

        except Exception as e:
            print("❌ Fetch error:", e)
            break

    return all_data


def monitor():
    global previous_vacancy_state

    current_time = now_gmt8().strftime("%Y-%m-%d %H:%M:%S")

    metrics["total_checks"] += 1
    daily_logs.append(f"{current_time} → Check #{metrics['total_checks']}")

    print(f"\n⏱️ Checking at {current_time}")

    data = fetch_data()
    # data = load_json("data/response_2026-03-25_11-07-39.json") # test with data

    if not data:
        send_email("⚠️ Monitor Alert", "No data received from PerfectGYM API. Please check the monitor.")
        return

    found = False

    for item in data:
        name = item.get("Name", "").lower()

        if TARGET_CLASS in name:
            found = True

            booking = item.get("BookingIndicator", {})
            available = booking.get("Available", 0)

            for d in item.get("ClassDates", []):
                if d.get("Day") == "Sun" and d.get("Dates"):
                    for date in d["Dates"]:
                        formatted_date = format_datetime(date)
                        key = f"{name}_{date}"

                        prev = previous_vacancy_state.get(key, None)
                        

                        print(f"➡️ {name} | {formatted_date} | {available}")

                        if available > 0 and (prev is None or prev == 0):
                            print("🔥 Vacancy!")

                            metrics["wetlanders_found"] += 1
                            
                            metrics["vacancy_times"].append({
                                "detected_at": current_time,
                                "class_name": name,
                                "slot_time": formatted_date,
                                "spots": available
                                })
                            msg = f"\n🏊 Wetlanders Slot Available!\n📌 {name}\n📅 {formatted_date}\n👥 Spots: {available}"

                            send_email("🏊 Slot Available", msg)
                            send_telegram(msg)
                        
                        if prev is not None and available < prev:
                            print("⚠️ Spots are getting filled!")
                            reduction = prev - available
                            daily_logs.append(
                                f"{current_time} → ⚠️ Spots reduced: {name} | {formatted_date} | {prev} → {available}"
                            )
                            msg = f"⚠️ Wetlanders Slot Filling Fast!\n📌 {name}\n📅 {formatted_date}\n⬇️ Spots reduced: {prev} → {available}\n🔥 {reduction} spot(s) just booked!"

                            send_email("⚠️ Slots Filling Fast", msg)
                            send_telegram(msg)

                        previous_vacancy_state[key] = available

    if not found:
        print("❌ No Wetlanders found")


def format_now(dt):
    return dt.strftime("%A, %d %B %Y at %I:%M:%S %p (GMT+8)")

def build_summary_html(crash=False, error=None):
    now_time = now_gmt8().strftime("%A, %d %B %Y %I:%M:%S %p")

    # build table rows
    rows = ""
    seen = set()

    for v in metrics["vacancy_times"]:
        key = (v["class_name"], v["slot_time"])

        if key in seen:
            continue
        seen.add(key)

        rows += f"""
        <tr>
            <td>{v['detected_at']}</td>
            <td>{v['class_name'].title()}</td>
            <td>{v['slot_time']}</td>
            <td>{v['spots']}</td>
        </tr>
        """

    if not rows:
        rows = """
        <tr>
            <td colspan="4">No vacancies detected</td>
        </tr>
        """

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">

        <h2>📊 Wetlanders Daily Monitoring Report</h2>

        <p><b>🕒 Start Time:</b> {metrics['start_time']}</p>
        <p><b>🕒 Current Time:</b> {now_time} (GMT+8)</p>

        <hr>

        <h3>📈 Summary Metrics</h3>
        <ul>
            <li>Total Checks: {metrics['total_checks']}</li>
            <li>Wetlanders Found: {metrics['wetlanders_found']}</li>
            
        </ul>

        <hr>

        <h3>📅 Vacancy Availability</h3>

        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse;">
            <tr style="background-color: #f2f2f2;">
                <th>Time Detected</th>
                <th>Class</th>
                <th>Slot Time</th>
                <th>Spots</th>
            </tr>
            {rows}
        </table>

        <hr>

        <h3>📜 Recent Logs</h3>
        <pre>
{chr(10).join(daily_logs[-20:])}
        </pre>
    """

    if crash:
        html += f"""
        <h3 style="color:red;">🚨 Crash Detected</h3>
        <p>{error}</p>
        """

    html += """
    </body>
    </html>
    """

    return html


def send_daily_summary():
    report = build_summary_html() #build_summary()

    send_email("📊 Daily Summary", report)

    print("📧 Summary sent")

    daily_logs.clear()
    metrics["total_checks"] = 0
    metrics["wetlanders_found"] = 0
    metrics["vacancy_times"] = []


def main():
    global LAST_SUMMARY_DATE

    print("\n🚀 Wetlanders Monitoring started...")

    while True:
        try:
            monitor()

            now = now_gmt8()
            print(f"\n⏰ Next Refresh in {CHECK_INTERVAL // 60} minutes | Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            # send summary at 17:00
            if now.hour == 17 and now.minute < 2:
            # if now.minute % 2 == 0: # test with every 2 minutes
                if LAST_SUMMARY_DATE != now.date():
                    send_daily_summary()
                    LAST_SUMMARY_DATE = now.date()

        except Exception as e:
            print("❌ Crash:", e)

            report = build_summary_html(crash=True, error=str(e))

            send_email("🚨 Monitor Crash", report)
            send_telegram("🚨 Monitor crashed")

            sys.exit()

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()