from rest_framework.permissions import BasePermission


class IsProviderOrAdmin(BasePermission):
    """Only providers and admins can access."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['provider', 'admin']


class CanAccessPatient(BasePermission):
    """
    Providers can only access their own patients.
    Admins can access all patients.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        if request.user.role == 'provider':
            try:
                return obj.assigned_provider == request.user.provider_profile
            except Exception:
                return False
        return False
