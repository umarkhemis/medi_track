# Automated Check-in Testing Guide

This guide shows you how to run and verify the full automated check-in cycle in
MediTrack – from creating daily check-in records to sending SMS via Africa's
Talking sandbox, receiving replies, and triggering risk alerts.

---

## Prerequisites

1. Backend running: `cd backend && python manage.py runserver`
2. Redis running: `redis-server` (required for Celery)
3. Africa's Talking sandbox configured (see `AFRICA_TALKING_SANDBOX_GUIDE.md`)
4. At least one active patient with `monitoring_active=True`, `sms_opt_in=True`,
   and a valid E.164 phone number

---

## Architecture Overview

```
Celery Beat (scheduler)
    │
    ├─ Every day at 00:05 UTC ──► create_daily_checkins
    │                                Creates one DailyCheckIn per active patient
    │
    ├─ Every 15 minutes ──────────► send_due_checkins
    │                                Sends SMS to patients whose check-in time has arrived
    │
    ├─ Every 30 minutes ──────────► send_checkin_reminders
    │                                Re-sends to patients who haven't replied after 4 hours
    │
    └─ Daily at 23:30 UTC ────────► mark_missed_checkins
                                     Marks unanswered check-ins as "missed"

Patient replies via SMS
    │
    └─ AT Inbound Webhook ────────► /api/messages/webhook/africastalking/
                                     Parses reply, records CheckInResponse,
                                     runs risk assessment, triggers alerts
```

---

## Quick Manual Test (No Celery Required)

### 1 – Create a Test Patient

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"yourpassword"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access'])")

curl -s -X POST http://localhost:8000/api/patients/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "last_name": "Doe",
    "phone_number_raw": "+254700000001",
    "condition": "heart failure",
    "monitoring_active": true,
    "sms_opt_in": true,
    "discharge_date": "2026-04-20"
  }'
```

### 2 – Trigger Check-in Creation

```bash
cd backend
python manage.py shell
```

```python
import datetime
from apps.checkins.scheduler import create_daily_checkins_for_date

result = create_daily_checkins_for_date(datetime.date.today())
print(result)
# {'created': 1, 'skipped': 0, 'date': '2026-04-28'}
```

### 3 – Force the Check-in to Be "Due" and Send It

```python
from django.utils import timezone
from apps.checkins.models import DailyCheckIn
from apps.checkins.scheduler import send_due_checkins
import datetime

# Make all today's check-ins immediately due
DailyCheckIn.objects.filter(
    status='scheduled',
    scheduled_date=datetime.date.today()
).update(scheduled_time=timezone.now() - datetime.timedelta(minutes=1))

result = send_due_checkins()
print(result)
# {'sent': 1, 'failed': 0}
```

Check the Africa's Talking **Simulator** – you should see a message like:

> Hello Jane, your daily heart check-in. Reply 1 for each YES, 2 for NO:
> 1) Chest pain? 2) Shortness of breath? 3) Leg swelling? 4) Took medications?

### 4 – Simulate a Patient Reply (via Webhook)

```bash
curl -s -X POST http://localhost:8000/api/messages/webhook/africastalking/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "from=+254700000001" \
  --data-urlencode "to=+254900000000" \
  --data-urlencode "text=2 2 2 1" \
  --data-urlencode "id=test-inbound-001" \
  --data-urlencode "date=2026-04-28T10:00:00Z"
```

The system will:
- Match the patient by phone number
- Parse the response and record `CheckInResponse` entries
- Update the `DailyCheckIn` status to `completed`
- Run risk assessment and trigger alerts if needed

### 5 – Verify the Result

```python
from apps.checkins.models import DailyCheckIn, CheckInResponse
import datetime

ci = DailyCheckIn.objects.get(
    patient__phone_number_e164='+254700000001',
    scheduled_date=datetime.date.today()
)
print('Status:', ci.status)
print('Responses:', list(ci.responses.values('question_key', 'response_value')))

from apps.alerts.models import Alert
alerts = Alert.objects.filter(patient__phone_number_e164='+254700000001')
print('Alerts:', list(alerts.values('severity', 'trigger_reason', 'status')))
```

---

## Running With Celery (Full Production Flow)

### Start All Services

```bash
# Terminal 1 – Django dev server
cd backend && python manage.py runserver

# Terminal 2 – Redis (if not running as a daemon)
redis-server

# Terminal 3 – Celery worker
cd backend && celery -A meditrack worker --loglevel=info

# Terminal 4 – Celery Beat (scheduler)
cd backend && celery -A meditrack beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Run Migrations for Celery Beat

The `django_celery_beat` package requires its own database tables:

```bash
cd backend
python manage.py migrate django_celery_beat
python manage.py migrate
```

### Trigger Tasks Manually via Celery

```bash
cd backend
python manage.py shell
```

```python
from apps.checkins.tasks import (
    create_daily_checkins,
    send_due_checkins_task,
    send_checkin_reminders_task,
    mark_missed_checkins_task,
)

# Run each task synchronously (useful for debugging)
create_daily_checkins.apply()
send_due_checkins_task.apply()
send_checkin_reminders_task.apply()
mark_missed_checkins_task.apply()
```

### Monitor Celery Task Status

```bash
# View scheduled tasks
celery -A meditrack inspect scheduled

# View currently active tasks
celery -A meditrack inspect active

# View task statistics
celery -A meditrack inspect stats
```

---

## Test the Reminder Flow

### Simulate a Patient Who Doesn't Reply

```python
import datetime
from django.utils import timezone
from apps.checkins.models import DailyCheckIn
from apps.checkins.scheduler import send_checkin_reminders

# Get a sent check-in and backdate the sent_time to trigger reminder
ci = DailyCheckIn.objects.filter(
    status='sent',
    scheduled_date=datetime.date.today()
).first()

if ci:
    ci.sent_time = timezone.now() - datetime.timedelta(hours=5)
    ci.save(update_fields=['sent_time'])

    result = send_checkin_reminders(reminder_delay_hours=4)
    print('Reminders sent:', result)
    # {'sent': 1}
```

---

## Test the Missed Check-in Flow

```python
import datetime
from apps.checkins.models import DailyCheckIn
from apps.checkins.scheduler import mark_missed_checkins

# Create a check-in for yesterday with status 'sent' to simulate a missed one
from apps.patients.models import Patient
patient = Patient.objects.filter(monitoring_active=True).first()

ci, _ = DailyCheckIn.objects.get_or_create(
    patient=patient,
    scheduled_date=datetime.date.today() - datetime.timedelta(days=1),
    defaults={'status': 'sent'},
)
ci.status = 'sent'
ci.save()

result = mark_missed_checkins()
print('Marked as missed:', result)
# {'marked': 1}

ci.refresh_from_db()
print('New status:', ci.status)
# missed
```

---

## End-to-End curl Test Script

Save as `/tmp/test_checkins.sh` and run with `bash /tmp/test_checkins.sh`:

```bash
#!/usr/bin/env bash
set -e

BASE=http://localhost:8000/api

# 1. Login
echo "=== Login ==="
TOKEN=$(curl -s -X POST "$BASE/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"yourpassword"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access'])")
echo "Token obtained"

# 2. Create patient
echo "=== Create patient ==="
PATIENT=$(curl -s -X POST "$BASE/patients/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Test",
    "last_name": "Patient",
    "phone_number_raw": "+254700999001",
    "condition": "heart failure",
    "monitoring_active": true,
    "sms_opt_in": true,
    "discharge_date": "2026-04-20"
  }')
PATIENT_ID=$(echo "$PATIENT" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Patient ID: $PATIENT_ID"

# 3. Send a manual message
echo "=== Send SMS ==="
curl -s -X POST "$BASE/messages/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"patient_id\": $PATIENT_ID, \"body\": \"Hello from automated test\"}" \
  | python3 -m json.tool

# 4. Simulate inbound reply
echo "=== Inbound reply ==="
curl -s -X POST "$BASE/messages/webhook/africastalking/" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "from=+254700999001" \
  --data-urlencode "to=+254900000000" \
  --data-urlencode "text=YES" \
  --data-urlencode "id=test-$(date +%s)"

echo ""
echo "=== Done ==="
```

---

## Interpreting Check-in Statuses

| Status | Meaning |
|--------|---------|
| `scheduled` | Check-in created, waiting to be sent |
| `sent` | SMS delivered to AT, awaiting patient reply |
| `reminded` | Reminder SMS sent, still awaiting reply |
| `completed` | Patient replied; response recorded |
| `missed` | Patient did not reply before expiration |
| `skipped` | Patient's follow-up period ended |

---

## Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `{'sent': 0, 'failed': 1}` | Invalid phone number or AT API key | Check `phone_number_e164` on patient; verify `AT_API_KEY` in `.env` |
| `No active check-in template found` | `MessageTemplate` with `template_type='checkin'` and `is_active=True` doesn't exist | Create one via Django admin at `/admin/messaging/messagetemplate/` |
| `Celery task not running` | Worker not started | Run `celery -A meditrack worker --loglevel=info` |
| `django_celery_beat` table error | Missing migration | Run `python manage.py migrate django_celery_beat` |
| Check-in not created | Patient has `monitoring_active=False` or `sms_opt_in=False` | Update the patient record |

---

## Creating a Default Check-in Template (if none exists)

```python
from apps.messaging.models import MessageTemplate

MessageTemplate.objects.create(
    name='Default Daily Check-in',
    template_type='checkin',
    condition='all',
    body=(
        "Hello {first_name}, this is your MediTrack daily check-in. "
        "Please reply YES if you have any symptoms today, or NO if you feel fine. "
        "Reply STOP to opt out."
    ),
    is_active=True,
)
```

For condition-specific templates:

```python
MessageTemplate.objects.create(
    name='Heart Failure Daily Check-in',
    template_type='checkin',
    condition='heart failure',
    body=(
        "Hello {first_name}, your daily heart check-in. "
        "Reply 1 for YES, 2 for NO: "
        "1) Chest pain? 2) Shortness of breath? 3) Leg swelling? 4) Took medications?"
    ),
    is_active=True,
)
```
