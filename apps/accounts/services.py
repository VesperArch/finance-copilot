from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.accounts.models import Membership, MembershipInvitation, Role
from apps.core.access import require_admin
from apps.finance.models import FinancialSpace


@transaction.atomic
def change_member(actor, space, member_id, role=None, remove=False):
    FinancialSpace.objects.select_for_update().get(pk=space.pk)
    require_admin(actor, space)
    member = get_object_or_404(Membership, pk=member_id, financial_space=space)
    if member.user_id == space.owner_id:
        raise ValidationError("O proprietário deve permanecer administrador da organização.")
    if remove:
        member.delete()
    else:
        member.role = role
        member.full_clean()
        member.save(update_fields=["role"])
    return member


@transaction.atomic
def invite_member(actor, space, username, role):
    FinancialSpace.objects.select_for_update().get(pk=space.pk)
    require_admin(actor, space)
    user = get_user_model().objects.filter(username=username, is_active=True).first()
    if user is None or Membership.objects.filter(user=user, financial_space=space).exists():
        raise ValidationError("Informe um usuário cadastrado e ativo que ainda não seja membro.")
    invitation = MembershipInvitation(financial_space=space, user=user, role=role, created_by=actor)
    invitation.full_clean()
    invitation.save()
    return invitation


@transaction.atomic
def accept_invitation(user, invitation_id):
    # Lock space before invitation, consistently with membership management.
    candidate = get_object_or_404(MembershipInvitation, pk=invitation_id, user=user)
    FinancialSpace.objects.select_for_update().get(pk=candidate.financial_space_id)
    invitation = get_object_or_404(MembershipInvitation.objects.select_for_update(), pk=candidate.pk, user=user)
    if invitation.accepted_at or invitation.expires_at <= timezone.now():
        raise ValidationError("Convite utilizado ou expirado.")
    if not Membership.objects.filter(user=invitation.created_by, financial_space=invitation.financial_space, role=Role.ADMIN).exists():
        raise PermissionDenied("O emissor deste convite não é mais administrador.")
    if Membership.objects.filter(user=user, financial_space=invitation.financial_space).exists():
        raise ValidationError("Você já é membro desta organização.")
    member = Membership.objects.create(user=user, financial_space=invitation.financial_space, role=invitation.role)
    invitation.accepted_at = timezone.now()
    invitation.save(update_fields=["accepted_at"])
    return member


@transaction.atomic
def rename_space(actor, space, name):
    locked = FinancialSpace.objects.select_for_update().get(pk=space.pk)
    require_admin(actor, locked)
    locked.name = name
    locked.full_clean()
    locked.save(update_fields=["name"])
    return locked


@transaction.atomic
def revoke_invitation(actor, space, invitation_id):
    FinancialSpace.objects.select_for_update().get(pk=space.pk)
    require_admin(actor, space)
    invitation = get_object_or_404(MembershipInvitation, pk=invitation_id, financial_space=space)
    invitation.delete()
