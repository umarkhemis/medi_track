"""
Celery tasks for automated check-in scheduling and sending.
"""

from celery import shared_task
from django.utils import timezone
from apps.checkins.services.scheduler import CheckInScheduler


@shared_task(name='apps.checkins.tasks.schedule_daily_checkins')
def schedule_daily_checkins():
    """
    Create daily check-in records for all active patients.
    Runs at midnight every day via Celery Beat.
    
    Returns:
        dict: Statistics about created check-ins
    """
    scheduler = CheckInScheduler()
    today = timezone.now().date()
    
    count = scheduler.create_daily_checkins(date=today)
    
    return {
        'status': 'success',
        'date': str(today),
        'created_count': count,
        'timestamp': timezone.now().isoformat()
    }


@shared_task(name='apps.checkins.tasks.send_scheduled_checkins')
def send_scheduled_checkins():
    """
    Send check-in messages for pending check-ins whose time has arrived.
    Runs every 5 minutes via Celery Beat.
    
    Returns:
        dict: Statistics about sent check-ins
    """
    scheduler = CheckInScheduler()
    stats = scheduler.send_pending_checkins()
    
    return {
        'status': 'success',
        **stats,
        'timestamp': timezone.now().isoformat()
    }


@shared_task(name='apps.checkins.tasks.send_reminders')
def send_reminders():
    """
    Send reminder messages to patients who haven't responded.
    Runs every 30 minutes via Celery Beat.
    
    Returns:
        dict: Statistics about sent reminders
    """
    scheduler = CheckInScheduler()
    stats = scheduler.send_reminders()
    
    return {
        'status': 'success',
        **stats,
        'timestamp': timezone.now().isoformat()
    }


@shared_task(name='apps.checkins.tasks.mark_missed_checkins')
def mark_missed_checkins():
    """
    Mark check-ins as missed if not completed by end of day.
    Runs at 11 PM daily via Celery Beat.
    
    Returns:
        dict: Statistics about marked check-ins
    """
    scheduler = CheckInScheduler()
    count = scheduler.mark_missed_checkins()
    
    return {
        'status': 'success',
        'marked_count': count,
        'timestamp': timezone.now().isoformat()
    }
