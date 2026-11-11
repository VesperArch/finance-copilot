from copy import copy

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from rest_framework import serializers

from apps.accounts.models import Membership, MembershipInvitation, Role
from apps.budgets.models import Budget
from apps.core.access import request_space
from apps.finance.models import Account, Category, FinancialSpace, InstallmentGroup, Parcela, Transaction
from apps.finance.services.installments import save_transaction
from apps.finance.services.records import save_record


class StrictInputMixin:
    def to_internal_value(self, data):
        if hasattr(data, "keys"):
            allowed = {name for name, field in self.fields.items() if not field.read_only}
            unexpected = set(data.keys()) - allowed
            if unexpected:
                raise serializers.ValidationError({name: "Campo desconhecido ou somente leitura." for name in sorted(unexpected)})
        return super().to_internal_value(data)


class SpaceSerializer(StrictInputMixin, serializers.ModelSerializer):
    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        if request:
            space = request_space(request)
            for name in ("account", "destination_account", "category"):
                if name in fields:
                    field = fields[name]
                    selected = getattr(self.instance, f"{name}_id", None)
                    field.queryset = field.queryset.filter(financial_space=space).filter(Q(active=True) | Q(pk=selected))
                    if isinstance(self, BudgetSerializer) and name == "category":
                        field.queryset = field.queryset.filter(type=Category.Type.EXPENSE)
        return fields

    def validate(self, attrs):
        instance = copy(self.instance) if self.instance else self.Meta.model(financial_space=request_space(self.context["request"]))
        for name, value in attrs.items():
            if name != "installments":
                setattr(instance, name, value)
        if isinstance(instance, Transaction) and not instance.pk:
            instance.user = self.context["request"].user
            instance.source = Transaction.Source.API
        try:
            instance.full_clean()
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.message_dict if hasattr(error, "message_dict") else error.messages)
        return attrs

    def create(self, validated_data):
        record = self.Meta.model(financial_space=request_space(self.context["request"]), **validated_data)
        return save_record(record, self.context["request"].user)

    def update(self, instance, validated_data):
        for name, value in validated_data.items():
            setattr(instance, name, value)
        return save_record(instance, self.context["request"].user)


class AccountSerializer(SpaceSerializer):
    class Meta:
        model = Account
        fields = ["id", "name", "type", "institution", "opening_balance", "active"]
        read_only_fields = ["id"]
        validators = []


class CategorySerializer(SpaceSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "type", "active"]
        read_only_fields = ["id"]
        validators = []


class BudgetSerializer(SpaceSerializer):
    class Meta:
        model = Budget
        fields = ["id", "category", "month", "year", "limit_amount", "alert_threshold"]
        read_only_fields = ["id"]
        validators = []


class TransactionSerializer(SpaceSerializer):
    installments = serializers.IntegerField(write_only=True, default=1, min_value=1, max_value=120)

    class Meta:
        model = Transaction
        fields = ["id", "description", "type", "amount", "account", "category", "date", "destination_account", "notes", "user", "source", "installment_group", "installments"]
        read_only_fields = ["id", "user", "source", "installment_group"]
        validators = []

    def create(self, validated_data):
        count = validated_data.pop("installments", 1)
        request = self.context["request"]
        entry = Transaction(financial_space=request_space(request), user=request.user, source=Transaction.Source.API, **validated_data)
        return save_transaction(entry, count, actor=request.user)

    def update(self, instance, validated_data):
        count = validated_data.pop("installments", 1)
        if count != 1:
            raise serializers.ValidationError({"installments": "Parcelamento disponível apenas para novos gastos."})
        for name, value in validated_data.items():
            setattr(instance, name, value)
        return save_transaction(instance, actor=self.context["request"].user)


class InstallmentSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(source="transaction.amount", max_digits=14, decimal_places=2, read_only=True)
    date = serializers.DateField(source="transaction.date", read_only=True)

    class Meta:
        model = Parcela
        fields = ["id", "group", "transaction", "number", "amount", "date"]
        read_only_fields = fields


class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstallmentGroup
        fields = ["id", "description", "total_amount", "count", "first_date"]
        read_only_fields = fields


class PurchaseCreateSerializer(TransactionSerializer):
    installments = serializers.IntegerField(write_only=True, min_value=2, max_value=120)

    def validate_type(self, value):
        if value != Transaction.Type.EXPENSE:
            raise serializers.ValidationError("Somente gastos podem ser parcelados.")
        return value


class OrganizationSerializer(StrictInputMixin, serializers.ModelSerializer):
    class Meta:
        model = FinancialSpace
        fields = ["id", "name", "currency", "owner"]
        read_only_fields = ["id", "currency", "owner"]


class MemberSerializer(StrictInputMixin, serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Membership
        fields = ["id", "user", "username", "role"]
        read_only_fields = ["id", "user", "username"]


class InvitationCreateSerializer(StrictInputMixin, serializers.Serializer):
    username = serializers.CharField(max_length=150)
    role = serializers.ChoiceField(choices=Role.choices, default=Role.OPERATOR)


class InvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipInvitation
        fields = ["id", "user", "role", "expires_at", "accepted_at"]
        read_only_fields = fields


class SwitchSerializer(StrictInputMixin, serializers.Serializer):
    financial_space = serializers.IntegerField(min_value=1)
