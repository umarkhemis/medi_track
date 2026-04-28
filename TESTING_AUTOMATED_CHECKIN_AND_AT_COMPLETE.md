# Complete Testing Guide: Automated Check-in & Africa's Talking

This guide shows you **exactly** how to test and verify that automated check-ins and Africa's Talking SMS are working end-to-end.

---

## Part 1: Get Africa's Talking Sandbox Credentials

### Step 1: Create Africa's Talking Account

1. Go to https://africastalking.com/
2. Click **"Sign up"** in top right
3. Fill in your details:
   - Email: Your email
   - Username: Something like `your_username_meditrack`
   - Password: Strong password
   - Organization: Your name or company
4. Click **"Create Account"**
5. Check your email for verification link
6. Click verification link

### Step 2: Get Your Sandbox API Key

1. After logging in, go to **Dashboard**
2. In left sidebar, click **"Settings"** → **"API Keys"**
3. You'll see:
   - **API Username**: `sandbox` (for testing)
   - **API Key**: Long string like `4e3a7e8f5d6b9c2a1f8e3d7b9c2e5a8f` - **COPY THIS**
4. Keep these safe - you'll need them

### Step 3: Get Sandbox Test Phone Number

1. In Dashboard, go to **"Settings"** → **"Account"**
2. Look for **"Sandbox Phone Number"** or **"Test Phone Number"**
3. Or use any phone number starting with your country code (examples):
   - Kenya: `+254720XXXXXX`
   - Uganda: `+256701XXXXXX`
   - Tanzania: `+255655XXXXXX`
   - Nigeria: `+234803XXXXXX`

**Your sandbox number**: `+254720XXXXXX` (replace X with any digits)

### Step 4: Understand Sandbox Mode

In **sandbox mode**:
- SMS won't actually send to real phones
- You can test the API without sending real messages
- Responses are simulated
- Perfect for development!

---

## Part 2: Configure Your Backend

### Step 1: Update `.env` File

Open `backend/.env` and update these lines:

```env
# Africa's Talking Configuration
AT_USERNAME=sandbox
AT_API_KEY=4e3a7e8f5d6b9c2a1f8e3d7b9c2e5a8f
AT_SMS_SENDER_ID=MediTrack
AT_INBOUND_SECRET=your-inbound-secret-key
AT_DELIVERY_SECRET=your-delivery-secret-key
DEFAULT_COUNTRY_CODE=KE

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

**Replace**:
- `4e3a7e8f5d6b9c2a1f8e3d7b9c2e5a8f` = Your actual API Key from Step 2
- `KE` = Your country code (KE, UG, TZ, NG, etc.)

### Step 2: Install Redis (Required for Celery)

**On macOS:**
```bash
brew install redis
brew services start redis
```

**On Ubuntu/Debian:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
```

**On Windows (using WSL or Docker):**
```bash
docker run -d -p 6379:6379 redis:latest
```

**Verify Redis is running:**
```bash
redis-cli ping
# Should return: PONG
```

### Step 3: Start Django Development Server

Open a terminal and run:

```bash
cd backend
python manage.py runserver
```

You should see:
```
Starting development server at http://127.0.0.1:8000/
```

### Step 4: Start Celery Worker (in NEW terminal)

Open a **new terminal** and run:

```bash
cd backend
celery -A meditrack worker -l info
```

You should see:
```
[2026-04-28 10:30:45,123: INFO/MainProcess] celery@your-machine ready.
```

### Step 5: Start Celery Beat (in ANOTHER NEW terminal)

Open **another new terminal** and run:

```bash
cd backend
celery -A meditrack beat -l info
```

You should see:
```
[2026-04-28 10:35:12,456: INFO/MainProcess] Starting scheduler...
```

**Now you have 3 terminals running:**
1. Django server (port 8000)
2. Celery worker
3. Celery beat scheduler

---

## Part 3: Create Test Data

### Step 1: Create Superuser (Admin Account)

```bash
cd backend
python manage.py createsuperuser
```

Follow prompts:
- Email: `admin@test.com`
- First name: `Admin`
- Last name: `User`
- Password: `testpass123`
- Re-enter password: `testpass123`

### Step 2: Access Django Admin

1. Open browser: `http://localhost:8000/admin/`
2. Login with:
   - Email: `admin@test.com`
   - Password: `testpass123`

### Step 3: Create a Provider

1. Click **"Users"** → **"Add User"**
2. Fill in:
   - Email: `doctor@hospital.com`
   - First name: `John`
   - Last name: `Doctor`
   - Role: **Provider**
   - Password: `provider123`
3. Click **"Save"**

### Step 4: Create a Provider Profile

1. Go back to Admin home
2. Click **"Providers"** → **"Add Provider"**
3. Fill in:
   - User: Select "John Doctor"
   - Department: "Cardiology"
   - Specialization: "Heart Failure"
   - License number: "LIC123456"
   - Phone: `+254720111222`
4. Click **"Save"**

### Step 5: Create a Test Patient

1. Go to **"Patients"** → **"Add Patient"**
2. Fill in:
   - First name: `Jane`
   - Last name: `Patient`
   - Date of birth: `1985-05-15`
   - Gender: `Female`
   - Phone number: `+254720999888` (use sandbox phone)
   - Condition: `heart failure`
   - Discharge date: `2026-04-20`
   - Follow-up end date: `2026-05-20`
   - Assigned provider: Select "John Doctor"
   - Monitoring active: ✓ Check
   - SMS opt-in: ✓ Check
   - Preferred check-in time: `09:00`
3. Click **"Save"**

**✅ You now have:**
- Provider account
- Patient assigned to provider
- Patient ready to receive check-ins

---

## Part 4: Test Automated Check-in Manually

### Test 1: Manually Trigger Check-in Creation

Open a Python shell:

```bash
cd backend
python manage.py shell
```

Run this code:

```python
from apps.checkins.scheduler import create_daily_checkins_for_date
from datetime import date

# Create check-ins for today
result = create_daily_checkins_for_date(date.today())
print(result)
# Output: {'created': 1, 'skipped': 0, 'date': '2026-04-28'}
```

**What happened:**
- ✅ 1 check-in created for Jane Patient
- The check-in is in "SCHEDULED" status
- Scheduled time is 09:00 (from her preferred check-in time)

### Test 2: Verify Check-in in Database

Still in Python shell:

```python
from apps.checkins.models import DailyCheckIn
from apps.patients.models import Patient

patient = Patient.objects.get(first_name='Jane')
checkins = DailyCheckIn.objects.filter(patient=patient)

for checkin in checkins:
    print(f"ID: {checkin.id}")
    print(f"Patient: {checkin.patient.first_name}")
    print(f"Status: {checkin.status}")
    print(f"Scheduled Time: {checkin.scheduled_time}")
    print(f"Questions: {checkin.question_keys}")
    print("---")
```

**Output should show:**
```
ID: 1
Patient: Jane
Status: scheduled
Scheduled Time: 2026-04-28 09:00:00+00:00
Questions: ['chest_pain', 'shortness_of_breath', 'leg_swelling', 'medication_taken']
```

### Test 3: Manually Trigger SMS Sending

Still in Python shell:

```python
from apps.checkins.scheduler import send_due_checkins
import datetime
from django.utils import timezone

# Make the check-in "due" by setting scheduled_time to now
checkin = DailyCheckIn.objects.first()
checkin.scheduled_time = timezone.now()
checkin.save()

# Now send it
result = send_due_checkins()
print(result)
# Output: {'sent': 1, 'failed': 0}
```

**What happened:**
- ✅ SMS message created
- ✅ Sent to Africa's Talking API
- ✅ Check-in status changed to "sent"

### Test 4: Check Message Was Sent

Still in Python shell:

```python
from apps.messaging.models import Message

# Get the message
msg = Message.objects.filter(patient__first_name='Jane').first()

if msg:
    print(f"To: {msg.to_number}")
    print(f"Body: {msg.body}")
    print(f"Status: {msg.status}")
    print(f"Provider Message ID: {msg.provider_message_id}")
    print(f"Sent At: {msg.sent_at}")
else:
    print("No message found")
```

**Output should show:**
```
To: +254720999888
Body: Hello Jane, your daily heart check-in. Reply 1 for each YES, 2 for NO: 1) Chest pain? 2) Shortness of breath? 3) Leg swelling? 4) Took medications?
Status: sent
Provider Message ID: SMbd7e8f3f... (from Africa's Talking)
Sent At: 2026-04-28 10:45:32.123456+00:00
```

**Type:** `exit()` to leave Python shell

---

## Part 5: Test via API (Using Curl)

### Test 1: Login as Provider

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "doctor@hospital.com",
    "password": "provider123"
  }'
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Copy the `access` token** - you'll need it for next requests.

### Test 2: Check Patient List

Replace `YOUR_ACCESS_TOKEN` with the token from above:

```bash
curl -X GET http://localhost:8000/api/patients/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "first_name": "Jane",
      "last_name": "Patient",
      "phone_number_e164": "+254720999888",
      "condition": "heart failure",
      "monitoring_active": true,
      "sms_opt_in": true
    }
  ]
}
```

### Test 3: Get Patient's Check-ins

```bash
curl -X GET http://localhost:8000/api/patients/1/checkins/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "patient": 1,
      "scheduled_date": "2026-04-28",
      "scheduled_time": "2026-04-28T09:00:00Z",
      "status": "sent",
      "question_keys": ["chest_pain", "shortness_of_breath", "leg_swelling", "medication_taken"]
    }
  ]
}
```

### Test 4: Get Messages Sent

```bash
curl -X GET http://localhost:8000/api/messages/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "to_number": "+254720999888",
      "body": "Hello Jane, your daily heart check-in...",
      "status": "sent",
      "is_automated": true,
      "sent_at": "2026-04-28T10:45:32.123456Z"
    }
  ]
}
```

---

## Part 6: Test Patient Response (Simulated)

### Simulate Patient Replying to SMS

In real life, patient would reply by SMS. For testing, we simulate this by calling the webhook:

```bash
curl -X POST http://localhost:8000/api/messages/webhook/africastalking/ \
  -H "Content-Type: application/json" \
  -d '{
    "from": "+254720999888",
    "to": "+254720111111",
    "text": "1 2 3 1",
    "id": "AFXI256b922e2aca8b21c5717de9f2b8d1f21",
    "date": "2026-04-28 11:00:00",
    "type": "incoming"
  }'
```

**Response:**
```json
{
  "status": "ok",
  "processed": true
}
```

### Verify Response Was Processed

In Python shell:

```python
from apps.checkins.models import CheckInResponse, DailyCheckIn

# Get the check-in
checkin = DailyCheckIn.objects.first()

# Get responses
responses = CheckInResponse.objects.filter(checkin=checkin)

for resp in responses:
    print(f"Question: {resp.question_key}")
    print(f"Response: {resp.response_text}")
    print(f"Value: {resp.response_value}")
    print("---")
```

**Output:**
```
Question: chest_pain
Response: 1
Value: 1
---
Question: shortness_of_breath
Response: 2
Value: 2
---
Question: leg_swelling
Response: 3
Value: 3
---
Question: medication_taken
Response: 1
Value: 1
```

---

## Part 7: Verify Risk Assessment & Alerts

### Check if Alert Was Created

In Python shell:

```python
from apps.alerts.models import Alert
from apps.patients.models import Patient

patient = Patient.objects.get(first_name='Jane')
alerts = Alert.objects.filter(patient=patient)

for alert in alerts:
    print(f"ID: {alert.id}")
    print(f"Severity: {alert.severity}")
    print(f"Status: {alert.status}")
    print(f"Title: {alert.title}")
    print(f"Description: {alert.description}")
    print("---")
```

**Example Output:**
```
ID: 1
Severity: yellow
Status: active
Title: Moderate Risk Detected
Description: Patient showing elevated symptoms. Shortness of breath level: 2
```

### Check Risk Level

```python
patient = Patient.objects.get(first_name='Jane')
print(f"Current Risk Level: {patient.current_risk_level}")
# Output: Current Risk Level: yellow
```

---

## Part 8: Complete End-to-End Test (Real-Time)

This shows the **full flow** happening automatically:

### Step 1: Set Patient's Check-in Time to Now

In Python shell:

```python
from apps.patients.models import Patient
from datetime import time

patient = Patient.objects.get(first_name='Jane')
patient.preferred_check_in_time = time(10, 30)  # Set to 10:30 AM
patient.save()
```

### Step 2: Create Check-in for Today

```python
from apps.checkins.scheduler import create_daily_checkins_for_date
from datetime import date

result = create_daily_checkins_for_date(date.today())
print(f"Created: {result}")
```

### Step 3: Watch Celery Beat (Look at Terminal 3)

In the **Celery Beat terminal**, you should see logs like:

```
[2026-04-28 10:30:45,123: INFO/MainProcess] Scheduler: Sending scheduled message for check-in 2
[2026-04-28 10:30:45,456: INFO/MainProcess] Sent check-in SMS to +254720999888
```

### Step 4: Watch Celery Worker (Look at Terminal 2)

In the **Celery Worker terminal**, you should see:

```
[2026-04-28 10:30:45,789: INFO/Worker] apps.checkins.tasks.send_due_checkins[abc123] STARTED
[2026-04-28 10:30:46,012: INFO/Worker] apps.checkins.tasks.send_due_checkins[abc123] SUCCESS
```

### Step 5: Verify in Database

```python
from apps.messaging.models import Message

msg = Message.objects.filter(is_automated=True).latest('sent_at')
print(f"✅ Message sent to: {msg.to_number}")
print(f"✅ Status: {msg.status}")
print(f"✅ Sent at: {msg.sent_at}")
```

**✅ SUCCESS!** Your automated check-in and Africa's Talking are working!

---

## Part 9: Verify Logs

### Django Server Logs

Look at **Terminal 1** (Django server). You should see:

```
[2026-04-28 10:30:45,123] INFO apps.messaging.services.africastalking_service: AfricasTalking SMS sent successfully to +254720999888
[2026-04-28 10:30:45,456] INFO apps.checkins.scheduler: send_due_checkins: sent=1, failed=0
```

### Celery Worker Logs

Look at **Terminal 2** (Celery Worker). You should see:

```
[2026-04-28 10:30:00,000: INFO/MainProcess] Received task: apps.checkins.tasks.send_due_checkins[f47e6522-8a92-4321-bb84-9f3c3d8e2f5a]
[2026-04-28 10:30:01,000: INFO/MainProcess] Task apps.checkins.tasks.send_due_checkins[f47e6522] returned {'sent': 1, 'failed': 0}
```

### Celery Beat Logs

Look at **Terminal 3** (Celery Beat). You should see:

```
[2026-04-28 10:30:05,000: DEBUG/MainProcess] Scheduler: Sending message for check-in ID 1
[2026-04-28 10:30:05,123: DEBUG/MainProcess] Scheduler: Check-in 1 scheduled for time 10:30, current time 10:30:05, will send
```

---

## Part 10: Test Reminders (4+ hours after check-in)

### Simulate Waiting 4 Hours

```python
from apps.checkins.models import DailyCheckIn
from datetime import datetime, timedelta
from django.utils import timezone

checkin = DailyCheckIn.objects.first()
checkin.sent_time = timezone.now() - timedelta(hours=4, minutes=1)
checkin.save()
```

### Trigger Reminder

```python
from apps.checkins.scheduler import send_checkin_reminders

result = send_checkin_reminders(reminder_delay_hours=4)
print(result)
# Output: {'sent': 1}
```

### Verify Reminder Message

```python
from apps.messaging.models import Message

# Get latest message (should be the reminder)
msg = Message.objects.filter(patient__first_name='Jane').order_by('-sent_at').first()
print(f"Message: {msg.body}")
# Should contain "reminder"
```

---

## Part 11: Test Missing Check-in Marking

### Simulate Check-in Expiring

```python
from apps.checkins.models import DailyCheckIn
from datetime import datetime, timedelta
from django.utils import timezone

checkin = DailyCheckIn.objects.first()
checkin.expiration_time = timezone.now() - timedelta(hours=1)
checkin.save()
```

### Mark Missed

```python
from apps.checkins.scheduler import mark_missed_checkins

result = mark_missed_checkins()
print(result)
# Output: {'marked': 1}
```

### Verify Status Changed

```python
checkin = DailyCheckIn.objects.first()
print(f"Status: {checkin.status}")
# Output: Status: missed
```

---

## Part 12: Debugging Africa's Talking Connection

### Test Africa's Talking Connection

```python
from apps.messaging.services.africastalking_service import AfricasTalkingService

# Try sending a test SMS
result = AfricasTalkingService.send_sms(
    to="+254720999888",
    message="Test message from MediTrack"
)

print(result)
# Output: {'status': 'sent', 'message_id': 'SMbd7e8f3f...', 'error': None}
```

### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| `Invalid API Key` | Wrong API key in `.env` | Check `.env` has correct `AT_API_KEY` from Africa's Talking dashboard |
| `Invalid username` | Wrong username in `.env` | Use `sandbox` for testing, or your actual username for production |
| `Invalid phone number` | Wrong format | Use E.164 format: `+254720999888` |
| `Network error` | Can't reach Africa's Talking | Check internet connection, check firewall |
| `Message not sending` | Celery not running | Verify Terminal 2 (Celery Worker) is running |
| `Check-in not created` | Database issue | Verify patient exists, check `monitoring_active=True`, `sms_opt_in=True` |
| `Redis connection error` | Redis not running | Run `redis-server` or start Docker Redis |

---

## Part 13: Complete Working Example (Copy & Paste)

Save this as `backend/test_automation.py`:

```python
#!/usr/bin/env python
"""
Complete test of automated check-in and Africa's Talking.
Run from: python backend/test_automation.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meditrack.settings')
django.setup()

from datetime import date, time, datetime, timedelta
from django.utils import timezone
from apps.patients.models import Patient
from apps.providers.models import Provider
from apps.users.models import User
from apps.checkins.models import DailyCheckIn, CheckInResponse
from apps.messaging.models import Message
from apps.alerts.models import Alert
from apps.checkins.scheduler import (
    create_daily_checkins_for_date,
    send_due_checkins,
    send_checkin_reminders
)

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_full_flow():
    print_section("AUTOMATED CHECK-IN & AFRICA'S TALKING TEST")
    
    # 1. Get or create provider
    print("1️⃣ Checking Provider...")
    provider_user = User.objects.filter(email='doctor@hospital.com').first()
    if not provider_user:
        print("❌ Provider not found! Create via Django admin first.")
        return
    
    provider = Provider.objects.get(user=provider_user)
    print(f"✅ Provider found: {provider.user.get_full_name()}")
    
    # 2. Get or create patient
    print("\n2️⃣ Checking Patient...")
    patient = Patient.objects.filter(first_name='Jane').first()
    if not patient:
        print("❌ Patient not found! Create via Django admin first.")
        return
    
    print(f"✅ Patient found: {patient.first_name} {patient.last_name}")
    print(f"   Phone: {patient.phone_number_e164}")
    print(f"   Condition: {patient.condition}")
    print(f"   Monitoring Active: {patient.monitoring_active}")
    print(f"   SMS Opt-in: {patient.sms_opt_in}")
    
    # 3. Create check-in
    print("\n3️⃣ Creating Check-in...")
    result = create_daily_checkins_for_date(date.today())
    print(f"✅ Check-in creation result: {result}")
    
    # 4. Send check-in
    print("\n4️⃣ Sending Check-in SMS...")
    # Make it due by setting to past time
    checkin = DailyCheckIn.objects.filter(patient=patient).first()
    if checkin:
        checkin.scheduled_time = timezone.now()
        checkin.save()
        
        result = send_due_checkins()
        print(f"✅ Send result: {result}")
        
        # Check message
        msg = Message.objects.filter(checkin=checkin).first()
        if msg:
            print(f"✅ Message sent:")
            print(f"   To: {msg.to_number}")
            print(f"   Status: {msg.status}")
            print(f"   Body: {msg.body[:50]}...")
    
    # 5. Simulate patient response
    print("\n5️⃣ Simulating Patient Response...")
    if checkin:
        CheckInResponse.objects.create(
            checkin=checkin,
            question_key='chest_pain',
            response_text='1',
            response_value=1
        )
        CheckInResponse.objects.create(
            checkin=checkin,
            question_key='shortness_of_breath',
            response_text='2',
            response_value=2
        )
        print("✅ Patient responses recorded")
        
        # Check for alerts
        alerts = Alert.objects.filter(patient=patient)
        if alerts.exists():
            alert = alerts.first()
            print(f"✅ Alert created:")
            print(f"   Severity: {alert.severity}")
            print(f"   Status: {alert.status}")
        else:
            print("⚠️  No alert created (responses may not trigger risk threshold)")
    
    # 6. Summary
    print("\n" + "="*60)
    print("  ✅ TEST COMPLETE!")
    print("="*60)
    print(f"""
Summary:
- Check-in created: {result.get('created', 0)}
- Message sent: {'✅ Yes' if msg and msg.status == 'sent' else '❌ No'}
- Patient responses: 2
- Alerts generated: {alerts.count() if alerts.exists() else 0}

Next Steps:
1. Check Django logs for Africa's Talking integration
2. Verify message in Django admin: Messages
3. Monitor Celery worker for task execution
4. Check alerts in Django admin: Alerts
    """)

if __name__ == '__main__':
    test_full_flow()
```

Run it:

```bash
cd backend
python test_automation.py
```

**Expected Output:**
```
============================================================
  AUTOMATED CHECK-IN & AFRICA'S TALKING TEST
============================================================

1️⃣ Checking Provider...
✅ Provider found: John Doctor

2️⃣ Checking Patient...
✅ Patient found: Jane Patient
   Phone: +254720999888
   Condition: heart failure
   Monitoring Active: True
   SMS Opt-in: True

3️⃣ Creating Check-in...
✅ Check-in creation result: {'created': 1, 'skipped': 0, 'date': '2026-04-28'}

4️⃣ Sending Check-in SMS...
✅ Send result: {'sent': 1, 'failed': 0}
✅ Message sent:
   To: +254720999888
   Status: sent
   Body: Hello Jane, your daily heart check-in...

5️⃣ Simulating Patient Response...
✅ Patient responses recorded

============================================================
  ✅ TEST COMPLETE!
============================================================
```

---

## Summary: How to Verify Everything Works

### ✅ Check-in is Scheduled
```bash
# In Python shell
DailyCheckIn.objects.filter(patient__first_name='Jane').values()
# Should show status='scheduled'
```

### ✅ SMS is Sent
```bash
# In Python shell
Message.objects.filter(is_automated=True, patient__first_name='Jane').values()
# Should show status='sent'
```

### ✅ Africa's Talking Connected
```bash
# In Python shell
result = AfricasTalkingService.send_sms('+254720999888', 'Test')
print(result['status'])
# Should show: 'sent' (not 'failed')
```

### ✅ Celery is Running
- Terminal 2: Should show active tasks
- Terminal 3: Should show scheduled tasks

### ✅ Patient Response Processed
```bash
# In Python shell
CheckInResponse.objects.filter(checkin__patient__first_name='Jane').count()
# Should be > 0
```

### ✅ Risk Assessment Works
```bash
# In Python shell
Patient.objects.get(first_name='Jane').current_risk_level
# Should show 'green', 'yellow', or 'red'
```

### ✅ Alerts Generated
```bash
# In Python shell
Alert.objects.filter(patient__first_name='Jane').count()
# Should be > 0 if risk level is yellow or red
```

---

## Troubleshooting Quick Reference

| Problem | Check This | Command |
|---------|-----------|---------|
| No check-ins created | Patient exists & monitoring_active=True | `Patient.objects.get(first_name='Jane').monitoring_active` |
| Messages not sending | Celery worker running | Look at Terminal 2 logs |
| Africa's Talking error | API key & username correct | Check `.env` file |
| Reminders not sent | 4+ hours since check-in sent | Manually test `send_checkin_reminders()` |
| Alerts not created | Risk score exceeds threshold | Check `RiskAssessmentService` logic |
| Redis error | Redis server running | `redis-cli ping` → should return PONG |

---

## You're Done! 🎉

Your automated check-in system and Africa's Talking integration are now fully tested and verified!

**Next:** Deploy to production or continue development with confidence.
