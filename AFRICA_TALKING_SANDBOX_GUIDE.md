# Africa's Talking Sandbox Setup Guide

This guide walks you through obtaining Africa's Talking sandbox credentials and
configuring MediTrack to send real SMS messages during development.

---

## Step 1 – Create a Free Africa's Talking Account

1. Open your browser and go to **https://africastalking.com**
2. Click **"Get Started"** (top-right corner)
3. Fill in the registration form:
   - Full Name
   - Email address
   - Password (min 8 characters)
   - Country
4. Click **"Create Account"**
5. Check your email inbox for a verification link and click it

---

## Step 2 – Access the Sandbox Environment

1. Log in at **https://account.africastalking.com**
2. In the left sidebar, look for the **"Sandbox"** section or click the
   environment switcher near the top of the dashboard (it will show *"Live"*
   – click it and select **"Sandbox"**)
3. You are now in the sandbox – all API calls here are **free** and no real
   money is charged

---

## Step 3 – Get Your Sandbox API Key

1. Inside the Sandbox dashboard, click **"Settings"** in the left sidebar
2. Click **"API Key"**
3. An API key is already generated for your sandbox app. Copy it.

> **Tip:** Your sandbox **username** is always `sandbox` – you do not need to
> change it.

Your credentials are:

| Setting | Value |
|---------|-------|
| `AT_USERNAME` | `sandbox` |
| `AT_API_KEY` | *(the key you just copied)* |

---

## Step 4 – Install the Simulator (to Receive SMS)

Africa's Talking provides a **Simulator** so you can see outgoing messages
and send replies without a real phone.

1. In the sandbox dashboard click **"Simulator"** (left sidebar)
2. Click **"Launch Simulator"** – a pop-up phone UI will appear
3. Enter a test phone number in the simulator, e.g. `+254700000000`
4. This simulated number will **receive** any SMS you send in sandbox mode

---

## Step 5 – Configure MediTrack

Copy the root `.env.example` to `.env` and fill in your sandbox credentials:

```bash
cp .env.example .env
```

Open `.env` and set:

```dotenv
# Africa's Talking SMS
AT_USERNAME=sandbox
AT_API_KEY=<paste-your-sandbox-api-key-here>
AT_SMS_SENDER_ID=           # Leave blank for sandbox (alphanumeric sender IDs are not allowed in sandbox)

# Inbound/delivery webhook secrets (can be any string in sandbox)
AT_INBOUND_SECRET=dev-inbound-secret
AT_DELIVERY_SECRET=dev-delivery-secret
```

Restart the Django development server after editing `.env`:

```bash
cd backend
python manage.py runserver
```

---

## Step 6 – Set Up Inbound Webhook (to Receive Replies)

Africa's Talking needs a **public URL** to forward inbound SMS to MediTrack.
During local development, use **ngrok** or **localtunnel**:

```bash
# Install ngrok (once)
npm install -g ngrok

# Expose your local Django server
ngrok http 8000
```

Copy the HTTPS URL printed by ngrok, e.g. `https://abc123.ngrok.io`, then:

1. In the sandbox dashboard → **SMS** → **Callbacks**
2. Set **Incoming Messages Callback URL** to:
   `https://abc123.ngrok.io/api/messages/webhook/africastalking/`
3. Set **Delivery Reports Callback URL** to:
   `https://abc123.ngrok.io/api/messages/delivery/`
4. Click **Save**

---

## Step 7 – Send a Test SMS

### Via the MediTrack API (curl)

```bash
# 1. Obtain a JWT token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"yourpassword"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access'])")

# 2. Get a patient ID
curl -s http://localhost:8000/api/patients/ \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -40

# 3. Send an SMS to that patient (replace 1 with the actual patient ID)
curl -s -X POST http://localhost:8000/api/messages/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"patient_id": 1, "body": "Hello from MediTrack sandbox test!"}'
```

You should see the message appear in the Africa's Talking **Simulator**.

### Via the Django Shell

```bash
cd backend
python manage.py shell
```

```python
from apps.messaging.services.africastalking_service import AfricasTalkingService

result = AfricasTalkingService.send_sms('+254700000000', 'Hello from MediTrack!')
print(result)
# Expected: {'status': 'sent', 'message_id': 'ATXid...', 'error': None}
```

---

## Step 8 – Test the Full Check-in Flow

```bash
cd backend
python manage.py shell
```

```python
import datetime
from apps.checkins.scheduler import (
    create_daily_checkins_for_date,
    send_due_checkins,
)

# Create check-ins for today
result = create_daily_checkins_for_date(datetime.date.today())
print('Created:', result)

# Send them immediately (ignores scheduled_time)
from django.utils import timezone
from apps.checkins.models import DailyCheckIn
from apps.checkins.scheduler import send_due_checkins

# Force all today's scheduled check-ins to be "due" right now
DailyCheckIn.objects.filter(
    status='scheduled',
    scheduled_date=datetime.date.today()
).update(scheduled_time=timezone.now() - datetime.timedelta(minutes=1))

result = send_due_checkins()
print('Sent:', result)
```

Check the **Simulator** – the check-in message should appear on the simulated phone.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Invalid API key` | Double-check `AT_API_KEY` in `.env`; make sure you copied the **sandbox** key, not the live key |
| Messages not appearing in Simulator | Ensure the phone number in the Patient record starts with `+` and is a valid E.164 number (e.g. `+254700000000`) |
| `phonenumbers.NumberParseException` | Add the country code to the phone number when creating a patient, or set `DEFAULT_COUNTRY_CODE=KE` in `.env` |
| Inbound replies not processed | Check ngrok is running and the callback URL is set correctly in the AT sandbox dashboard |
| `africastalking package not installed` | Run `pip install africastalking` inside the backend virtual environment |

---

## Sandbox Limitations

- **No real money** – all sandbox messages are free and simulated
- **Sender ID** – alphanumeric sender IDs (e.g. `MediTrack`) are **not supported** in sandbox; leave `AT_SMS_SENDER_ID` blank
- **Delivery receipts** – the simulator always reports `Success`; failure scenarios must be tested with specific numbers listed in the AT docs
- **Rate limits** – sandbox has generous limits, but avoid sending thousands of messages in automated tests

---

## Next Steps

- See `AUTOMATED_CHECKIN_TESTING_GUIDE.md` for a complete end-to-end testing walkthrough
- See `AUTOMATED_MESSAGING_GUIDE.md` for the messaging system architecture
