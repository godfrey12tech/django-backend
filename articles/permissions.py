from rest_framework import permissions

class IsSuperAdmin(permissions.BasePermission):
    """
    Custom permission to allow only superusers to modify objects.
    Read-only requests are allowed for all users.
    """

    def has_permission(self, request, view):
        # Allow safe methods (GET, HEAD, OPTIONS) for all users.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Only allow if the user is authenticated and is a superuser.
        return request.user and (request.user.is_superuser or request.user.is_staff)
