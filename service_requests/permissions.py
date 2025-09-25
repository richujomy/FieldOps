from rest_framework.permissions import BasePermission


class IsOwnerOrAdmin(BasePermission):
    """Allow edits only by the request owner (customer) or admin users."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, "is_admin", False):
            return True
        return getattr(obj, 'customer_id', None) == getattr(user, 'id', None)


