from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

from apps.budgets.models import Budget
from apps.finance.models import Account, Category, Transaction
from tests.test_finance import FinanceTestCase


class UserJourneyTests(FinanceTestCase):
    def setUp(self):
        self.client.force_login(self.user)

    def test_create_edit_and_delete_account(self):
        response = self.client.post(reverse("account-create"), {"name": "Carteira", "type": "WALLET", "opening_balance": "123,45", "active": "on"})
        self.assertRedirects(response, reverse("account-list"))
        account = Account.objects.get(name="Carteira", financial_space=self.space)
        self.assertEqual(account.opening_balance, Decimal("123.45"))
        response = self.client.post(reverse("account-edit", args=[account.pk]), {"name": "Dinheiro", "type": "WALLET", "opening_balance": "200", "active": "on"})
        self.assertRedirects(response, reverse("account-list"))
        account.refresh_from_db()
        self.assertEqual(account.name, "Dinheiro")
        self.client.post(reverse("account-delete", args=[account.pk]))
        self.assertFalse(Account.objects.filter(pk=account.pk).exists())

    def test_create_edit_and_delete_category(self):
        self.client.post(reverse("category-create"), {"name": "Pets", "type": "EXPENSE", "active": "on"})
        category = Category.objects.get(name="Pets", financial_space=self.space)
        self.client.post(reverse("category-edit", args=[category.pk]), {"name": "Animais", "type": "EXPENSE"})
        category.refresh_from_db()
        self.assertEqual(category.name, "Animais")
        self.assertFalse(category.active)
        self.client.post(reverse("category-delete", args=[category.pk]))
        self.assertFalse(Category.objects.filter(pk=category.pk).exists())

    def test_create_edit_and_delete_transaction(self):
        data = {"description": "Almoço", "amount": "42,90", "type": "EXPENSE", "account": self.account.pk, "category": self.category.pk, "date": timezone.localdate().isoformat(), "installments": "1"}
        response = self.client.post(reverse("transaction-create"), data)
        self.assertRedirects(response, reverse("transaction-list"))
        entry = Transaction.objects.get(description="Almoço")
        data.update(amount="50,00", description="Jantar")
        self.assertRedirects(self.client.post(reverse("transaction-edit", args=[entry.pk]), data), reverse("transaction-list"))
        entry.refresh_from_db()
        self.assertEqual(entry.amount, Decimal("50.00"))
        self.assertEqual(entry.description, "Jantar")
        self.client.post(reverse("transaction-delete", args=[entry.pk]))
        self.assertFalse(Transaction.objects.exists())

    def test_create_edit_and_delete_budget(self):
        today = timezone.localdate()
        data = {"category": self.category.pk, "month": today.month, "year": today.year, "limit_amount": "500,00", "alert_threshold": "75"}
        self.assertRedirects(self.client.post(reverse("budget-create"), data), reverse("budget-list"))
        budget = Budget.objects.get(financial_space=self.space)
        data["limit_amount"] = "600,00"
        self.assertRedirects(self.client.post(reverse("budget-edit", args=[budget.pk]), data), reverse("budget-list"))
        budget.refresh_from_db()
        self.assertEqual(budget.limit_amount, Decimal("600.00"))
        self.client.post(reverse("budget-delete", args=[budget.pk]))
        self.assertFalse(Budget.objects.exists())

    def test_purchase_form_creates_navigable_schedule(self):
        data = {"description": "Notebook", "amount": "3000", "type": "EXPENSE", "account": self.account.pk, "category": self.category.pk, "date": "2026-09-30", "installments": "10"}
        response = self.client.post(reverse("transaction-create"), data, follow=True)
        self.assertContains(response, "Parcela 10 de 10")
        self.assertContains(response, "30/06/2027")
        self.assertEqual(Transaction.objects.count(), 10)

    def test_invalid_small_installments_preserve_form(self):
        response = self.client.post(reverse("transaction-create"), {"description": "Compra pequena", "amount": "0,01", "type": "EXPENSE", "account": self.account.pk, "category": self.category.pk, "date": "2026-09-30", "installments": "10"})
        self.assertContains(response, "pelo menos R$ 0,01")
        self.assertContains(response, "Compra pequena")
        self.assertFalse(Transaction.objects.exists())
