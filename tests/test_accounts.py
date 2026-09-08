from django.contrib.auth.models import User
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.finance.models import Category, FinancialSpace


class AuthenticationTests(TestCase):
    def test_signup_creates_space_and_categories_and_logs_in(self):
        response = self.client.post(reverse("signup"), {"first_name": "Clara", "username": "clara", "email": "clara@example.com", "password1": "MinhaSenha-Forte-2026", "password2": "MinhaSenha-Forte-2026"})
        self.assertRedirects(response, reverse("account-create"))
        self.assertEqual(FinancialSpace.objects.count(), 1)
        self.assertEqual(Category.objects.count(), 18)
        self.assertIn("_auth_user_id", self.client.session)

    def test_login_logout_and_page_protection(self):
        User.objects.create_user("clara", password="MinhaSenha-Forte-2026")
        response = self.client.post(reverse("login"), {"username": "clara", "password": "MinhaSenha-Forte-2026"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get(reverse("password_change")).status_code, 200)
        self.assertEqual(self.client.get(reverse("password_change_done")).status_code, 200)
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        self.assertEqual(self.client.post(reverse("logout")).status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 302)

    def test_csrf_protects_signup(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(reverse("signup"), {}).status_code, 403)

    def test_weak_password_is_rejected(self):
        response = self.client.post(reverse("signup"), {"first_name": "Clara", "username": "clara", "email": "clara@example.com", "password1": "123", "password2": "123"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.exists())

    def test_login_does_not_redirect_to_external_site(self):
        User.objects.create_user("clara", password="MinhaSenha-Forte-2026")
        response = self.client.post(reverse("login"), {"username": "clara", "password": "MinhaSenha-Forte-2026", "next": "https://example.com"})
        self.assertEqual(response.url, reverse("dashboard"))

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_password_reset_sends_link(self):
        User.objects.create_user("clara", "clara@example.com", "MinhaSenha-Forte-2026")
        response = self.client.post(reverse("password_reset"), {"email": "clara@example.com"})
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/acesso/reset/", mail.outbox[0].body)

    def test_public_authentication_pages_render(self):
        for name in ("login", "signup", "password_reset", "password_reset_done", "password_reset_complete"):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)
