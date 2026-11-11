from django import forms

from apps.accounts.models import Role


class InvitationForm(forms.Form):
    username = forms.CharField(label="Usuário convidado", max_length=150, help_text="A pessoa deve criar seu próprio cadastro antes de receber o convite.")
    role = forms.ChoiceField(label="Papel", choices=Role.choices, initial=Role.OPERATOR)


class RoleForm(forms.Form):
    role = forms.ChoiceField(label="Papel", choices=Role.choices)


class OrganizationForm(forms.Form):
    name = forms.CharField(label="Nome da organização", max_length=100)
