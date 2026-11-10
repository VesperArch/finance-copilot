import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Role(models.TextChoices):
    ADMIN = "ADMIN", "Administrador"
    OPERATOR = "OPERATOR", "Operador"


class Membership(models.Model):
    financial_space = models.ForeignKey("finance.FinancialSpace", on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField("Papel", max_length=8, choices=Role.choices, default=Role.OPERATOR)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["pk"]
        constraints = [
            models.UniqueConstraint(fields=["financial_space", "user"], name="unique_space_member"),
            models.CheckConstraint(condition=models.Q(role__in=["ADMIN", "OPERATOR"]), name="valid_member_role"),
        ]

    def __str__(self):
        return f"{self.user} · {self.financial_space} · {self.get_role_display()}"


def invitation_expiry():
    return timezone.now() + timedelta(days=7)


class MembershipInvitation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    financial_space = models.ForeignKey("finance.FinancialSpace", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="space_invitations")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_space_invitations")
    role = models.CharField("Papel", max_length=8, choices=Role.choices, default=Role.OPERATOR)
    expires_at = models.DateTimeField(default=invitation_expiry)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(role__in=["ADMIN", "OPERATOR"]), name="valid_invitation_role")]
