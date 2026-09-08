from calendar import monthrange
from datetime import date
from decimal import Decimal, ROUND_DOWN

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.finance.models import InstallmentGroup, Parcela, Transaction


def monthly_date(first_date, offset):
    year, month = divmod(first_date.year * 12 + first_date.month - 1 + offset, 12)
    if year > 9999:
        raise ValidationError("A última parcela ultrapassa o limite de datas permitido.")
    month += 1
    return date(year, month, min(first_date.day, monthrange(year, month)[1]))


@transaction.atomic
def save_transaction(entry, count=1):
    if entry.pk and entry.installment_group_id:
        raise ValidationError("Para alterar esta compra, exclua o parcelamento completo e cadastre novamente.")
    entry.full_clean()
    if not 1 <= count <= 120:
        raise ValidationError("Escolha de 1 a 120 parcelas.")
    if count == 1:
        entry.save()
        return entry
    if entry.pk or entry.type != Transaction.Type.EXPENSE:
        raise ValidationError("O parcelamento está disponível para novos gastos.")
    total = entry.amount
    regular = (total / count).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    if regular < Decimal("0.01"):
        raise ValidationError("O valor de cada parcela deve ser de pelo menos R$ 0,01.")
    monthly_date(entry.date, count - 1)
    group = InstallmentGroup.objects.create(
        financial_space=entry.financial_space, description=entry.description,
        total_amount=total, count=count, first_date=entry.date,
    )
    first = None
    for offset in range(count):
        payment = Transaction(
            financial_space=entry.financial_space, user=entry.user,
            account=entry.account, category=entry.category, type=entry.type,
            description=entry.description, notes=entry.notes,
            amount=regular if offset < count - 1 else total - regular * (count - 1),
            date=monthly_date(entry.date, offset), installment_group=group,
        )
        payment.full_clean()
        payment.save()
        Parcela.objects.create(transaction=payment, group=group, number=offset + 1)
        first = first or payment
    return first
