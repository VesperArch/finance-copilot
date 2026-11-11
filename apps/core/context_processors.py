from apps.accounts.models import Membership
from apps.core.access import SESSION_SPACE_KEY


def organization(request):
    if not request.user.is_authenticated:
        return {}
    memberships = list(Membership.objects.filter(user=request.user).select_related("financial_space"))
    selected = request.session.get(SESSION_SPACE_KEY)
    current = next((m for m in memberships if m.financial_space_id == selected), None) if selected is not None else next(iter(memberships), None)
    return {"space_memberships": memberships, "current_membership": current}
