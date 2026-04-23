from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User


@receiver(post_save, sender=User)
def create_provider_profile(sender, instance, created, **kwargs):
    """Auto-create a Provider profile when a provider user is registered."""
    if created and instance.role == User.Role.PROVIDER:
        from apps.providers.models import Provider
        Provider.objects.get_or_create(user=instance)
