from django import forms
from django.db.models import Q

from apps.finance.models import Account, Category, Transaction


class SpaceForm(forms.ModelForm):
    def __init__(self, *args, space, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.financial_space = space
        for name in ("opening_balance", "amount", "limit_amount"):
            if name in self.fields:
                self.fields[name].localize = True
                self.fields[name].widget = forms.TextInput(attrs={"inputmode": "decimal", "placeholder": "0,00"})
        for name, field in self.fields.items():
            if isinstance(field, forms.ModelChoiceField):
                selected = getattr(self.instance, f"{name}_id", None)
                field.queryset = field.queryset.filter(financial_space=space).filter(Q(active=True) | Q(pk=selected))


class AccountForm(SpaceForm):
    class Meta:
        model = Account
        fields = ["name", "type", "institution", "opening_balance", "active"]


class CategoryForm(SpaceForm):
    class Meta:
        model = Category
        fields = ["name", "type", "active"]


class TransactionForm(SpaceForm):
    installments = forms.IntegerField(label="Número de parcelas", min_value=1, max_value=120, initial=1, help_text="Use 1 para pagamento único. Em compras parceladas, informe o valor total e a data da primeira parcela.")

    class Meta:
        model = Transaction
        fields = ["description", "type", "amount", "account", "category", "date", "destination_account", "notes"]
        widgets = {"date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}), "notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.user = user
        if self.instance.pk:
            self.fields["installments"].disabled = True
        self.fields["category"].help_text = "Escolha uma categoria do mesmo tipo. Deixe vazia para transferências."
        self.fields["destination_account"].help_text = "Preencha apenas para transferências entre suas contas."
        if not self.is_bound and not self.instance.pk:
            self.initial["account"] = self.fields["account"].queryset.first()

    def clean(self):
        data = super().clean()
        if data.get("installments", 1) > 1 and data.get("type") != Transaction.Type.EXPENSE:
            self.add_error("installments", "Somente gastos podem ser parcelados.")
        return data
