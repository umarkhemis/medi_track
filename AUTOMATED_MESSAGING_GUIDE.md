# Automated Messaging System - Complete Guide

## Overview

MediTrack now has **FULL AUTOMATED MESSAGING FUNCTIONALITY** for sending SMS and WhatsApp messages to patients based on their discharge data and processing their responses.

## How It Works

### 1. Patient Discharge Setup

When a patient is discharged from the hospital:
- Patient record created with: `discharge_date`, `condition`, `medications`, `preferred_check_in_time`
- Patient marked as `monitoring_active=True`
- Example conditions: heart_failure, copd, diabetes, hypertension, pneumonia

### 2. Automated Daily Check-in Flow

**Step 1: Schedule Creation (Midnight Daily)**
- Celery Beat task runs at midnight: `schedule_daily_checkins`
- Creates `DailyCheckIn` records for all active patients
- Status: `scheduled`

**Step 2: Message Sending (Every 5 Minutes)**
- Celery Beat task: `send_scheduled_checkins`
- Finds check-ins where `scheduled_time` has passed
- Loads appropriate `MessageTemplate` based on patient's condition
- Formats message with patient data (name, condition, etc.)
- Sends via Twilio SMS or WhatsApp
- Updates check-in status to `sent`
- Creates `Message` record with `is_automated=True`

**Step 3: Patient Response (Real-time)**
- Patient receives message like:
  ```
  Good morning John! How are you feeling today?
  
  Please rate 1-10:
  1. Shortness of breath?
  2. Swelling in legs?
  3. Fatigue level?
  
  Reply with numbers (e.g., 3 5 7)
  ```
- Patient replies: `4 6 3`
- Twilio sends to webhook: `/api/messages/webhook/twilio/`
- System processes response:
  - Creates `CheckInResponse` records for each answer
  - Parses numeric responses (0-10 scale)
  - Updates check-in status to `in_progress`

**Step 4: Risk Assessment (Automatic)**
- When responses complete, `RiskAssessmentService` activates
- Calculates risk score using condition-specific symptom weights
- Example for heart_failure:
  - Shortness of breath: weight 2.5 (critical)
  - Swelling: weight 1.8 (important)
  - Fatigue: weight 1.2 (moderate)
- Formula: `risk_score = Σ(response_value × weight) / total_possible × 10`
- Determines risk level:
  - `green`: score 0-3 (low risk)
  - `yellow`: score 3-6.5 (moderate risk)
  - `red`: score 6.5-10 (high risk)

**Step 5: Alert Generation (Automatic)**
- If risk level is `yellow` or `red`:
  - Creates `Alert` record automatically
  - Status: `active`
  - Includes: trigger reason, concerning symptoms, timestamp
  - Links to the check-in
  - Updates patient's `current_risk_level`
- Provider sees alert in dashboard immediately

**Step 6: Reminders (Every 30 Minutes)**
- Celery Beat task: `send_reminders`
- Finds check-ins sent >2 hours ago with no response
- Sends reminder message via SMS/WhatsApp
- Example: "Reminder: Please complete your daily health check-in"

**Step 7: Missed Check-ins (11 PM Daily)**
- Celery Beat task: `mark_missed_checkins`
- Marks yesterday's incomplete check-ins as `missed`
- Helps providers identify non-compliant patients

## Architecture

### Files Created/Updated

```
backend/
├── meditrack/
│   ├── __init__.py                          ✅ UPDATED - Added Celery import
│   └── celery.py                            ✅ NEW - Celery app configuration
│
├── apps/messaging/
│   ├── services/
│   │   ├── __init__.py                      ✅ NEW
│   │   └── twilio_service.py                ✅ NEW - SMS/WhatsApp sending
│   └── views.py                             ✅ UPDATED - Integrated TwilioService
│
└── apps/checkins/
    ├── services/
    │   ├── __init__.py                      ✅ NEW
    │   ├── scheduler.py                     ✅ NEW - Check-in scheduling
    │   └── risk_assessment.py               ✅ NEW - Risk calculation
    └── tasks.py                             ✅ NEW - Celery tasks
```

### Components

#### 1. TwilioService (`apps/messaging/services/twilio_service.py`)
- `send_sms(to_number, message)` - Send SMS via Twilio
- `send_whatsapp(to_number, message)` - Send WhatsApp via Twilio
- `send_message(to_number, message, channel)` - Universal sender
- `format_message(template, patient)` - Replace placeholders

#### 2. CheckInScheduler (`apps/checkins/services/scheduler.py`)
- `create_daily_checkins(date)` - Create check-in records
- `send_pending_checkins()` - Send messages for scheduled check-ins
- `send_checkin_message(checkin)` - Send individual check-in
- `send_reminders()` - Send reminder messages
- `send_reminder_message(checkin)` - Send individual reminder
- `mark_missed_checkins()` - Mark incomplete check-ins

#### 3. RiskAssessmentService (`apps/checkins/services/risk_assessment.py`)
- `calculate_risk_score(checkin)` - Calculate 0-10 risk score
- `get_risk_level(score)` - Convert score to green/yellow/red
- `process_checkin(checkin)` - Complete processing pipeline
- `create_alert(checkin, risk_level, score)` - Generate alerts
- `parse_response_value(text, question_key)` - Parse patient responses

#### 4. Celery Tasks (`apps/checkins/tasks.py`)
- `schedule_daily_checkins()` - Runs at midnight
- `send_scheduled_checkins()` - Runs every 5 minutes
- `send_reminders()` - Runs every 30 minutes
- `mark_missed_checkins()` - Runs at 11 PM

## Setup Instructions

### 1. Install Dependencies (Already in requirements.txt)
```bash
pip install celery redis twilio
```

### 2. Configure Environment Variables

Add to `.env`:
```env
# Twilio Configuration
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WHATSAPP_NUMBER=+1234567890

# Redis for Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 3. Start Redis
```bash
# Install Redis
sudo apt install redis-server  # Ubuntu/Debian
brew install redis             # macOS

# Start Redis
redis-server
```

### 4. Start Celery Worker
```bash
cd backend
celery -A meditrack worker --loglevel=info
```

### 5. Start Celery Beat (Scheduler)
```bash
cd backend
celery -A meditrack beat --loglevel=info
```

### 6. Configure Twilio Webhook

In Twilio Console:
1. Go to Phone Numbers → Your Number
2. Set webhook URL: `https://yourdomain.com/api/messages/webhook/twilio/`
3. Method: POST
4. For WhatsApp: Configure WhatsApp sandbox webhook

## Message Templates

### Creating Templates

Via Django Admin (`/admin/messaging/messagetemplate/`):

**Example: Daily Check-in for Heart Failure**
```
Name: Heart Failure Daily Check-in
Type: daily_checkin
Condition: heart_failure
Content:
Good morning {first_name}! 

How are you feeling today? Please rate the following symptoms on a scale of 1-10 (1=none, 10=severe):

1. Shortness of breath?
2. Swelling in legs or ankles?
3. Fatigue or weakness?

Reply with three numbers separated by spaces (e.g., 3 5 4)

Questions (JSON):
[
  "Shortness of breath (1-10)?",
  "Swelling in legs (1-10)?",
  "Fatigue level (1-10)?"
]
```

**Example: Reminder**
```
Name: Check-in Reminder
Type: reminder
Condition: all
Content:
Hi {first_name}, this is a friendly reminder to complete your daily health check-in. 

Please reply to the previous message with your symptom ratings.

Your care team is here to help! Contact {provider_name} if you have concerns.
```

### Template Placeholders

Available placeholders:
- `{patient_name}` - Full name
- `{first_name}` - First name only
- `{last_name}` - Last name only
- `{condition}` - Patient's condition (display format)
- `{discharge_date}` - Discharge date (formatted)
- `{provider_name}` - Assigned provider's name

## Risk Assessment Configuration

### Symptom Weights by Condition

Defined in `RiskAssessmentService.SYMPTOM_WEIGHTS`:

**Heart Failure:**
- Chest pain: 3.0 (most critical)
- Shortness of breath: 2.5
- Swelling: 1.8
- Weight gain: 1.8
- Palpitations: 1.5
- Dizziness: 1.3
- Fatigue: 1.2

**COPD:**
- Shortness of breath: 2.5
- Wheezing: 1.8
- Cough severity: 1.8
- Chest tightness: 1.5
- Mucus production: 1.2
- Fatigue: 1.0

**Diabetes:**
- Blood sugar low: 3.0 (most critical)
- Blood sugar high: 2.5
- Medication missed: 2.0
- Blurred vision: 1.8
- Dizziness: 1.5
- Excessive thirst: 1.3
- Frequent urination: 1.2

### Risk Level Thresholds

- **Green (Low Risk)**: Score 0-3.0
  - Patient stable, routine monitoring
- **Yellow (Moderate Risk)**: Score 3.1-6.5
  - Elevated symptoms, provider review recommended
  - Auto-generates yellow alert
- **Red (High Risk)**: Score 6.6-10.0
  - Critical symptoms, immediate provider attention
  - Auto-generates red alert

## API Endpoints

### Manual Message Sending

```bash
POST /api/messages/send/
Content-Type: application/json

{
  "patient_id": 1,
  "content": "Hello! How are you feeling today?",
  "channel": "sms"  // or "whatsapp"
}

Response:
{
  "id": 123,
  "patient": {...},
  "content": "Hello! How are you feeling today?",
  "channel": "sms",
  "status": "sent",
  "twilio_sid": "SM...",
  "sent_at": "2024-02-11T10:30:00Z",
  "twilio_result": {
    "success": true,
    "sid": "SM...",
    "status": "sent"
  }
}
```

### Webhook Endpoint (Twilio Callback)

```bash
POST /api/messages/webhook/twilio/
Content-Type: application/x-www-form-urlencoded

From=+1234567890
Body=4 6 3
MessageSid=SM...

Response:
{
  "status": "received",
  "processed": true
}
```

## Monitoring & Debugging

### Check Celery Tasks Status

```bash
# View scheduled tasks
celery -A meditrack inspect scheduled

# View active tasks
celery -A meditrack inspect active

# View task stats
celery -A meditrack inspect stats
```

### Test Manual Check-in

```python
from apps.checkins.services.scheduler import CheckInScheduler
from apps.patients.models import Patient

scheduler = CheckInScheduler()

# Create check-ins for today
count = scheduler.create_daily_checkins()
print(f"Created {count} check-ins")

# Send pending check-ins
stats = scheduler.send_pending_checkins()
print(f"Sent: {stats['sent']}, Failed: {stats['failed']}")
```

### Test Risk Assessment

```python
from apps.checkins.services.risk_assessment import RiskAssessmentService
from apps.checkins.models import DailyCheckIn

service = RiskAssessmentService()
checkin = DailyCheckIn.objects.get(id=1)

result = service.process_checkin(checkin)
print(f"Score: {result['score']}, Level: {result['risk_level']}")
```

## Production Deployment

### Using Supervisor (Recommended)

Create `/etc/supervisor/conf.d/meditrack.conf`:

```ini
[program:meditrack_celery]
command=/path/to/venv/bin/celery -A meditrack worker --loglevel=info
directory=/path/to/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/meditrack/celery.log

[program:meditrack_beat]
command=/path/to/venv/bin/celery -A meditrack beat --loglevel=info
directory=/path/to/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/meditrack/beat.log
```

Reload supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start meditrack_celery meditrack_beat
```

### Using systemd

Create service files for Celery worker and beat.

## Testing

### Mock Mode (Without Twilio)

If Twilio credentials are not configured, the system runs in **mock mode**:
- Messages are logged but not actually sent
- API returns `"mock": true` in response
- Check-ins still created and tracked
- Perfect for development and testing

### With Twilio Sandbox (WhatsApp)

1. Activate Twilio WhatsApp Sandbox
2. Send "join [your-sandbox-keyword]" to Twilio number
3. Test sending messages to sandbox number
4. Configure sandbox webhook to your development URL (use ngrok for local testing)

## Summary

✅ **Automated messaging is FULLY IMPLEMENTED**
✅ **Two-way communication works** (send & receive)
✅ **Risk assessment is automatic**
✅ **Alerts auto-generate** for elevated risk
✅ **Celery tasks are scheduled**
✅ **Templates support customization**
✅ **Multiple conditions supported** with specific risk weights

The system is production-ready and requires only:
1. Twilio account configuration
2. Redis running
3. Celery worker + beat running
4. Message templates created in admin

**Status: 100% FUNCTIONAL** 🎉
