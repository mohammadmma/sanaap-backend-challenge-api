from rest_framework.permissions import BasePermission


def get_user_role(user):
    """Returns the user's primary group name."""
    return user.groups.values_list('name', flat=True).first()


class IsAdmin(BasePermission):
    """Full access."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and get_user_role(request.user) == 'admin'


class IsEditor(BasePermission):
    """Can create and update, not delete."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        role = get_user_role(request.user)
        return role in ('admin', 'editor')


class IsViewer(BasePermission):
    """Read only."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        role = get_user_role(request.user)
        return role in ('admin', 'editor', 'viewer')