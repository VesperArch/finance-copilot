from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Membership, Role
from apps.accounts.services import invite_member
from apps.finance.models import Account, Category, InstallmentGroup, Parcela, Transaction
from apps.finance.services.installments import save_transaction
from tests.test_finance import FinanceTestCase


class APITests(FinanceTestCase):
    def setUp(self):
        self.api = APIClient()
        self.api.force_login(self.user)

    def payload(self, **kwargs):
        data = {"description": "Compra API", "type": "EXPENSE", "amount": "100.00", "account": self.account.pk,
                "category": self.category.pk, "date": timezone.localdate().isoformat()}
        data.update(kwargs)
        return data

    def test_anonymous_api_is_denied(self):
        self.api.logout()
        for route in ("accounts", "categories", "transactions", "budgets", "purchases", "installments", "organizations", "members", "invitations", "me", "dashboard"):
            self.assertEqual(self.api.get(f"/api/{route}/").status_code, 403)
        self.assertEqual(self.api.post("/api/transactions/", self.payload(), format="json").status_code, 403)

    def test_no_profile_or_superuser_gets_controlled_denial(self):
        user = User.objects.create_superuser("root", "root@example.com", "Senha-Forte-2026")
        self.api.force_login(user)
        self.assertEqual(self.api.get("/api/accounts/").status_code, 403)
        self.assertEqual(self.api.get("/api/me/").status_code, 403)

    def test_account_crud_and_pagination(self):
        url = "/api/accounts/"
        response = self.api.post(url, {"name": "Digital", "type": "DIGITAL", "opening_balance": "12.34"}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        detail = f"{url}{response.data['id']}/"
        self.assertEqual(self.api.get(detail).data["opening_balance"], "12.34")
        self.assertEqual(self.api.patch(detail, {"name": "Nova"}, format="json").status_code, 200)
        self.assertEqual(self.api.put(detail, {"name": "Completa", "type": "WALLET", "opening_balance": "0.01", "active": True}, format="json").status_code, 200)
        listing = self.api.get(url)
        self.assertEqual(listing.data["count"], 2)
        self.assertIn("results", listing.data)
        self.assertEqual(self.api.delete(detail).status_code, 204)
        self.assertEqual(self.api.get(detail).status_code, 404)

    def test_category_crud_and_duplicate_names(self):
        response = self.api.post("/api/categories/", {"name": "Pet", "type": "EXPENSE"}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        detail = f"/api/categories/{response.data['id']}/"
        self.assertEqual(self.api.patch(detail, {"name": "Animais"}, format="json").status_code, 200)
        self.assertEqual(self.api.get(detail).data["name"], "Animais")
        self.assertEqual(self.api.post("/api/categories/", {"name": "Animais", "type": "EXPENSE"}, format="json").status_code, 400)
        self.assertEqual(self.api.delete(detail).status_code, 204)

    def test_transaction_crud_preserves_decimal(self):
        response = self.api.post("/api/transactions/", self.payload(amount="42.90"), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        entry = Transaction.objects.get(pk=response.data["id"])
        self.assertEqual(entry.financial_space_id, self.space.pk)
        self.assertEqual(entry.user_id, self.user.pk)
        self.assertEqual(entry.source, "API")
        detail = f"/api/transactions/{entry.pk}/"
        self.assertEqual(self.api.patch(detail, {"amount": "0.01"}, format="json").status_code, 200)
        response = self.api.put(detail, self.payload(amount="999999999999.99"), format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["amount"], "999999999999.99")
        self.assertEqual(self.api.delete(detail).status_code, 204)

    def test_budget_crud_and_validation(self):
        payload = {"category": self.category.pk, "month": 11, "year": 2026, "limit_amount": "100.00", "alert_threshold": 75}
        response = self.api.post("/api/budgets/", payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        detail = f"/api/budgets/{response.data['id']}/"
        self.assertEqual(self.api.patch(detail, {"limit_amount": "250.00"}, format="json").status_code, 200)
        self.assertEqual(self.api.post("/api/budgets/", payload, format="json").status_code, 400)
        self.assertEqual(self.api.patch(detail, {"month": 13}, format="json").status_code, 400)
        self.assertEqual(self.api.delete(detail).status_code, 204)

    def test_foreign_resource_ids_cannot_be_read_updated_or_deleted(self):
        category = Category.objects.get(financial_space=self.other_space, name="Alimentação")
        entry = save_transaction(self.entry(financial_space=self.other_space, account=self.other_account, user=self.other, category=category))
        budget = self.budget(financial_space=self.other_space, category=category)
        for route, obj in [("accounts", self.other_account), ("categories", category), ("transactions", entry), ("budgets", budget)]:
            url = f"/api/{route}/{obj.pk}/"
            for method in ("get", "put", "patch", "delete"):
                with self.subTest(route=route, method=method):
                    response = getattr(self.api, method)(url, {}, format="json")
                    self.assertEqual(response.status_code, 404)
            ids = {record["id"] for record in self.api.get(f"/api/{route}/").data["results"]}
            self.assertNotIn(obj.pk, ids)

    def test_foreign_relationships_rejected(self):
        foreign = Category.objects.get(financial_space=self.other_space, name="Alimentação")
        for changes in ({"account": self.other_account.pk}, {"category": foreign.pk},
                        {"type": "TRANSFER", "category": None, "destination_account": self.other_account.pk}):
            response = self.api.post("/api/transactions/", self.payload(**changes), format="json")
            self.assertEqual(response.status_code, 400, response.data)
        response = self.api.post("/api/budgets/", {"category": foreign.pk, "month": 1, "year": 2026, "limit_amount": "50"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_mass_assignment_and_derived_fields_rejected(self):
        for field, value in {"financial_space": self.other_space.pk, "user": self.other.pk, "source": "MANUAL", "installment_group": 1, "id": 900}.items():
            response = self.api.post("/api/transactions/", self.payload(**{field: value}), format="json")
            self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(self.api.post("/api/accounts/", {"name": "Ataque", "financial_space": self.other_space.pk}, format="json").status_code, 400)
        self.assertFalse(Transaction.objects.exists())

    def test_invalid_values_and_kinds(self):
        for amount in ("0", "-0.01", "1000000000000.00", "1.001", "NaN"):
            with self.subTest(amount=amount):
                self.assertEqual(self.api.post("/api/transactions/", self.payload(amount=amount), format="json").status_code, 400)
        for changes in ({"type": "INCOME"}, {"date": "2026-02-30"}, {"type": "TRANSFER", "category": None, "destination_account": self.account.pk}):
            self.assertEqual(self.api.post("/api/transactions/", self.payload(**changes), format="json").status_code, 400)

    def test_transfer_has_no_impact_on_total_income_expenses_or_budget(self):
        destination = Account.objects.create(financial_space=self.space, name="Destino")
        response = self.api.post("/api/transactions/", self.payload(type="TRANSFER", category=None, destination_account=destination.pk, amount="25.00"), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        summary = self.api.get("/api/dashboard/").data
        self.assertEqual(summary["balance"], "100.00")
        for key in ("income", "expenses", "budget_used", "result"):
            self.assertEqual(summary[key], "0.00")

    def test_purchase_rounding_dates_source_and_individual_protection(self):
        response = self.api.post("/api/purchases/", self.payload(installments=3, date="2028-01-31"), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        group = InstallmentGroup.objects.get(pk=response.data["id"])
        installments = self.api.get(f"/api/purchases/{group.pk}/installments/")
        self.assertEqual(installments.status_code, 200, installments.data)
        self.assertEqual([p["amount"] for p in installments.data["results"]], ["33.33", "33.33", "33.34"])
        self.assertEqual([p["date"] for p in installments.data["results"]], ["2028-01-31", "2028-02-29", "2028-03-31"])
        self.assertEqual(group.transactions.count(), 3)
        self.assertEqual(group.transactions.exclude(source="API").count(), 0)
        for payment in group.installments.all():
            self.assertEqual(self.api.get(f"/api/installments/{payment.pk}/").status_code, 200)
            for method in ("put", "patch", "delete"):
                self.assertEqual(getattr(self.api, method)(f"/api/installments/{payment.pk}/", {}, format="json").status_code, 405)
                self.assertEqual(getattr(self.api, method)(f"/api/transactions/{payment.transaction_id}/", {}, format="json").status_code, 403)
        self.assertEqual(self.api.patch(f"/api/purchases/{group.pk}/", {"count": 4}, format="json").status_code, 405)
        self.assertEqual(self.api.delete(f"/api/purchases/{group.pk}/").status_code, 204)
        self.assertEqual(Parcela.objects.count(), 0)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_invalid_purchase_is_atomic(self):
        for changes in ({"installments": 1}, {"installments": 121}, {"installments": 2, "amount": "0.01"}, {"installments": 2, "date": "9999-12-31"}):
            self.assertEqual(self.api.post("/api/purchases/", self.payload(**changes), format="json").status_code, 400)
        self.assertEqual(InstallmentGroup.objects.count(), 0)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_operator_shared_data_author_and_administrative_denial(self):
        Membership.objects.create(user=self.other, financial_space=self.space)
        self.api.force_login(self.other)
        self.assertEqual(self.api.post("/api/context/", {"financial_space": self.space.pk}, format="json").status_code, 200)
        response = self.api.post("/api/transactions/", self.payload(), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["user"], self.other.pk)
        for route in ("members", "invitations"):
            self.assertEqual(self.api.get(f"/api/{route}/").status_code, 403)
            self.assertEqual(self.api.post(f"/api/{route}/", {"role": "ADMIN"}, format="json").status_code, 403)
        self.assertEqual(self.api.patch(f"/api/organizations/{self.space.pk}/", {"name": "Ataque"}, format="json").status_code, 403)

    def test_author_preserved_on_api_edit(self):
        member = User.objects.create_user("colaborador")
        Membership.objects.create(user=member, financial_space=self.space)
        entry = save_transaction(self.entry())
        self.api.force_login(member)
        response = self.api.patch(f"/api/transactions/{entry.pk}/", {"description": "Atualizado"}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["user"], self.user.pk)

    def test_protected_history_returns_conflict(self):
        save_transaction(self.entry())
        self.assertEqual(self.api.delete(f"/api/accounts/{self.account.pk}/").status_code, 409)
        self.assertEqual(self.api.delete(f"/api/categories/{self.category.pk}/").status_code, 409)
        self.assertEqual(self.api.patch(f"/api/categories/{self.category.pk}/", {"type": "INCOME"}, format="json").status_code, 400)

    def test_inactive_relations_reject_new_records_allow_history_edits(self):
        entry = save_transaction(self.entry())
        self.account.active = False
        self.account.save()
        self.assertEqual(self.api.post("/api/transactions/", self.payload(), format="json").status_code, 400)
        self.assertEqual(self.api.patch(f"/api/transactions/{entry.pk}/", {"notes": "Histórico"}, format="json").status_code, 200)

    def test_foreign_purchase_and_installment_are_hidden(self):
        entry = save_transaction(self.entry(), 2)
        self.api.force_login(self.other)
        group = entry.installment_group
        payment = group.installments.first()
        for url in (f"/api/purchases/{group.pk}/", f"/api/purchases/{group.pk}/installments/", f"/api/installments/{payment.pk}/"):
            self.assertEqual(self.api.get(url).status_code, 404)
        self.assertEqual(self.api.delete(f"/api/purchases/{group.pk}/").status_code, 404)
        self.assertEqual(self.api.get("/api/installments/").data["count"], 0)

    def test_profile_context_and_cross_tenant_rejection(self):
        profile = self.api.get("/api/me/")
        self.assertEqual(profile.data["financial_space"], self.space.pk)
        self.assertEqual(profile.data["role"], "ADMIN")
        self.assertEqual(self.api.post("/api/context/", {"financial_space": self.other_space.pk}, format="json").status_code, 403)
        self.assertEqual(self.api.get(f"/api/organizations/{self.other_space.pk}/").status_code, 404)
        self.assertEqual(self.api.post("/api/organizations/", {"name": "Nova"}, format="json").status_code, 405)
        self.assertEqual(self.api.patch(f"/api/organizations/{self.space.pk}/", {"name": "Equipe"}, format="json").status_code, 200)
        self.assertEqual(self.api.patch(f"/api/organizations/{self.space.pk}/", {"owner": self.other.pk}, format="json").status_code, 400)

    def test_admin_member_invitation_crud_and_foreign_ids(self):
        response = self.api.post("/api/invitations/", {"username": self.other.username, "role": "OPERATOR"}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        token = response.data["id"]
        self.api.force_login(self.other)
        self.assertEqual(self.api.post(f"/api/invitations/{token}/accept/", {}, format="json").status_code, 201)
        self.api.force_login(self.user)
        member = Membership.objects.get(user=self.other, financial_space=self.space)
        response = self.api.patch(f"/api/members/{member.pk}/", {"role": "ADMIN"}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        foreign = Membership.objects.get(user=self.other, financial_space=self.other_space)
        for method in ("get", "patch", "delete"):
            self.assertEqual(getattr(self.api, method)(f"/api/members/{foreign.pk}/", {"role": "ADMIN"}, format="json").status_code, 404)
        self.assertEqual(self.api.delete(f"/api/members/{member.pk}/").status_code, 204)
        owner = Membership.objects.get(user=self.user, financial_space=self.space)
        self.assertEqual(self.api.delete(f"/api/members/{owner.pk}/").status_code, 400)
        self.assertEqual(self.api.patch(f"/api/members/{owner.pk}/", {"role": "OPERATOR"}, format="json").status_code, 400)

    def test_session_authentication_enforces_csrf(self):
        api = APIClient(enforce_csrf_checks=True)
        api.force_login(self.user)
        self.assertEqual(api.post("/api/accounts/", {"name": "CSRF"}, format="json").status_code, 403)
        api.get(reverse("account-create"))
        token = api.cookies["csrftoken"].value
        self.assertEqual(api.post("/api/accounts/", {"name": "CSRF"}, format="json", HTTP_X_CSRFTOKEN=token).status_code, 201)

    def test_dashboard_isolation_month_validation_and_future_semantics(self):
        save_transaction(self.entry(amount=Decimal("60.00"), date=date(2026, 12, 31)), 3)
        self.budget(month=12, year=2026)
        summary = self.api.get("/api/dashboard/?month=2026-12").data
        self.assertEqual(summary["expenses"], "20.00")
        self.assertEqual(summary["budget_used"], "20.00")
        self.assertEqual(summary["transaction_count"], 1)
        self.assertEqual(summary["result"], "-20.00")
        self.assertEqual(self.api.get("/api/dashboard/?month=2026-99").status_code, 400)
        self.api.force_login(self.other)
        summary = self.api.get("/api/dashboard/?month=2026-12").data
        self.assertEqual(summary["expenses"], "0.00")
        self.assertEqual(summary["categories"], [])

    def test_membership_role_updates_are_effective_on_next_request(self):
        member = Membership.objects.create(user=self.other, financial_space=self.space)
        self.api.force_login(self.other)
        self.api.post("/api/context/", {"financial_space": self.space.pk}, format="json")
        self.assertEqual(self.api.get("/api/members/").status_code, 403)
        member.role = Role.ADMIN
        member.save()
        self.assertEqual(self.api.get("/api/members/").status_code, 200)
        member.delete()
        self.assertEqual(self.api.get("/api/accounts/").status_code, 403)
        self.assertEqual(self.api.post("/api/accounts/", {"name": "Revogado"}, format="json").status_code, 403)

    def test_operator_cannot_directly_change_or_remove_members(self):
        member = Membership.objects.create(user=self.other, financial_space=self.space)
        self.api.force_login(self.other)
        self.api.post("/api/context/", {"financial_space": self.space.pk}, format="json")
        for method in ("put", "patch", "delete"):
            self.assertEqual(getattr(self.api, method)(f"/api/members/{member.pk}/", {"role": "ADMIN"}, format="json").status_code, 403)

    def test_invitation_is_bound_to_target_and_can_be_revoked(self):
        invitation = invite_member(self.user, self.space, self.other.username, Role.OPERATOR)
        url = f"/api/invitations/{invitation.pk}/accept/"
        self.assertEqual(self.api.post(url, {}, format="json").status_code, 404)
        self.assertEqual(self.api.delete(f"/api/invitations/{invitation.pk}/").status_code, 204)
        self.api.force_login(self.other)
        self.assertEqual(self.api.post(url, {}, format="json").status_code, 404)

    def test_invitation_role_and_member_identity_are_protected(self):
        invitation = invite_member(self.user, self.space, self.other.username, Role.OPERATOR)
        self.api.force_login(self.other)
        response = self.api.post(f"/api/invitations/{invitation.pk}/accept/", {"role": "ADMIN"}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["role"], Role.OPERATOR)
        self.api.force_login(self.user)
        member = Membership.objects.get(user=self.other, financial_space=self.space)
        self.assertEqual(self.api.patch(f"/api/members/{member.pk}/", {"user": self.user.pk}, format="json").status_code, 400)
        self.assertEqual(self.api.patch(f"/api/members/{member.pk}/", {"financial_space": self.other_space.pk}, format="json").status_code, 400)

    def test_transaction_endpoint_can_create_purchase_and_blocks_reinstallment(self):
        response = self.api.post("/api/transactions/", self.payload(installments=2), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertIsNotNone(response.data["installment_group"])
        response = self.api.post("/api/transactions/", self.payload(), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.api.patch(f"/api/transactions/{response.data['id']}/", {"installments": 2}, format="json").status_code, 400)

    def test_budget_rejects_income_and_inactive_categories(self):
        income = Category.objects.get(financial_space=self.space, name="Salário")
        self.category.active = False
        self.category.save()
        for category in (income, self.category):
            response = self.api.post("/api/budgets/", {"category": category.pk, "month": 1, "year": 2026, "limit_amount": "10"}, format="json")
            self.assertEqual(response.status_code, 400, response.data)

    def test_lists_have_no_per_record_relationship_queries(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        save_transaction(self.entry(), 25)
        with CaptureQueriesContext(connection) as queries:
            response = self.api.get("/api/installments/")
            self.assertEqual(len(response.data["results"]), 25)
        self.assertLessEqual(len(queries), 6, [q["sql"] for q in queries])
