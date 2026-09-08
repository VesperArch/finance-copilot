from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from apps.finance.models import Category, SpaceRecord


class Budget(SpaceRecord):
    category = models.ForeignKey(Category, verbose_name="Categoria", on_delete=models.PROTECT)
    month = models.PositiveSmallIntegerField("Mês", validators=[MinValueValidator(1), MaxValueValidator(12)])
    year = models.PositiveSmallIntegerField("Ano", validators=[MinValueValidator(1900), MaxValueValidator(9999)])
    limit_amount = models.DecimalField("Limite mensal", max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    alert_threshold = models.PositiveSmallIntegerField("Alertar a partir de (%)", default=75, validators=[MinValueValidator(1), MaxValueValidator(100)])

    class Meta:
        verbose_name = "Orçamento"
        verbose_name_plural = "Orçamentos"
        ordering = ["-year", "-month", "category__name"]
        constraints = [
            models.UniqueConstraint(fields=["financial_space", "category", "year", "month"], name="unique_monthly_budget", violation_error_message="Já existe um orçamento para esta categoria neste mês."),
            models.CheckConstraint(condition=Q(month__gte=1, month__lte=12), name="valid_budget_month"),
            models.CheckConstraint(condition=Q(year__gte=1900, year__lte=9999), name="valid_budget_year"),
            models.CheckConstraint(condition=Q(limit_amount__gt=0), name="positive_budget_limit"),
            models.CheckConstraint(condition=Q(alert_threshold__gte=1, alert_threshold__lte=100), name="valid_budget_alert"),
        ]

    def clean(self):
        super().clean()
        if self.category_id:
            if self.category.financial_space_id != self.financial_space_id:
                raise ValidationError({"category": "Escolha uma categoria do seu espaço financeiro."})
            if self.category.type != Category.Type.EXPENSE:
                raise ValidationError({"category": "Planeje seus limites em categorias de gastos."})

    def __str__(self):
        return f"{self.category.name} · {self.month:02d}/{self.year}"
