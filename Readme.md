
## 🛠️ Setup Instructions for Wetlanders Monitoring Script

### 1. Prerequisites

Make sure you have:

* A computer or server (Windows / Mac / Linux)
* Python 3.9+ installed
* Internet connection

---

## 2. Download the Project

* Download the project files (shared by me)
* Extract them into a folder, e.g.:

```
perfect_gym_alert/
```

---

## 3. Install Dependencies

Open terminal/command prompt inside the project folder and run:

```
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create a file named **`.env`** in the project folder and add:

```
EMAIL_RECEIVER=your_email@example.com
RESEND_API_KEY=your_resend_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

---

## 5. Setup Email (Resend)

1. Go to <https://resend.com>
2. Create an account
3. Generate an API Key
4. Copy it into:

```
RESEND_API_KEY=...
```

---

## 6. Setup Telegram Alerts

### Step 1: Create Bot

* Open Telegram
* Search for **@BotFather**
* Type: `/start`
* Type: `/newbot`
* Follow instructions
* Copy the **Bot Token**

Paste into:

```
TELEGRAM_BOT_TOKEN=...
```

---

### Step 2: Activate Bot (IMPORTANT)

* Open this link in browser:

```
https://t.me/<your_bot_username>
```

* Click **Start**
* Send any message (e.g. "Hi")

👉 This step is required for alerts to work

---

## 7. Run the Script

In terminal:

```
python main.py
```

You should see:

```
🚀 Monitoring started...
```

---

## 8. How It Works

* Script checks every **30 minutes**
* Monitors Sunday “Wetlanders” classes
* If a spot becomes available:

  * 📧 Email is sent
  * 📱 Telegram alert is sent
* If the script crashes:

  * 🚨 Alert is sent automatically

* At the end of the day (1700), An Email summary is send.

---

## 9. Deployment

For 24/7 running, deploy on cloud:

### Railway

1. Go to <https://railway.app>
2. Create account
3. Upload project (via GitHub)
4. Add environment variables in Railway dashboard
5. Deploy

---

## 10. Start / Stop

### Start

```
python main.py
```

### Stop

Press:

```
Ctrl + C
```

---

## 11. Notes

* No duplicate alerts will be sent
* Telegram alerts are instant and free
* Email is sent via Resend (reliable API)
* Script runs continuously in the background

---

## ✅ You’re All Set

Once configured, the system will automatically monitor and notify you whenever a slot becomes available.

If you face any issues, I’m happy to help.
