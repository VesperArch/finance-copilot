import apps.accounts.models
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('finance', '0002_alter_financialspace_owner'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('ADMIN', 'Administrador'), ('OPERATOR', 'Operador')], default='OPERATOR', max_length=8, verbose_name='Papel')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('financial_space', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='finance.financialspace')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['pk'],
                'constraints': [models.UniqueConstraint(fields=('financial_space', 'user'), name='unique_space_member'), models.CheckConstraint(condition=models.Q(('role__in', ['ADMIN', 'OPERATOR'])), name='valid_member_role')],
            },
        ),
        migrations.CreateModel(
            name='MembershipInvitation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('role', models.CharField(choices=[('ADMIN', 'Administrador'), ('OPERATOR', 'Operador')], default='OPERATOR', max_length=8, verbose_name='Papel')),
                ('expires_at', models.DateTimeField(default=apps.accounts.models.invitation_expiry)),
                ('accepted_at', models.DateTimeField(blank=True, null=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_space_invitations', to=settings.AUTH_USER_MODEL)),
                ('financial_space', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='finance.financialspace')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='space_invitations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'constraints': [models.CheckConstraint(condition=models.Q(('role__in', ['ADMIN', 'OPERATOR'])), name='valid_invitation_role')],
            },
        ),
    ]
