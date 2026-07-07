from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """Object-level check: the request user must be the object's owner.
    Combine with IsAuthenticated so anonymous requests are rejected first.
    """

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
