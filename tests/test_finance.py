from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.budgets.models import Budget
from apps.budgets.services import budget_progress
from apps.finance.forms import TransactionForm
from apps.finance.models import Account, Category, InstallmentGroup, Parcela, Transaction
from apps.finance.services.installments import monthly_date, save_transaction
from apps.finance.services.spaces import create_personal_space
from apps.finance.services.summary import account_balances, dashboard_summary


class FinanceTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("ana", "ana@example.com", "UmaSenha-Forte-2026")
        cls.space = create_personal_space(cls.user)
        cls.account = Account.objects.create(financial_space=cls.space, name="Principal", opening_balance=Decimal("100.00"))
        cls.category = Category.objects.get(financial_space=cls.space, name="Alimentação")
        cls.other = User.objects.create_user("bia", "bia@example.com", "OutraSenha-Forte-2026")
        cls.other_space = create_personal_space(cls.other)
        cls.other_account = Account.objects.create(financial_space=cls.other_space, name="Outra conta")

    def entry(self, **kwargs):
        data = {"financial_space": self.space, "user": self.user, "account": self.account, "category": self.category, "description": "Mercado", "amount": Decimal("42.90"), "date": timezone.localdate()}
        data.update(kwargs)
        return Transaction(**data)

    def budget(self, **kwargs):
        today = timezone.localdate()
        data = {"financial_space": self.space, "category": self.category, "month": today.month, "year": today.year, "limit_amount": Decimal("100.00")}
        data.update(kwargs)
        return Budget.objects.create(**data)


class TransactionTests(FinanceTestCase):
    def test_create_expense_and_balance(self):
        entry = save_transaction(self.entry())
        self.assertEqual(Transaction.objects.get(pk=entry.pk).amount, Decimal("42.90"))
        self.assertEqual(account_balances(self.space)[0].balance, Decimal("57.10"))

    def test_zero_negative_and_oversized_amounts(self):
        for value in ("0", "-0.01", "1000000000000.00"):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                save_transaction(self.entry(amount=Decimal(value)))
        self.assertEqual(Transaction.objects.count(), 0)

    def test_large_decimal_preserved(self):
        entry = save_transaction(self.entry(amount=Decimal("999999999999.99")))
        entry.refresh_from_db()
        self.assertEqual(entry.amount, Decimal("999999999999.99"))

    def test_database_rejects_nonpositive_amount(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.entry(amount=Decimal("0")).save()

    def test_income_category_must_match(self):
        with self.assertRaises(ValidationError):
            save_transaction(self.entry(type=Transaction.Type.INCOME))

    def test_transfer_moves_money_without_changing_total_or_expenses(self):
        destination = Account.objects.create(financial_space=self.space, name="Poupança")
        save_transaction(self.entry(type=Transaction.Type.TRANSFER, category=None, destination_account=destination, amount=Decimal("25.00")))
        balances = {account.pk: account.balance for account in account_balances(self.space)}
        self.assertEqual(balances, {self.account.pk: Decimal("75.00"), destination.pk: Decimal("25.00")})
        today = timezone.localdate()
        summary = dashboard_summary(self.space, today.year, today.month)
        self.assertEqual(summary["balance"], Decimal("100.00"))
        self.assertEqual(summary["expenses"], Decimal("0.00"))
        self.assertEqual(summary["income"], Decimal("0.00"))

    def test_transfer_requires_different_destination(self):
        for destination in (None, self.account, self.other_account):
            with self.subTest(destination=destination), self.assertRaises(ValidationError):
                save_transaction(self.entry(type=Transaction.Type.TRANSFER, category=None, destination_account=destination))

    def test_foreign_space_rejected(self):
        with self.assertRaises(ValidationError):
            save_transaction(self.entry(account=self.other_account))

    def test_future_expense_does_not_reduce_current_balance(self):
        save_transaction(self.entry(date=monthly_date(timezone.localdate(), 1)))
        self.assertEqual(account_balances(self.space)[0].balance, Decimal("100.00"))

    def test_form_accepts_decimal_comma(self):
        form = TransactionForm(data={"description": "Almoço", "type": "EXPENSE", "amount": "42,90", "account": self.account.pk, "category": self.category.pk, "date": "2026-09-07", "installments": "1"}, space=self.space, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["amount"], Decimal("42.90"))


class InstallmentTests(FinanceTestCase):
    def test_two_installments(self):
        entry = save_transaction(self.entry(amount=Decimal("100.00"), date=date(2026, 12, 31)), 2)
        payments = list(entry.installment_group.installments.select_related("transaction"))
        self.assertEqual([p.transaction.amount for p in payments], [Decimal("50.00"), Decimal("50.00")])
        self.assertEqual([p.transaction.date for p in payments], [date(2026, 12, 31), date(2027, 1, 31)])

    def test_ten_installments(self):
        entry = save_transaction(self.entry(amount=Decimal("3000.00")), 10)
        self.assertEqual(entry.installment_group.installments.count(), 10)
        self.assertEqual(entry.installment_group.transactions.count(), 10)
        self.assertTrue(all(p.amount == Decimal("300.00") for p in entry.installment_group.transactions.all()))

    def test_rounding_difference_in_last_installment(self):
        entry = save_transaction(self.entry(amount=Decimal("100.00")), 3)
        values = [p.transaction.amount for p in entry.installment_group.installments.select_related("transaction")]
        self.assertEqual(values, [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")])
        self.assertEqual(sum(values), Decimal("100.00"))

    def test_small_total_never_creates_zero_or_negative_last_installment(self):
        entry = save_transaction(self.entry(amount=Decimal("0.06")), 4)
        self.assertEqual([p.transaction.amount for p in entry.installment_group.installments.select_related("transaction")], [Decimal("0.01"), Decimal("0.01"), Decimal("0.01"), Decimal("0.03")])

    def test_month_end_anchor_and_leap_year(self):
        self.assertEqual(monthly_date(date(2026, 1, 31), 1), date(2026, 2, 28))
        self.assertEqual(monthly_date(date(2026, 1, 31), 2), date(2026, 3, 31))
        self.assertEqual(monthly_date(date(2028, 1, 31), 1), date(2028, 2, 29))

    def test_invalid_purchase_is_atomic(self):
        for total, count in [("0.01", 2), ("10.00", 121), ("10.00", 0)]:
            with self.subTest(count=count), self.assertRaises(ValidationError):
                save_transaction(self.entry(amount=Decimal(total)), count)
        with self.assertRaises(ValidationError):
            save_transaction(self.entry(date=date(9999, 12, 1)), 2)
        self.assertEqual(Transaction.objects.count(), 0)
        self.assertEqual(InstallmentGroup.objects.count(), 0)

    def test_installment_edit_is_rejected(self):
        entry = save_transaction(self.entry(), 2)
        entry.amount = Decimal("1.00")
        with self.assertRaises(ValidationError):
            save_transaction(entry)

    def test_only_monthly_installment_counts_for_budget(self):
        self.budget(month=1, year=2026)
        save_transaction(self.entry(amount=Decimal("90.00"), date=date(2026, 1, 31)), 3)
        self.assertEqual(budget_progress(self.space, 2026, 1)[0]["used"], Decimal("30.00"))


class BudgetTests(FinanceTestCase):
    def test_empty_exact_and_over_budget(self):
        budget = self.budget()
        row = budget_progress(self.space, budget.year, budget.month)[0]
        self.assertEqual(row["used"], Decimal("0.00"))
        self.assertEqual(row["remaining"], Decimal("100.00"))
        save_transaction(self.entry(amount=Decimal("100.00")))
        row = budget_progress(self.space, budget.year, budget.month)[0]
        self.assertEqual(row["percentage"], Decimal("100"))
        self.assertEqual(row["status"], "Limite atingido")
        save_transaction(self.entry(amount=Decimal("25.00")))
        row = budget_progress(self.space, budget.year, budget.month)[0]
        self.assertEqual(row["remaining"], Decimal("-25.00"))
        self.assertEqual(row["percentage"], Decimal("125"))
        self.assertEqual(row["bar"], Decimal("100"))

    def test_missing_budget(self):
        save_transaction(self.entry())
        today = timezone.localdate()
        self.assertEqual(budget_progress(self.space, today.year, today.month), [])

    def test_alert_thresholds(self):
        budget = self.budget()
        entry = save_transaction(self.entry(amount=Decimal("75")))
        self.assertEqual(budget_progress(self.space, budget.year, budget.month)[0]["status"], "Perto do limite")
        entry.amount = Decimal("90")
        save_transaction(entry)
        self.assertEqual(budget_progress(self.space, budget.year, budget.month)[0]["status"], "Atenção: 90% ou mais utilizado")

    def test_unique_budget_enforced_in_database(self):
        self.budget()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.budget()

    def test_budget_rejects_income_or_foreign_category(self):
        budget = self.budget()
        for category in [Category.objects.get(financial_space=self.space, name="Salário"), Category.objects.get(financial_space=self.other_space, name="Alimentação")]:
            budget.category = category
            with self.assertRaises(ValidationError):
                budget.full_clean()


class PermissionAndViewTests(FinanceTestCase):
    def setUp(self):
        self.client.force_login(self.user)

    def test_authenticated_pages_render(self):
        entry = save_transaction(self.entry())
        budget = self.budget()
        for name in ("dashboard", "account-list", "category-list", "transaction-list", "budget-list", "account-create", "category-create", "transaction-create", "budget-create"):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        for kind, obj in [("account", self.account), ("category", self.category), ("transaction", entry), ("budget", budget)]:
            for action in ("edit", "delete"):
                with self.subTest(kind=kind, action=action):
                    self.assertEqual(self.client.get(reverse(f"{kind}-{action}", args=[obj.pk])).status_code, 200)

    def test_anonymous_redirected(self):
        self.client.logout()
        for name in ("dashboard", "account-list", "category-list", "transaction-list", "budget-list", "transaction-create"):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 302)

    def test_foreign_objects_cannot_be_edited_or_deleted(self):
        category = Category.objects.get(financial_space=self.other_space, name="Alimentação")
        entry = save_transaction(self.entry(financial_space=self.other_space, user=self.other, account=self.other_account, category=category))
        budget = self.budget(financial_space=self.other_space, category=category)
        for kind, obj in [("account", self.other_account), ("category", category), ("transaction", entry), ("budget", budget)]:
            for action in ("edit", "delete"):
                url = reverse(f"{kind}-{action}", args=[obj.pk])
                with self.subTest(kind=kind, action=action):
                    self.assertEqual(self.client.get(url).status_code, 404)
                    self.assertEqual(self.client.post(url, {}).status_code, 404)

    def test_foreign_installments_are_private(self):
        entry = save_transaction(self.entry(), 2)
        self.client.force_login(self.other)
        for name in ("installment-detail", "installment-delete"):
            self.assertEqual(self.client.get(reverse(name, args=[entry.installment_group_id])).status_code, 404)
            self.assertEqual(self.client.post(reverse(name, args=[entry.installment_group_id])).status_code, 404)

    def test_form_cannot_select_foreign_account(self):
        response = self.client.post(reverse("transaction-create"), {"description": "Compra", "amount": "10,00", "type": "EXPENSE", "account": self.other_account.pk, "category": self.category.pk, "date": "2026-09-07", "installments": 1})
        self.assertEqual(response.status_code, 200)
        self.assertIn("account", response.context["form"].errors)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_protected_category_and_account_preserve_history(self):
        save_transaction(self.entry())
        for kind, obj in [("category", self.category), ("account", self.account)]:
            response = self.client.post(reverse(f"{kind}-delete", args=[obj.pk]), follow=True)
            self.assertContains(response, "Este registro está em uso")
            self.assertTrue(type(obj).objects.filter(pk=obj.pk).exists())

    def test_get_delete_is_read_only_and_post_deletes_purchase(self):
        entry = save_transaction(self.entry(), 2)
        url = reverse("installment-delete", args=[entry.installment_group_id])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(Parcela.objects.count(), 2)
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertEqual(Parcela.objects.count(), 0)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_duplicate_budget_has_friendly_error(self):
        budget = self.budget()
        response = self.client.post(reverse("budget-create"), {"category": self.category.pk, "month": budget.month, "year": budget.year, "limit_amount": "100", "alert_threshold": 75})
        self.assertContains(response, "Já existe um orçamento para esta categoria neste mês.")
        self.assertEqual(Budget.objects.count(), 1)

    def test_invalid_month_does_not_crash(self):
        response = self.client.get(reverse("dashboard"), {"month": "2026-99"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["month_form"].errors)

    def test_staff_cannot_read_financial_admin(self):
        self.user.is_staff = True
        self.user.save()
        self.assertEqual(self.client.get(reverse("admin:finance_transaction_changelist")).status_code, 403)
