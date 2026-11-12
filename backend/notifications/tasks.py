import logging

from celery import shared_task
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)
def send_assignment_email(self, event_id: str) -> None:
    """Send the "task assigned" email for one TaskAssignmentEvent.

    Idempotency [CELERY-08/09/10]: the event row is locked with
    `select_for_update` and its `notified` flag is the single source of
    truth. A retried delivery of the SAME event_id finds `notified=True`
    and no-ops; a genuinely NEW event (new UUID, e.g. a later reassignment)
    is a different row and is always eligible to send.
    """
    # Imported lazily to avoid a notifications -> tasks -> notifications
    # import cycle at module load time.
    from tasks.models import TaskAssignmentEvent

    with transaction.atomic():
        try:
            event = TaskAssignmentEvent.objects.select_for_update().get(id=event_id)
        except TaskAssignmentEvent.DoesNotExist:
            logger.error("assignment_event_not_found", extra={"event_id": event_id})
            return

        if event.notified:
            logger.info("assignment_notification_duplicate_suppressed", extra={"event_id": event_id})
            return

        send_mail(
            subject=f"Task assigned: {event.task.title}",
            message=(
                f"You have been assigned to the task '{event.task.title}' "
                f"by {event.assigned_by.username}."
            ),
            from_email="noreply@taskhub.local",
            recipient_list=[event.assigned_to.email or event.assigned_to.username],
            fail_silently=False,
        )

        event.notified = True
        event.notified_at = timezone.now()
        event.save(update_fields=["notified", "notified_at"])

        logger.info(
            "assignment_notification_sent",
            extra={"event_id": event_id, "task_id": event.task_id, "assigned_to": event.assigned_to_id},
        )
