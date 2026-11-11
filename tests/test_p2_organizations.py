from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Membership, Role
from apps.accounts.services import accept_invitation, change_member, invite_member
from apps.core.access import SESSION_SPACE_KEY
from apps.finance.models import Account, Category, Transaction
from apps.finance.services.installments import save_transaction
from apps.finance.services.records import save_record
from apps.finance.services.spaces import create_personal_space
from tests.test_finance import FinanceTestCase


class OrganizationTests(FinanceTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.operator = User.objects.create_user("operador", password="Senha-Forte-2026")
        cls.member = Membership.objects.create(user=cls.operator, financial_space=cls.space)

    def setUp(self):
        self.client.force_login(self.user)

    def test_registration_service_creates_admin(self):
        self.assertEqual(Membership.objects.get(user=self.user, financial_space=self.space).role, Role.ADMIN)

    def test_same_organization_shares_lists_and_dashboard(self):
        save_transaction(self.entry(description="Compra compartilhada"))
        self.client.force_login(self.operator)
        self.assertContains(self.client.get(reverse("transaction-list")), "Compra compartilhada")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.context["balance"], self.account.opening_balance - self.entry().amount)
        self.assertNotContains(response, self.other_account.name)

    def test_operator_creates_and_edits_preserving_original_author(self):
        entry = save_transaction(self.entry())
        self.client.force_login(self.operator)
        data = {"description": "Editado", "type": "EXPENSE", "amount": "10", "account": self.account.pk,
                "category": self.category.pk, "date": timezone.localdate().isoformat(), "installments": 1}
        self.assertEqual(self.client.post(reverse("transaction-edit", args=[entry.pk]), data).status_code, 302)
        entry.refresh_from_db()
        self.assertEqual(entry.user_id, self.user.pk)
        self.assertEqual(self.client.post(reverse("transaction-create"), data).status_code, 302)
        self.assertTrue(Transaction.objects.filter(user=self.operator).exists())

    def test_operator_cannot_manage_members_roles_or_settings(self):
        self.client.force_login(self.operator)
        for name, args in [("organization", []), ("member-edit", [self.member.pk])]:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                self.assertEqual(self.client.get(url).status_code, 403)
                self.assertEqual(self.client.post(url, {"role": "ADMIN", "action": "remove"}).status_code, 403)
        with self.assertRaises(PermissionDenied):
            change_member(self.operator, self.space, self.member.pk, role=Role.ADMIN)

    def test_admin_changes_member_and_removes_access_without_history_loss(self):
        entry = save_transaction(self.entry(user=self.operator))
        url = reverse("member-edit", args=[self.member.pk])
        self.assertEqual(self.client.post(url, {"role": "ADMIN"}).status_code, 302)
        self.member.refresh_from_db()
        self.assertEqual(self.member.role, Role.ADMIN)
        self.assertEqual(self.client.post(url, {"role": "ADMIN", "action": "remove"}).status_code, 302)
        self.assertTrue(Transaction.objects.filter(pk=entry.pk, user=self.operator).exists())
        entry.description = "Histórico preservado"
        save_transaction(entry, actor=self.user)
        self.client.force_login(self.operator)
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 403)

    def test_owner_cannot_be_removed_or_demoted(self):
        owner = Membership.objects.get(user=self.user, financial_space=self.space)
        for kwargs in ({"role": Role.OPERATOR}, {"remove": True}):
            with self.assertRaises(ValidationError):
                change_member(self.user, self.space, owner.pk, **kwargs)

    def test_foreign_member_is_hidden(self):
        member = Membership.objects.get(user=self.other, financial_space=self.other_space)
        url = reverse("member-edit", args=[member.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, {"role": "OPERATOR"}).status_code, 404)

    def test_invitation_requires_intended_user_and_explicit_acceptance(self):
        invitation = invite_member(self.user, self.space, self.other.username, Role.OPERATOR)
        url = reverse("invitation-accept", args=[invitation.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertFalse(Membership.objects.filter(user=self.other, financial_space=self.space).exists())
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertTrue(Membership.objects.filter(user=self.other, financial_space=self.space, role=Role.OPERATOR).exists())
        with self.assertRaises(ValidationError):
            accept_invitation(self.other, invitation.pk)

    def test_expired_or_revoked_inviter_cannot_grant_access(self):
        Membership.objects.create(user=self.other, financial_space=self.space, role=Role.ADMIN)
        newcomer = User.objects.create_user("novo")
        invitation = invite_member(self.other, self.space, newcomer.username, Role.OPERATOR)
        invitation.expires_at = timezone.now() - timedelta(seconds=1)
        invitation.save()
        with self.assertRaises(ValidationError):
            accept_invitation(newcomer, invitation.pk)
        invitation.expires_at = timezone.now() + timedelta(days=1)
        invitation.save()
        Membership.objects.filter(user=self.other, financial_space=self.space).update(role=Role.OPERATOR)
        with self.assertRaises(PermissionDenied):
            accept_invitation(newcomer, invitation.pk)

    def test_context_switch_requires_membership_and_post(self):
        url = reverse("space-switch", args=[self.other_space.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url).status_code, 403)
        Membership.objects.create(user=self.user, financial_space=self.other_space)
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertEqual(self.client.session[SESSION_SPACE_KEY], self.other_space.pk)
        self.assertContains(self.client.get(reverse("account-list")), self.other_account.name)
        self.assertNotContains(self.client.get(reverse("account-list")), "Principal")

    def test_revoked_selected_context_is_denied_until_valid_switch(self):
        session = self.client.session
        session[SESSION_SPACE_KEY] = self.other_space.pk
        session.save()
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 403)
        self.assertEqual(self.client.post(reverse("space-switch", args=[self.space.pk])).status_code, 302)
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)

    def test_no_profile_and_superuser_have_controlled_response(self):
        for is_superuser in [False, True]:
            user = User.objects.create_user(f"semperfil{is_superuser}", is_staff=is_superuser, is_superuser=is_superuser)
            self.client.force_login(user)
            self.assertEqual(self.client.get(reverse("dashboard")).status_code, 403)
            if is_superuser:
                self.assertEqual(self.client.get(reverse("admin:index")).status_code, 200)

    def test_unique_member_and_role_constraints(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Membership.objects.create(user=self.operator, financial_space=self.space)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Membership.objects.filter(pk=self.member.pk).update(role="INVALID")

    def test_scope_cannot_be_moved_and_author_cannot_be_changed(self):
        self.account.financial_space = self.other_space
        with self.assertRaises(ValidationError):
            self.account.full_clean()
        self.account.refresh_from_db()
        entry = save_transaction(self.entry())
        entry.user = self.operator
        with self.assertRaises(ValidationError):
            save_transaction(entry)

    def test_names_are_unique_within_scope(self):
        other_account = Account(financial_space=self.other_space, name="Principal")
        other_account.full_clean()
        other_account.save()
        duplicate = Account(financial_space=self.space, name="Principal")
        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_inactive_relations_preserve_existing_history_but_reject_new_links(self):
        entry = save_transaction(self.entry())
        self.account.active = False
        self.account.save()
        entry.description = "Histórico"
        save_transaction(entry)
        with self.assertRaises(ValidationError):
            save_transaction(self.entry())

    def test_csrf_protects_member_operations(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(reverse("member-edit", args=[self.member.pk]), {"role": "ADMIN"}).status_code, 403)

    def test_owner_account_deletion_is_protected(self):
        with self.assertRaises(ProtectedError):
            self.user.delete()
        self.assertTrue(Account.objects.filter(pk=self.account.pk).exists())
        self.assertTrue(Membership.objects.filter(user=self.user, financial_space=self.space, role=Role.ADMIN).exists())

    def test_financial_services_reject_actor_without_membership(self):
        with self.assertRaises(PermissionDenied):
            save_transaction(self.entry(), actor=self.other)
        with self.assertRaises(PermissionDenied):
            save_record(Account(financial_space=self.space, name="Acesso indevido"), self.other)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_superuser_cannot_bypass_membership_rules_through_admin(self):
        root = User.objects.create_superuser("root-admin", "root@example.com", "Senha-Forte-2026")
        self.client.force_login(root)
        for app, model in [("accounts", "membership"), ("accounts", "membershipinvitation"), ("finance", "financialspace")]:
            self.assertEqual(self.client.get(reverse(f"admin:{app}_{model}_add")).status_code, 403)
        url = reverse("admin:accounts_membership_change", args=[self.member.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.post(url, {"role": "ADMIN"}).status_code, 403)
