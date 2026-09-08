from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.budgets.forms import BudgetForm
from apps.budgets.models import Budget
from apps.budgets.services import budget_progress
from apps.core.access import personal_space
from apps.core.forms import MonthForm
from apps.finance.forms import AccountForm, CategoryForm, TransactionForm
from apps.finance.models import Account, Category, InstallmentGroup, Transaction
from apps.finance.services.installments import save_transaction
from apps.finance.services.summary import account_balances, dashboard_summary


RESOURCES = {
    "account": (Account, AccountForm, "Contas", "conta"),
    "category": (Category, CategoryForm, "Categorias", "categoria"),
    "transaction": (Transaction, TransactionForm, "Movimentações", "movimentação"),
    "budget": (Budget, BudgetForm, "Planejamento", "orçamento"),
}


def selected_month(request):
    today = timezone.localdate()
    form = MonthForm(request.GET if "month" in request.GET else None, initial={"month": today})
    value = form.cleaned_data["month"] if form.is_bound and form.is_valid() else today
    return form, value


@login_required
def dashboard(request):
    space = personal_space(request.user)
    month_form, month = selected_month(request)
    context = dashboard_summary(space, month.year, month.month)
    context.update({"month_form": month_form, "has_accounts": Account.objects.filter(financial_space=space, active=True).exists()})
    return render(request, "finance/dashboard.html", context)


@login_required
def resource_list(request, kind):
    model, _, title, singular = RESOURCES[kind]
    space = personal_space(request.user)
    queryset = model.objects.filter(financial_space=space)
    context = {"kind": kind, "title": title, "singular": singular}
    if kind == "account":
        context["objects"] = account_balances(space)
    elif kind == "transaction":
        month_form, month = selected_month(request)
        queryset = queryset.filter(date__year=month.year, date__month=month.month).select_related("account", "category", "installment__group")
        context.update({"month_form": month_form, "month_value": month.strftime("%Y-%m")})
    elif kind == "budget":
        month_form, month = selected_month(request)
        context.update({"month_form": month_form, "budget_rows": budget_progress(space, month.year, month.month)})
    if kind not in ("account", "budget"):
        context["page_obj"] = Paginator(queryset, 25).get_page(request.GET.get("page"))
        context["objects"] = context["page_obj"]
    return render(request, "finance/list.html", context)


@login_required
def resource_edit(request, kind, pk=None):
    model, form_class, _, singular = RESOURCES[kind]
    space = personal_space(request.user)
    instance = get_object_or_404(model, pk=pk, financial_space=space) if pk else None
    if kind == "transaction" and instance and instance.installment_group_id:
        messages.info(request, "As parcelas mantêm os valores da compra original. Para corrigir, exclua a compra e cadastre novamente.")
        return redirect("installment-detail", pk=instance.installment_group_id)
    kwargs = {"space": space, "instance": instance}
    if kind == "transaction":
        kwargs["user"] = request.user
    form = form_class(request.POST if request.method == "POST" else None, **kwargs)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                if kind == "transaction":
                    entry = save_transaction(form.save(commit=False), form.cleaned_data["installments"])
                else:
                    form.save()
        except ValidationError as error:
            form.add_error(None, error.messages)
        except IntegrityError:
            form.add_error(None, "Já existe um registro com estes dados. Revise o nome ou o mês informado.")
        else:
            messages.success(request, "Alterações salvas." if pk else "Registro adicionado com sucesso.")
            if kind == "transaction" and entry.installment_group_id:
                return redirect("installment-detail", pk=entry.installment_group_id)
            return redirect(f"{kind}-list")
    return render(request, "finance/form.html", {"form": form, "title": f"{'Editar' if pk else 'Adicionar'} {singular}", "kind": kind})


@login_required
def resource_delete(request, kind, pk):
    model, _, _, singular = RESOURCES[kind]
    obj = get_object_or_404(model, pk=pk, financial_space=personal_space(request.user))
    if kind == "transaction" and obj.installment_group_id:
        return redirect("installment-detail", pk=obj.installment_group_id)
    if request.method == "POST":
        try:
            obj.delete()
        except ProtectedError:
            messages.error(request, "Este registro está em uso. Você pode desativá-lo para preservar seu histórico.")
        else:
            messages.success(request, "Registro excluído.")
        return redirect(f"{kind}-list")
    return render(request, "finance/delete.html", {"object": obj, "kind": kind, "title": f"Excluir {singular}"})


@login_required
def installment_detail(request, pk):
    group = get_object_or_404(InstallmentGroup, pk=pk, financial_space=personal_space(request.user))
    return render(request, "finance/installments.html", {"group": group, "payments": group.installments.select_related("transaction", "transaction__account")})


@login_required
def installment_delete(request, pk):
    group = get_object_or_404(InstallmentGroup, pk=pk, financial_space=personal_space(request.user))
    if request.method == "POST":
        with transaction.atomic():
            group.delete()
        messages.success(request, "Compra e todas as parcelas excluídas.")
        return redirect("transaction-list")
    return render(request, "finance/delete.html", {"object": group, "kind": "transaction", "title": "Excluir compra parcelada", "installment_group": True})
