import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('finance', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Budget',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('month', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(12)], verbose_name='Mês')),
                ('year', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1900), django.core.validators.MaxValueValidator(9999)], verbose_name='Ano')),
                ('limit_amount', models.DecimalField(decimal_places=2, max_digits=14, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], verbose_name='Limite mensal')),
                ('alert_threshold', models.PositiveSmallIntegerField(default=75, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)], verbose_name='Alertar a partir de (%)')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='finance.category', verbose_name='Categoria')),
                ('financial_space', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='finance.financialspace')),
            ],
            options={
                'verbose_name': 'Orçamento',
                'verbose_name_plural': 'Orçamentos',
                'ordering': ['-year', '-month', 'category__name'],
                'constraints': [models.UniqueConstraint(fields=('financial_space', 'category', 'year', 'month'), name='unique_monthly_budget', violation_error_message='Já existe um orçamento para esta categoria neste mês.'), models.CheckConstraint(condition=models.Q(('month__gte', 1), ('month__lte', 12)), name='valid_budget_month'), models.CheckConstraint(condition=models.Q(('year__gte', 1900), ('year__lte', 9999)), name='valid_budget_year'), models.CheckConstraint(condition=models.Q(('limit_amount__gt', 0)), name='positive_budget_limit'), models.CheckConstraint(condition=models.Q(('alert_threshold__gte', 1), ('alert_threshold__lte', 100)), name='valid_budget_alert')],
            },
        ),
    ]
