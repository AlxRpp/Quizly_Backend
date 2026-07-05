from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """Check the request user is really the owner of the object, not just
    logged in. Used together with IsAuthenticated so nobody can edit or
    delete quizzes that arent theirs."""

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
