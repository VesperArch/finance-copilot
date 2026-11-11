from django.core.exceptions import ValidationError
from django.db import transaction

from apps.core.access import current_membership
from apps.finance.models import Parcela, Transaction


@transaction.atomic
def save_record(record, actor):
    current_membership(actor, record.financial_space_id)
    record.full_clean()
    record.save()
    return record


@transaction.atomic
def delete_record(record, actor):
    current_membership(actor, record.financial_space_id)
    if isinstance(record, Parcela) or isinstance(record, Transaction) and record.installment_group_id:
        raise ValidationError("Exclua a compra completa; parcelas individuais são protegidas.")
    record.delete()
