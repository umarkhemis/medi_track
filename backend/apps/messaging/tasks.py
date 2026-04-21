from celery import shared_task
from django.utils import timezone

from apps.messaging.services.followup_service import FollowUpSchedulerService


@shared_task(name='apps.messaging.tasks.send_followups')
def send_followups():
    """Send automated follow-up messages that are due."""
    stats = FollowUpSchedulerService().send_due_followups()
    return {
        'status': 'success',
        **stats,
        'timestamp': timezone.now().isoformat(),
    }
