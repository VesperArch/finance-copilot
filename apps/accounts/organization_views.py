from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.accounts.models import Membership, MembershipInvitation
from apps.accounts.organization_forms import InvitationForm, OrganizationForm, RoleForm
from apps.accounts.services import accept_invitation, change_member, invite_member, rename_space
from apps.core.access import SESSION_SPACE_KEY, current_membership, request_space, require_admin


@login_required
@require_POST
def switch_space(request, pk):
    current_membership(request.user, pk)
    request.session[SESSION_SPACE_KEY] = pk
    return redirect("dashboard")


@login_required
def organization(request):
    space = request_space(request)
    require_admin(request.user, space)
    settings_form = OrganizationForm(initial={"name": space.name})
    invite_form = InvitationForm()
    invitation_url = None
    if request.method == "POST":
        if request.POST.get("action") == "rename":
            settings_form = OrganizationForm(request.POST)
            if settings_form.is_valid():
                rename_space(request.user, space, settings_form.cleaned_data["name"])
                messages.success(request, "Organização atualizada.")
                return redirect("organization")
        else:
            invite_form = InvitationForm(request.POST)
            if invite_form.is_valid():
                try:
                    invitation = invite_member(request.user, space, **invite_form.cleaned_data)
                except ValidationError as error:
                    invite_form.add_error(None, error.messages)
                else:
                    invitation_url = reverse("invitation-accept", args=[invitation.pk])
                    messages.success(request, "Convite criado. Compartilhe o link com a pessoa convidada; ele expira em 7 dias.")
    return render(request, "accounts/organization.html", {
        "space": space, "members": space.memberships.select_related("user"),
        "settings_form": settings_form, "invite_form": invite_form, "invitation_url": invitation_url,
    })


@login_required
def member_edit(request, pk):
    space = request_space(request)
    require_admin(request.user, space)
    member = get_object_or_404(Membership, pk=pk, financial_space=space)
    form = RoleForm(request.POST if request.method == "POST" else None, initial={"role": member.role})
    if request.method == "POST" and form.is_valid():
        try:
            change_member(request.user, space, pk, role=form.cleaned_data["role"], remove=request.POST.get("action") == "remove")
        except ValidationError as error:
            form.add_error(None, error.messages)
        else:
            messages.success(request, "Membro atualizado.")
            return redirect("organization")
    return render(request, "accounts/member.html", {"member": member, "form": form})


@login_required
def invitation_accept(request, token):
    invitation = get_object_or_404(MembershipInvitation.objects.select_related("financial_space"), pk=token, user=request.user)
    error = None
    if request.method == "POST":
        try:
            member = accept_invitation(request.user, token)
        except ValidationError as exc:
            error = " ".join(exc.messages)
        else:
            request.session[SESSION_SPACE_KEY] = member.financial_space_id
            return redirect("dashboard")
    return render(request, "accounts/invitation.html", {"invitation": invitation, "error": error})
