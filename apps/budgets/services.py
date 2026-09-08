from decimal import Decimal

from django.db.models import Sum

from apps.budgets.models import Budget
from apps.finance.models import Transaction


ZERO = Decimal("0.00")


def budget_progress(space, year, month):
    spending = dict(Transaction.objects.filter(
        financial_space=space, type=Transaction.Type.EXPENSE,
        date__year=year, date__month=month,
    ).values("category_id").annotate(total=Sum("amount")).values_list("category_id", "total"))
    rows = []
    for budget in Budget.objects.filter(financial_space=space, year=year, month=month).select_related("category"):
        used = spending.get(budget.category_id, ZERO)
        percentage = used * 100 / budget.limit_amount
        status = "Dentro do planejado"
        if percentage >= 100:
            status = "Limite atingido" if percentage == 100 else "Acima do limite"
        elif percentage >= 90:
            status = "Atenção: 90% ou mais utilizado"
        elif percentage >= min(75, budget.alert_threshold):
            status = "Perto do limite"
        rows.append({
            "budget": budget, "used": used, "remaining": budget.limit_amount - used,
            "percentage": percentage, "bar": min(percentage, Decimal("100")),
            "status": status, "warning": percentage >= min(75, budget.alert_threshold),
        })
    return rows
