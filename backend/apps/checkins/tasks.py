import logging
from celery import shared_task
from .scheduler import (
    create_daily_checkins_for_date,
    send_due_checkins,
    send_checkin_reminders,
    mark_missed_checkins,
)

logger = logging.getLogger(__name__)


@shared_task(name='apps.checkins.tasks.create_daily_checkins', bind=True, max_retries=3)
def create_daily_checkins(self):
    try:
        result = create_daily_checkins_for_date()
        logger.info(f'create_daily_checkins task result: {result}')
        return result
    except Exception as exc:
        logger.exception(f'create_daily_checkins task error: {exc}')
        raise self.retry(exc=exc, countdown=60)


@shared_task(name='apps.checkins.tasks.send_due_checkins', bind=True, max_retries=3)
def send_due_checkins_task(self):
    try:
        result = send_due_checkins()
        logger.info(f'send_due_checkins task result: {result}')
        return result
    except Exception as exc:
        logger.exception(f'send_due_checkins task error: {exc}')
        raise self.retry(exc=exc, countdown=30)


@shared_task(name='apps.checkins.tasks.send_checkin_reminders', bind=True, max_retries=3)
def send_checkin_reminders_task(self):
    try:
        result = send_checkin_reminders()
        logger.info(f'send_checkin_reminders task result: {result}')
        return result
    except Exception as exc:
        logger.exception(f'send_checkin_reminders task error: {exc}')
        raise self.retry(exc=exc, countdown=60)


@shared_task(name='apps.checkins.tasks.mark_missed_checkins', bind=True, max_retries=3)
def mark_missed_checkins_task(self):
    try:
        result = mark_missed_checkins()
        logger.info(f'mark_missed_checkins task result: {result}')
        return result
    except Exception as exc:
        logger.exception(f'mark_missed_checkins task error: {exc}')
        raise self.retry(exc=exc, countdown=60)
