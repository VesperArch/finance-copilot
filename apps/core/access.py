from django.core.exceptions import PermissionDenied

from apps.accounts.models import Membership, Role


SESSION_SPACE_KEY = "financial_space_id"


def current_membership(user, space_id=None):
    if not user.is_authenticated or not user.is_active:
        raise PermissionDenied("Autenticação necessária.")
    memberships = Membership.objects.filter(user=user).select_related("financial_space")
    membership = memberships.filter(financial_space_id=space_id).first() if space_id is not None else memberships.first()
    if membership is None:
        raise PermissionDenied("Sem associação a esta organização. Solicite um convite ao administrador.")
    return membership


def request_membership(request):
    if not hasattr(request, "space_membership"):
        request.space_membership = current_membership(request.user, request.session.get(SESSION_SPACE_KEY))
    return request.space_membership


def personal_space(user):
    """Compatibility for non-request callers; HTTP handlers use request_space."""
    return current_membership(user).financial_space


def request_space(request):
    return request_membership(request).financial_space


def require_admin(user, space):
    membership = current_membership(user, space.pk)
    if membership.role != Role.ADMIN:
        raise PermissionDenied("Apenas administradores da organização podem executar esta operação.")
    return membership
