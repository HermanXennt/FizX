from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwner(BasePermission):
    """Object-level permission: only the resource's owner can read or write it.

    Looks for an `owner_field` attribute on the view (defaults to "user") to
    know which attribute on the object points back to the requesting user.
    """

    def has_object_permission(self, request, view, obj):
        owner_field = getattr(view, "owner_field", "user")
        return getattr(obj, owner_field, None) == request.user


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        owner_field = getattr(view, "owner_field", "user")
        return getattr(obj, owner_field, None) == request.user
