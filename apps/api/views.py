from decimal import Decimal

from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Membership, MembershipInvitation
from apps.accounts.services import accept_invitation, change_member, invite_member, rename_space, revoke_invitation
from apps.api.permissions import OrganizationAdmin, OrganizationMember
from apps.api.serializers import (
    AccountSerializer, BudgetSerializer, CategorySerializer, InstallmentSerializer,
    InvitationCreateSerializer, InvitationSerializer, MemberSerializer,
    OrganizationSerializer, PurchaseCreateSerializer, PurchaseSerializer,
    SwitchSerializer, TransactionSerializer,
)
from apps.core.access import SESSION_SPACE_KEY, current_membership, request_membership, request_space
from apps.core.forms import MonthForm
from apps.budgets.models import Budget
from apps.finance.models import Account, Category, InstallmentGroup, Parcela, Transaction
from apps.finance.services.records import delete_record
from apps.finance.services.summary import dashboard_summary


class SpaceViewSet(viewsets.ModelViewSet):
    permission_classes = [OrganizationMember]

    def get_queryset(self):
        return self.queryset.filter(financial_space=request_space(self.request))

    def perform_destroy(self, instance):
        delete_record(instance, self.request.user)


class AccountViewSet(SpaceViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer


class CategoryViewSet(SpaceViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class BudgetViewSet(SpaceViewSet):
    queryset = Budget.objects.select_related("category")
    serializer_class = BudgetSerializer


class TransactionViewSet(SpaceViewSet):
    queryset = Transaction.objects.select_related("account", "destination_account", "category", "installment_group", "user")
    serializer_class = TransactionSerializer

    def get_object(self):
        instance = super().get_object()
        if self.request.method in ("PUT", "PATCH", "DELETE") and instance.installment_group_id:
            raise PermissionDenied("Parcelas individuais não podem ser alteradas. Exclua a compra completa.")
        return instance


class PurchaseViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    permission_classes = [OrganizationMember]
    serializer_class = PurchaseSerializer

    def get_queryset(self):
        return InstallmentGroup.objects.filter(financial_space=request_space(self.request)).order_by("-pk")

    def get_serializer_class(self):
        return PurchaseCreateSerializer if self.action == "create" else PurchaseSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entry = serializer.save()
        return Response(PurchaseSerializer(entry.installment_group).data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        delete_record(instance, self.request.user)

    @action(detail=True, methods=["get"], serializer_class=InstallmentSerializer)
    def installments(self, request, pk=None):
        queryset = self.get_object().installments.select_related("transaction")
        page = self.paginate_queryset(queryset)
        return self.get_paginated_response(InstallmentSerializer(page, many=True).data)


class InstallmentViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [OrganizationMember]
    serializer_class = InstallmentSerializer

    def get_queryset(self):
        space = request_space(self.request)
        return Parcela.objects.filter(group__financial_space=space, transaction__financial_space=space).select_related("transaction").order_by("group_id", "number")


class OrganizationViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    permission_classes = [OrganizationMember]
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        return type(request_space(self.request)).objects.filter(pk=request_space(self.request).pk)

    def perform_update(self, serializer):
        space = serializer.instance
        serializer.instance = rename_space(self.request.user, space, serializer.validated_data.get("name", space.name))


class MemberViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    permission_classes = [OrganizationAdmin]
    serializer_class = MemberSerializer

    def get_queryset(self):
        return Membership.objects.filter(financial_space=request_space(self.request)).select_related("user")

    def perform_update(self, serializer):
        serializer.instance = change_member(self.request.user, request_space(self.request), serializer.instance.pk, role=serializer.validated_data.get("role", serializer.instance.role))

    def perform_destroy(self, instance):
        change_member(self.request.user, request_space(self.request), instance.pk, remove=True)


class InvitationViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    permission_classes = [OrganizationAdmin]
    serializer_class = InvitationSerializer

    def get_queryset(self):
        return MembershipInvitation.objects.filter(financial_space=request_space(self.request)).order_by("-expires_at", "pk")

    def get_serializer_class(self):
        return InvitationCreateSerializer if self.action == "create" else InvitationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation = invite_member(request.user, request_space(request), **serializer.validated_data)
        return Response(InvitationSerializer(invitation).data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        revoke_invitation(self.request.user, request_space(self.request), instance.pk)


class AcceptInvitationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, token):
        member = accept_invitation(request.user, token)
        request.session[SESSION_SPACE_KEY] = member.financial_space_id
        return Response(MemberSerializer(member).data, status=status.HTTP_201_CREATED)


class ProfileView(APIView):
    permission_classes = [OrganizationMember]

    def get(self, request):
        member = request_membership(request)
        return Response({
            "id": request.user.pk, "username": request.user.username,
            "financial_space": member.financial_space_id, "role": member.role,
            "memberships": [{"financial_space": item.financial_space_id, "name": item.financial_space.name, "role": item.role}
                            for item in request.user.memberships.select_related("financial_space")],
        })


class SwitchView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SwitchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = current_membership(request.user, serializer.validated_data["financial_space"])
        request.session[SESSION_SPACE_KEY] = member.financial_space_id
        return Response({"financial_space": member.financial_space_id, "role": member.role})


class DashboardView(APIView):
    permission_classes = [OrganizationMember]

    def get(self, request):
        form = MonthForm(request.query_params if "month" in request.query_params else {"month": timezone.localdate().strftime("%Y-%m")})
        if not form.is_valid():
            raise ValidationError(form.errors)
        month = form.cleaned_data["month"]
        summary = dashboard_summary(request_space(request), month.year, month.month)

        def money(value):
            return str(value.quantize(Decimal("0.01"))) if value is not None else None

        return Response({
            "month": month.strftime("%Y-%m"),
            **{key: money(summary[key]) for key in ("balance", "income", "expenses", "result", "budget_limit", "budget_used", "daily")},
            "transaction_count": summary["transaction_count"],
            "categories": [{"name": row["category__name"], "total": money(row["total"])} for row in summary["categories"]],
        })
