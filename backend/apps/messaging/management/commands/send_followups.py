from django.core.management.base import BaseCommand

from apps.messaging.services.followup_service import FollowUpSchedulerService


class Command(BaseCommand):
    help = 'Send automated follow-up messages that are due.'

    def handle(self, *args, **options):
        stats = FollowUpSchedulerService().send_due_followups()
        self.stdout.write(
            self.style.SUCCESS(
                (
                    f"Follow-ups processed. Attempted: {stats['attempted']}, "
                    f"sent: {stats['sent']}, failed: {stats['failed']}, skipped: {stats['skipped']}"
                )
            )
        )
