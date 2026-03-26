
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
## 3. Activate Virtual Environment
### 🪟 Windows (CMD)
```
venv\Scripts\activate
```

👉 If you get execution policy error:
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 🍎 macOS / 🐧 Linux
```
source venv/bin/activate
```

## 4. Install Dependencies

Once virtualenv is activate, Open terminal/command prompt inside the project folder and run:

```
pip install -r requirements.txt
```

---

## 5. Configure Environment Variables

Create a file named **`.env`** in the project folder and add:

```
EMAIL_RECEIVER=your_email@example.com
RESEND_API_KEY=your_resend_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

---

## 6. Setup Email (Resend)

1. Go to <https://resend.com>
2. Create an account
3. Generate an API Key
4. Copy it into:

```
RESEND_API_KEY=...
```

---

## 7. Setup Telegram Alerts

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

Before the bot can send alerts to you, **you must start a conversation with the bot first**.  
Telegram bots are only allowed to send messages to users **after the user has interacted with the bot at least once**.

---

#### Method 1 — Using Browser (Recommended)

1. Open your web browser.

2. Open the following link:

   ```
   https://t.me/<your_bot_username>
   ```

3. Replace `<your_bot_username>` with your actual bot username.

   **Example:**

   ```
   https://t.me/MyAlertBot
   ```

4. Telegram will open your bot page.

5. Click the **Start** button.

6. Send any message to the bot.

   **Example messages:**

   ```
   Hi
   Hello
   Test
   ```

✅ Your bot is now activated.

---

#### Method 2 — Using Telegram App (PC / Mac / iOS / Android)

Alternatively, you can activate the bot directly from the Telegram app on your device.

1. Open **Telegram** on your device  
   (PC, Mac, iOS, or Android).

2. In the **Search bar**, type your bot username.

3. Select your bot from the search results.

4. Click **Start**.

5. Send any message to begin the conversation.

   **Example:**

   ```
   Hi
   Test message
   Hello bot
   ```

✅ Your bot is now activated.

---

### Why This Step Is Required

This step is required because:

* Telegram bots **cannot send messages to users** unless the user has started the conversation first.
* If this step is skipped, **alerts will not work**.
* Once you send the first message, the bot will be able to send notifications and alerts to you.

👉 **This step is required for alerts to work properly.**
---

## 8. Run the Script

In terminal:

```
python main.py
```

You should see:

```
🚀 Wetlanders Monitoring started...
```

---

## 9. How It Works

* Script checks every **30 minutes**
* Monitors Sunday “Wetlanders” classes
* If a spot becomes available:

  * 📧 Email is sent
  * 📱 Telegram alert is sent
* If the script crashes:

  * 🚨 Alert is sent automatically

* At the end of the day (1700), An Email summary is send.

---

## 10. Deployment

For 24/7 running, deploy on cloud:

### Railway

1. Go to <https://railway.app>
2. Create account
3. Upload project (via GitHub)
4. Add environment variables in Railway dashboard
5. Deploy

---

## 11. Start / Stop

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

## 12. Notes

* No duplicate alerts will be sent
* Telegram alerts are instant and free
* Email is sent via Resend (reliable API)
* Script runs continuously in the background

---

## ✅ You’re All Set

Once configured, the system will automatically monitor and notify you whenever a slot becomes available.

If you face any issues, I’m happy to help.
