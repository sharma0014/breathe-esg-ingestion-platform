from rest_framework.permissions import BasePermission

from .models import Membership, Organization


class IsOrgMember(BasePermission):
    """Checks that request.user is an active member of the org in the URL."""

    def has_permission(self, request, view):
        org_slug = view.kwargs.get('org_slug')
        if not org_slug:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        try:
            org = Organization.objects.get(slug=org_slug)
        except Organization.DoesNotExist:
            return False
        return Membership.objects.filter(org=org, user=request.user, is_active=True).exists()
