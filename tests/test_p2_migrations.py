from datetime import date
from decimal import Decimal

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class LegacyMigrationTests(TransactionTestCase):
    """Exercise historical models on the disposable test database only."""

    def test_p1_records_ids_and_multiple_spaces_survive_migration(self):
        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes()
        before = [("accounts", None), ("finance", "0001_initial"), ("budgets", "0001_initial")]
        try:
            executor.migrate(before)
            apps = executor.loader.project_state([("finance", "0001_initial"), ("budgets", "0001_initial")]).apps
            User = apps.get_model("auth", "User")
            Space = apps.get_model("finance", "FinancialSpace")
            Account = apps.get_model("finance", "Account")
            Category = apps.get_model("finance", "Category")
            Transaction = apps.get_model("finance", "Transaction")
            Group = apps.get_model("finance", "InstallmentGroup")
            Parcela = apps.get_model("finance", "Parcela")
            Budget = apps.get_model("budgets", "Budget")
            owner = User.objects.create(username="legado")
            other = User.objects.create(username="outro-legado")
            spaces = [Space.objects.create(owner=owner, name="Pessoal"), Space.objects.create(owner=owner, name="Segundo"), Space.objects.create(owner=other, name="Outra organização")]
            account = Account.objects.create(financial_space=spaces[0], name="Legada", active=False, opening_balance=Decimal("123.45"))
            category = Category.objects.create(financial_space=spaces[0], name="Histórico", type="EXPENSE", active=False)
            group = Group.objects.create(financial_space=spaces[0], description="Compra", total_amount=Decimal("100.00"), count=2, first_date=date(2028, 1, 31))
            ids = []
            for i, due in enumerate([date(2028, 1, 31), date(2028, 2, 29)], 1):
                entry = Transaction.objects.create(financial_space=spaces[0], user=owner, account=account, category=category, type="EXPENSE", description="Histórico", amount=Decimal("50.00"), date=due, installment_group=group)
                ids.append(entry.pk)
                Parcela.objects.create(transaction=entry, group=group, number=i)
            budget = Budget.objects.create(financial_space=spaces[0], category=category, month=1, year=2028, limit_amount=Decimal("200.00"))
            executor = MigrationExecutor(connection)
            executor.migrate(latest)
            apps = executor.loader.project_state(latest).apps
            Member = apps.get_model("accounts", "Membership")
            self.assertEqual(Member.objects.count(), 3)
            for space in spaces:
                self.assertTrue(Member.objects.filter(financial_space_id=space.pk, user_id=space.owner_id, role="ADMIN").exists())
            moved = apps.get_model("finance", "Transaction").objects.filter(pk__in=ids).order_by("pk")
            self.assertEqual([e.amount for e in moved], [Decimal("50.00"), Decimal("50.00")])
            self.assertEqual([e.date for e in moved], [date(2028, 1, 31), date(2028, 2, 29)])
            self.assertTrue(all(e.financial_space_id == spaces[0].pk and e.account_id == account.pk and e.installment_group_id == group.pk for e in moved))
            self.assertEqual(apps.get_model("finance", "Account").objects.get(pk=account.pk).opening_balance, Decimal("123.45"))
            self.assertFalse(apps.get_model("finance", "Category").objects.get(pk=category.pk).active)
            self.assertEqual(apps.get_model("finance", "Parcela").objects.count(), 2)
            self.assertEqual(apps.get_model("budgets", "Budget").objects.get(pk=budget.pk).category_id, category.pk)
            # Re-running the data migration is idempotent.
            from importlib import import_module
            with connection.schema_editor() as editor:
                import_module("apps.accounts.migrations.0002_legacy_memberships").migrate_owners(apps, editor)
            self.assertEqual(Member.objects.count(), 3)
        finally:
            MigrationExecutor(connection).migrate(latest)
