from decimal import Decimal

from django import template
from django.utils.formats import number_format


register = template.Library()


@register.filter
def brl(value):
    return f"R$ {number_format(value or Decimal('0'), decimal_pos=2, use_l10n=True, force_grouping=True)}"
