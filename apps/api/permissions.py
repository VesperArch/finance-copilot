from rest_framework.permissions import BasePermission

from apps.core.access import request_membership, require_admin


class OrganizationMember(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        request_membership(request)
        return True


class OrganizationAdmin(OrganizationMember):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        require_admin(request.user, request_membership(request).financial_space)
        return True
