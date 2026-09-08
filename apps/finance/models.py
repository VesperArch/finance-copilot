from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class FinancialSpace(models.Model):
    name = models.CharField("Nome", max_length=100, default="Pessoal")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="financial_spaces")
    currency = models.CharField("Moeda", max_length=3, default="BRL", editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Espaço financeiro"
        verbose_name_plural = "Espaços financeiros"

    def __str__(self):
        return self.name


class SpaceRecord(models.Model):
    financial_space = models.ForeignKey(FinancialSpace, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Account(SpaceRecord):
    class Type(models.TextChoices):
        CHECKING = "CHECKING", "Conta corrente"
        WALLET = "WALLET", "Carteira"
        SAVINGS = "SAVINGS", "Poupança"
        CARD = "CARD", "Cartão"
        DIGITAL = "DIGITAL", "Conta digital"

    name = models.CharField("Nome", max_length=100)
    type = models.CharField("Tipo", max_length=10, choices=Type.choices, default=Type.CHECKING)
    institution = models.CharField("Instituição", max_length=100, blank=True)
    opening_balance = models.DecimalField("Saldo inicial", max_digits=14, decimal_places=2, default=Decimal("0"))
    active = models.BooleanField("Ativa", default=True)

    class Meta:
        verbose_name = "Conta"
        verbose_name_plural = "Contas"
        ordering = ["name", "pk"]
        constraints = [models.UniqueConstraint(fields=["financial_space", "name"], name="unique_account_name")]

    def __str__(self):
        return self.name


class Category(SpaceRecord):
    class Type(models.TextChoices):
        INCOME = "INCOME", "Entrada"
        EXPENSE = "EXPENSE", "Gasto"

    name = models.CharField("Nome", max_length=80)
    type = models.CharField("Tipo", max_length=7, choices=Type.choices, default=Type.EXPENSE)
    active = models.BooleanField("Ativa", default=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["type", "name", "pk"]
        constraints = [models.UniqueConstraint(fields=["financial_space", "name", "type"], name="unique_category_name")]

    def clean(self):
        super().clean()
        if self.pk and Category.objects.filter(pk=self.pk).exclude(type=self.type).exists():
            if self.transaction_set.exists() or self.budget_set.exists():
                raise ValidationError({"type": "Esta categoria já está em uso. Crie outra categoria para mudar o tipo."})

    def __str__(self):
        return f"{self.name} · {self.get_type_display()}"


class InstallmentGroup(SpaceRecord):
    description = models.CharField("Compra", max_length=160)
    total_amount = models.DecimalField("Valor total", max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    count = models.PositiveSmallIntegerField("Quantidade")
    first_date = models.DateField("Primeiro vencimento")

    class Meta:
        verbose_name = "Compra parcelada"
        verbose_name_plural = "Compras parceladas"
        constraints = [
            models.CheckConstraint(condition=Q(total_amount__gt=0), name="positive_purchase_total"),
            models.CheckConstraint(condition=Q(count__gte=2, count__lte=120), name="valid_installment_count"),
        ]

    def __str__(self):
        return self.description


class Transaction(SpaceRecord):
    class Type(models.TextChoices):
        INCOME = "INCOME", "Entrada"
        EXPENSE = "EXPENSE", "Gasto"
        TRANSFER = "TRANSFER", "Transferência"

    class Source(models.TextChoices):
        MANUAL = "MANUAL", "Manual"
        CSV = "CSV", "CSV"
        OFX = "OFX", "OFX"
        RECEIPT = "RECEIPT", "Comprovante"
        API = "API", "API"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    account = models.ForeignKey(Account, verbose_name="Conta", on_delete=models.PROTECT, related_name="transactions")
    destination_account = models.ForeignKey(Account, verbose_name="Conta de destino", on_delete=models.PROTECT, related_name="incoming_transfers", null=True, blank=True)
    category = models.ForeignKey(Category, verbose_name="Categoria", on_delete=models.PROTECT, null=True, blank=True)
    type = models.CharField("Tipo", max_length=8, choices=Type.choices, default=Type.EXPENSE)
    description = models.CharField("Descrição", max_length=160)
    amount = models.DecimalField("Valor", max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    date = models.DateField("Data", default=timezone.localdate)
    notes = models.TextField("Observações", blank=True, max_length=2000)
    source = models.CharField(max_length=7, choices=Source.choices, default=Source.MANUAL, editable=False)
    recurring = models.BooleanField(default=False, editable=False)
    installment_group = models.ForeignKey(InstallmentGroup, on_delete=models.CASCADE, related_name="transactions", null=True, blank=True, editable=False)

    class Meta:
        verbose_name = "Lançamento"
        verbose_name_plural = "Lançamentos"
        ordering = ["-date", "-pk"]
        indexes = [models.Index(fields=["financial_space", "date"])]
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="positive_transaction_amount"),
            models.CheckConstraint(condition=(Q(type="TRANSFER", category__isnull=True, destination_account__isnull=False) & ~Q(account=F("destination_account"))) | Q(type__in=["INCOME", "EXPENSE"], category__isnull=False, destination_account__isnull=True), name="valid_transaction_kind"),
        ]

    def clean(self):
        super().clean()
        errors = {}
        for field in ("account", "destination_account", "category", "installment_group"):
            related = getattr(self, field) if getattr(self, f"{field}_id") else None
            if related and related.financial_space_id != self.financial_space_id:
                errors[field] = "Escolha um registro do seu espaço financeiro."
        if self.user_id and self.financial_space_id and self.financial_space.owner_id != self.user_id:
            errors["user"] = "Este usuário não tem acesso ao espaço financeiro."
        if self.type == self.Type.TRANSFER:
            if not self.destination_account_id or self.destination_account_id == self.account_id:
                errors["destination_account"] = "Escolha uma conta de destino diferente da origem."
            if self.category_id:
                errors["category"] = "Transferências não precisam de categoria."
            if self.installment_group_id:
                errors["installment_group"] = "Transferências não podem ser parceladas."
        else:
            if not self.category_id:
                errors["category"] = "Escolha uma categoria."
            elif self.category.type != self.type:
                errors["category"] = "Escolha uma categoria compatível com o tipo da movimentação."
            if self.destination_account_id:
                errors["destination_account"] = "Use conta de destino apenas para transferências."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.description


class Parcela(models.Model):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name="installment", verbose_name="Lançamento")
    group = models.ForeignKey(InstallmentGroup, on_delete=models.CASCADE, related_name="installments", verbose_name="Compra")
    number = models.PositiveSmallIntegerField("Número")

    class Meta:
        verbose_name = "Parcela"
        verbose_name_plural = "Parcelas"
        ordering = ["number"]
        constraints = [
            models.UniqueConstraint(fields=["group", "number"], name="unique_installment_number"),
            models.CheckConstraint(condition=Q(number__gte=1), name="positive_installment_number"),
        ]

    def clean(self):
        super().clean()
        if self.transaction_id and self.group_id:
            if self.transaction.installment_group_id != self.group_id or self.number > self.group.count:
                raise ValidationError("A parcela deve pertencer à mesma compra e respeitar a quantidade definida.")

    def __str__(self):
        return f"{self.number}/{self.group.count} · {self.group.description}"
