from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.db.models import Q, Sum
from django.utils import timezone

from apps.budgets.services import budget_progress
from apps.finance.models import Account, Transaction


ZERO = Decimal("0.00")


def account_balances(space):
    today = timezone.localdate()
    accounts = list(Account.objects.filter(financial_space=space))
    outgoing = {}
    for row in Transaction.objects.filter(financial_space=space, date__lte=today).values("account_id", "type").annotate(total=Sum("amount")):
        key = row["account_id"]
        sign = 1 if row["type"] == Transaction.Type.INCOME else -1
        outgoing[key] = outgoing.get(key, ZERO) + sign * row["total"]
    incoming = dict(Transaction.objects.filter(financial_space=space, date__lte=today, type=Transaction.Type.TRANSFER).values("destination_account_id").annotate(total=Sum("amount")).values_list("destination_account_id", "total"))
    for account in accounts:
        account.balance = account.opening_balance + outgoing.get(account.pk, ZERO) + incoming.get(account.pk, ZERO)
    return accounts


def dashboard_summary(space, year, month):
    entries = Transaction.objects.filter(financial_space=space, date__year=year, date__month=month)
    totals = entries.aggregate(
        income=Sum("amount", filter=Q(type=Transaction.Type.INCOME)),
        expenses=Sum("amount", filter=Q(type=Transaction.Type.EXPENSE)),
    )
    rows = budget_progress(space, year, month)
    limit = sum((row["budget"].limit_amount for row in rows), ZERO)
    used = sum((row["used"] for row in rows), ZERO)
    today = timezone.localdate()
    daily = None
    if rows and (year, month) == (today.year, today.month):
        daily = max(limit - used, ZERO) / (monthrange(year, month)[1] - today.day + 1)
    return {
        "balance": sum((account.balance for account in account_balances(space)), ZERO),
        "income": totals["income"] or ZERO, "expenses": totals["expenses"] or ZERO,
        "budget_rows": rows, "budget_limit": limit, "budget_used": used,
        "budget_percentage": used * 100 / limit if limit else ZERO,
        "daily": daily, "month_date": date(year, month, 1),
        "recent": entries.select_related("account", "category", "installment__group")[:6],
        "categories": entries.filter(type=Transaction.Type.EXPENSE).values("category__name").annotate(total=Sum("amount")).order_by("-total"),
    }
