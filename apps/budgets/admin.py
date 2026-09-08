from django.contrib import admin

from apps.budgets.models import Budget
from apps.finance.admin import SuperuserAdmin


@admin.register(Budget)
class BudgetAdmin(SuperuserAdmin):
    list_display = ["category", "financial_space", "month", "year", "limit_amount"]
    list_filter = ["year", "month"]
    list_select_related = ["category", "financial_space"]
