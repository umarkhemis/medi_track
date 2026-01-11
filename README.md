# MediTrack: Post-Discharge Patient Monitoring Platform

A comprehensive web-based platform for monitoring patients after hospital discharge, reducing 30-day readmissions through automated daily check-ins, symptom tracking, risk-based alerts, and two-way communication between patients and healthcare providers.

## Tech Stack

### Backend
- **Framework**: Django 5.x with Django REST Framework
- **Language**: Python 3.12
- **Database**: PostgreSQL (production) / SQLite (development)
- **Authentication**: JWT (djangorestframework-simplejwt)
- **API Documentation**: drf-spectacular (Swagger/OpenAPI)
- **Task Queue**: Celery with Redis
- **Messaging**: Twilio SMS and WhatsApp API

### Frontend
- **Framework**: React.js 18
- **Node Version**: v24.11.1
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **State Management**: React Context API & TanStack Query

## Features

### Phase 1: Core Infrastructure ✅
- Custom user authentication with role-based access (Patient, Provider, Admin)
- JWT token-based authentication
- Split settings for development and production environments
- API documentation with Swagger UI and ReDoc
- Modular app structure

### Phase 2: Patient & Provider Management ✅
- Patient profile management with medical history
- Healthcare provider profiles with patient assignment
- Provider dashboard with key metrics
- Risk level tracking (green/yellow/red)
- Patient filtering and search capabilities

### Phase 3: Monitoring & Communication ✅
- Daily check-in system with automated scheduling
- SMS and WhatsApp integration via Twilio
- Risk assessment engine with automatic alert generation
- Alert management with acknowledgment and resolution workflows
- Message templates for different conditions
- Webhook support for incoming messages

## Project Structure

```
meditrack/
├── backend/                    # Django backend
│   ├── apps/
│   │   ├── users/             # User authentication & management
│   │   ├── patients/          # Patient profiles & management
│   │   ├── providers/         # Healthcare provider management
│   │   ├── checkins/          # Daily check-in system
│   │   ├── alerts/            # Alert management
│   │   ├── messaging/         # Twilio SMS/WhatsApp integration
│   │   └── analytics/         # Reporting & analytics
│   ├── meditrack/
│   │   ├── settings/          # Split settings (base, dev, prod)
│   │   └── urls.py
│   ├── manage.py
│   └── requirements.txt
├── frontend/                   # React frontend (to be implemented)
├── .env.example               # Environment variables template
├── .gitignore
└── README.md
```

## Setup Instructions

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd medi_track
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp ../.env.example .env
   # Edit .env with your configuration
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

The API will be available at `http://localhost:8000/`

### API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/api/docs/`
- **ReDoc**: `http://localhost:8000/api/redoc/`
- **Admin Panel**: `http://localhost:8000/admin/`

## API Endpoints

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login and get JWT tokens
- `POST /api/auth/token/refresh/` - Refresh access token
- `GET /api/auth/profile/` - Get current user profile
- `PUT /api/auth/profile/` - Update user profile

### Patients
- `GET /api/patients/` - List all patients
- `POST /api/patients/` - Create new patient
- `GET /api/patients/{id}/` - Get patient details
- `PUT /api/patients/{id}/` - Update patient
- `GET /api/patients/high-risk/` - Get high-risk patients
- `GET /api/patients/pending-response/` - Get patients with pending check-ins
- `GET /api/patients/{id}/checkins/` - Get patient's check-in history
- `GET /api/patients/{id}/alerts/` - Get patient's alerts
- `GET /api/patients/{id}/messages/` - Get patient's messages

### Providers
- `GET /api/providers/` - List all providers
- `GET /api/providers/{id}/` - Get provider details
- `GET /api/providers/{id}/patients/` - Get provider's patients
- `GET /api/providers/{id}/dashboard/` - Get dashboard metrics
- `PUT /api/providers/{id}/availability/` - Update availability

### Check-ins
- `GET /api/checkins/` - List check-ins
- `GET /api/checkins/today/` - Get today's check-ins
- `GET /api/checkins/{id}/` - Get check-in details
- `POST /api/checkins/{id}/send/` - Manually send check-in
- `GET /api/checkins/{id}/responses/` - Get check-in responses
- `POST /api/checkins/schedule/` - Schedule check-ins

### Alerts
- `GET /api/alerts/` - List all alerts
- `GET /api/alerts/active/` - Get active alerts
- `GET /api/alerts/{id}/` - Get alert details
- `POST /api/alerts/{id}/acknowledge/` - Acknowledge alert
- `POST /api/alerts/{id}/resolve/` - Resolve alert

### Messages
- `GET /api/messages/` - List messages
- `POST /api/messages/send/` - Send message to patient
- `GET /api/messages/templates/` - List message templates
- `POST /api/messages/webhook/twilio/` - Twilio webhook endpoint

## Environment Variables

Key environment variables (see `.env.example` for full list):

```bash
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
USE_SQLITE=True  # Set to False for PostgreSQL
DB_NAME=meditrack
DB_USER=meditrack_user
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Twilio
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WHATSAPP_NUMBER=+1234567890

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
```

## Database Models

### User
Custom user model with roles (patient, provider, admin)

### Patient
- Personal and medical information
- Discharge details
- Assigned provider
- Risk level tracking
- Emergency contact information

### Provider
- Healthcare provider profiles
- Department and specialization
- Patient capacity management
- Availability status

### DailyCheckIn
- Scheduled patient check-ins
- Status tracking (scheduled, sent, completed, missed)
- Risk score calculation
- Response collection

### Alert
- Risk-based alerts (yellow/red)
- Acknowledgment and resolution tracking
- Provider assignment
- Action documentation

### Message
- SMS and WhatsApp messages
- Direction (inbound/outbound)
- Status tracking
- Twilio integration

### MessageTemplate
- Reusable message templates
- Condition-specific content
- Check-in question sets

## Development

### Running Tests
```bash
cd backend
python manage.py test
```

### Code Style
```bash
# Format code with black
black .

# Check with flake8
flake8 .

# Sort imports
isort .
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Support

For support, email support@meditrack.com or open an issue in the repository.

## Roadmap

- [ ] React frontend implementation
- [ ] Real-time dashboard updates with WebSockets
- [ ] Mobile app for patients (React Native)
- [ ] Advanced analytics and reporting
- [ ] Integration with EHR systems
- [ ] Telemedicine video consultation
- [ ] Multi-language support
- [ ] HIPAA compliance audit trail
