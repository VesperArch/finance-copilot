from django.contrib import admin

from apps.accounts.models import Membership, MembershipInvitation
from apps.finance.admin import FinancialHistoryAdmin


@admin.register(Membership)
class MembershipAdmin(FinancialHistoryAdmin):
    list_display = ["user", "financial_space", "role"]
    list_select_related = ["user", "financial_space"]


@admin.register(MembershipInvitation)
class MembershipInvitationAdmin(FinancialHistoryAdmin):
    list_display = ["user", "financial_space", "role", "expires_at", "accepted_at"]
    list_select_related = ["user", "financial_space"]
