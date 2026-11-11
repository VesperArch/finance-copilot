from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.api import views


router = DefaultRouter()
router.register("accounts", views.AccountViewSet, basename="api-account")
router.register("categories", views.CategoryViewSet, basename="api-category")
router.register("transactions", views.TransactionViewSet, basename="api-transaction")
router.register("budgets", views.BudgetViewSet, basename="api-budget")
router.register("purchases", views.PurchaseViewSet, basename="api-purchase")
router.register("installments", views.InstallmentViewSet, basename="api-installment")
router.register("organizations", views.OrganizationViewSet, basename="api-organization")
router.register("members", views.MemberViewSet, basename="api-member")
router.register("invitations", views.InvitationViewSet, basename="api-invitation")

urlpatterns = [
    path("me/", views.ProfileView.as_view(), name="api-profile"),
    path("context/", views.SwitchView.as_view(), name="api-context"),
    path("dashboard/", views.DashboardView.as_view(), name="api-dashboard"),
    path("invitations/<uuid:token>/accept/", views.AcceptInvitationView.as_view(), name="api-invitation-accept"),
    path("", include(router.urls)),
]
