from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrAssigneeOrReadOnly(BasePermission):
    """Admins full access. Assignee can update their task. Others read-only."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, 'is_admin', False):
            return True
        if request.method in SAFE_METHODS:
            return True
        return getattr(obj, 'assigned_to_id', None) == getattr(user, 'id', None)


