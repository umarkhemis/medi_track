# MediTrack Backend v2

A provider-led, automated post-discharge patient monitoring platform.

## Architecture

**Core rule:** Providers and admins authenticate. Patients are provider-managed records. Africa's Talking handles all SMS.

### Stack
- **Framework:** Django 5.x + Django REST Framework
- **Auth:** JWT (djangorestframework-simplejwt)
- **SMS:** Africa's Talking
- **Task Queue:** Celery + Redis + django-celery-beat
- **Database:** SQLite (dev) / PostgreSQL (prod)
- **Docs:** drf-spectacular (Swagger + ReDoc)

### App Structure
```
backend/
├── meditrack/              # Project config, settings, celery
│   └── settings/
│       ├── base.py
│       ├── dev.py
│       └── prod.py
├── apps/
│   ├── users/              # Auth: provider + admin only
│   ├── providers/          # Provider profiles & dashboard
│   ├── patients/           # Patient records (no auth needed)
│   ├── checkins/           # Daily check-in lifecycle + scheduler
│   ├── alerts/             # Risk engine + alert management
│   ├── messaging/          # Africa's Talking SMS + inbound processing
│   └── analytics/          # Summary reporting
└── tests/                  # Test suite (20 tests, all green)
```

---

## Setup

### 1. Clone & virtual environment
```bash
git clone <repo-url>
cd medi_track/backend
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp ../.env.example .env
# Edit .env with your Africa's Talking credentials and other settings
```

### 4. Run migrations
```bash
python manage.py migrate
```

### 5. Create superuser
```bash
python manage.py createsuperuser
```

### 6. Start the server
```bash
python manage.py runserver
```

### 7. Start Celery (in a separate terminal)
```bash
celery -A meditrack worker -l info
celery -A meditrack beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

## API Docs

Once running:
- **Swagger UI:** http://localhost:8000/api/docs/
- **ReDoc:** http://localhost:8000/api/redoc/
- **Admin:** http://localhost:8000/admin/

---

## API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register provider or admin |
| POST | `/api/auth/login/` | Login → JWT tokens |
| POST | `/api/auth/token/refresh/` | Refresh access token |
| GET/PUT | `/api/auth/profile/` | Get or update own profile |

### Patients
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/patients/` | List patients (filtered by provider) |
| POST | `/api/patients/` | Create patient (no auth account needed) |
| GET | `/api/patients/{id}/` | Patient detail |
| PUT/PATCH | `/api/patients/{id}/` | Update patient |
| GET | `/api/patients/high_risk/` | Red-risk patients |
| POST | `/api/patients/{id}/pause_monitoring/` | Pause monitoring |
| POST | `/api/patients/{id}/resume_monitoring/` | Resume monitoring |
| POST | `/api/patients/{id}/opt_out/` | Opt patient out of SMS |
| POST | `/api/patients/{id}/mark_unreachable/` | Mark unreachable |
| POST | `/api/patients/{id}/enroll/` | Enroll in follow-up program |
| GET | `/api/patients/{id}/checkins/` | Patient check-in history |
| GET | `/api/patients/{id}/alerts/` | Patient alerts |
| GET | `/api/patients/{id}/messages/` | Patient messages |

### Providers
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/providers/` | List providers |
| GET | `/api/providers/{id}/dashboard/` | Provider dashboard metrics |
| GET | `/api/providers/{id}/patients/` | Provider's patients |
| PATCH | `/api/providers/{id}/availability/` | Update availability |

### Check-ins
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/checkins/` | List check-ins |
| GET | `/api/checkins/today/` | Today's check-ins |
| GET | `/api/checkins/{id}/` | Check-in detail |
| POST | `/api/checkins/{id}/send/` | Manually send check-in |
| GET | `/api/checkins/{id}/responses/` | Check-in responses |
| POST | `/api/checkins/schedule/` | Trigger scheduling for a date |

### Alerts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/alerts/` | List alerts |
| GET | `/api/alerts/active/` | Open alerts only |
| GET | `/api/alerts/{id}/` | Alert detail |
| POST | `/api/alerts/{id}/acknowledge/` | Acknowledge alert |
| POST | `/api/alerts/{id}/resolve/` | Resolve alert |
| GET | `/api/alerts/escalations/` | Escalation tasks |
| POST | `/api/alerts/escalations/{id}/complete/` | Complete escalation |

### Messages
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/messages/` | Message history |
| POST | `/api/messages/send/` | Send manual SMS to patient |
| GET | `/api/messages/templates/` | Message templates |
| GET/POST | `/api/messages/programs/` | Follow-up programs |
| GET | `/api/messages/enrollments/` | Program enrollments |
| POST | `/api/messages/webhook/africastalking/` | Inbound SMS webhook |
| POST | `/api/messages/webhook/africastalking/delivery/` | Delivery report webhook |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/summary/` | Platform summary metrics |

---

## Operational Flow

```
1. Provider registers → Provider profile auto-created
2. Provider creates patient (phone number stored + normalized to E.164)
3. Patient enrolled in a follow-up program
4. Celery beat creates daily check-ins at midnight
5. Celery beat sends SMS at patient's preferred_check_in_time via Africa's Talking
6. Patient replies by SMS → inbound webhook fires
7. Backend finds patient by phone_number_e164 (not User)
8. Reply parsed → CheckInResponse rows stored
9. Risk engine evaluates: green / yellow / red
10. Yellow → Alert created; Red → Alert + EscalationTask
11. Provider sees alerts on dashboard
12. Patient can reply STOP to opt out at any time
```

---

## Risk Engine Rules

| Condition | Trigger | Risk Level |
|-----------|---------|------------|
| Heart Failure | chest_pain = yes | 🔴 RED |
| Heart Failure | shortness_of_breath + leg_swelling = yes | 🟡 YELLOW |
| COPD | breathlessness + rescue_inhaler_use = yes | 🔴 RED |
| Any | any positive symptom | 🟡 YELLOW |
| Any | no symptoms | 🟢 GREEN |

Red alerts automatically generate an EscalationTask with a 1-hour due time.

---

## Celery Beat Schedule

| Task | Schedule | Description |
|------|----------|-------------|
| `create_daily_checkins` | 00:05 daily | Creates one check-in per active patient |
| `send_due_checkins` | Every 15 min | Sends scheduled check-ins via SMS |
| `send_checkin_reminders` | Every 30 min | Reminds non-responders after 4 hours |
| `mark_missed_checkins` | 23:30 daily | Marks expired unanswered check-ins |

---

## Africa's Talking Environment Variables

```env
AT_USERNAME=sandbox         # 'sandbox' for testing, your username for production
AT_API_KEY=your-api-key
AT_SMS_SENDER_ID=MediTrack  # Optional sender ID
AT_INBOUND_SECRET=secret    # For verifying inbound webhook requests
AT_DELIVERY_SECRET=secret   # For verifying delivery report requests
DEFAULT_COUNTRY_CODE=KE     # Default country for phone normalization
```

---

## Running Tests

```bash
python manage.py test tests --verbosity=2
```

20 tests covering:
- Patient creation without auth account
- Duplicate phone rejection
- Provider data isolation
- Check-in scheduling and deduplication
- Africa's Talking SMS sending (mocked)
- Inbound SMS processing and STOP opt-out
- Idempotent webhook handling
- Risk engine (chest pain, COPD, no symptoms)
- Follow-up program enrollment and deactivation

---

## Production Checklist

- [ ] Set `DJANGO_ENV=prod` in environment
- [ ] Set strong `SECRET_KEY`
- [ ] Set `USE_SQLITE=False` and configure PostgreSQL
- [ ] Set real `AT_USERNAME` and `AT_API_KEY`
- [ ] Configure `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`
- [ ] Run `python manage.py collectstatic`
- [ ] Set up Redis for Celery
- [ ] Configure Africa's Talking webhook URLs:
  - Inbound: `https://yourdomain.com/api/messages/webhook/africastalking/`
  - Delivery: `https://yourdomain.com/api/messages/webhook/africastalking/delivery/`
