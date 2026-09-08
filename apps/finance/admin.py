from django.contrib import admin

from apps.finance.models import Account, Category, FinancialSpace, InstallmentGroup, Parcela, Transaction


class SuperuserAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(FinancialSpace)
class FinancialSpaceAdmin(SuperuserAdmin):
    list_display = ["name", "owner", "currency"]
    search_fields = ["name", "owner__username"]


@admin.register(Account)
class AccountAdmin(SuperuserAdmin):
    list_display = ["name", "financial_space", "type", "active"]
    list_filter = ["active", "type"]


@admin.register(Category)
class CategoryAdmin(SuperuserAdmin):
    list_display = ["name", "financial_space", "type", "active"]
    list_filter = ["type", "active"]


class FinancialHistoryAdmin(SuperuserAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Transaction)
class TransactionAdmin(FinancialHistoryAdmin):
    list_display = ["description", "financial_space", "type", "amount", "date"]
    list_filter = ["type", "date"]
    list_select_related = ["financial_space"]


@admin.register(InstallmentGroup)
class InstallmentGroupAdmin(FinancialHistoryAdmin):
    list_display = ["description", "total_amount", "count", "first_date"]


@admin.register(Parcela)
class ParcelaAdmin(FinancialHistoryAdmin):
    list_display = ["group", "number", "transaction"]
    list_select_related = ["group", "transaction"]


admin.site.site_header = "Finance Copilot · Administração"
admin.site.site_title = "Finance Copilot"
