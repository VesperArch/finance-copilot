from django import forms
from django.utils import timezone

from apps.budgets.models import Budget
from apps.finance.forms import SpaceForm
from apps.finance.models import Category


class BudgetForm(SpaceForm):
    class Meta:
        model = Budget
        fields = ["category", "month", "year", "limit_amount", "alert_threshold"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = self.fields["category"].queryset.filter(type=Category.Type.EXPENSE)
        self.initial.setdefault("month", timezone.localdate().month)
        self.initial.setdefault("year", timezone.localdate().year)

    def clean(self):
        data = super().clean()
        if all(data.get(key) for key in ("category", "month", "year")):
            duplicate = Budget.objects.filter(financial_space=self.instance.financial_space, category=data["category"], month=data["month"], year=data["year"]).exclude(pk=self.instance.pk)
            if duplicate.exists():
                raise forms.ValidationError("Já existe um orçamento para esta categoria neste mês.")
        return data
