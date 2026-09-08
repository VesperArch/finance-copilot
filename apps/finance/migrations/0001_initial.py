import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FinancialSpace',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Pessoal', max_length=100, verbose_name='Nome')),
                ('currency', models.CharField(default='BRL', editable=False, max_length=3, verbose_name='Moeda')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='financial_spaces', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Espaço financeiro',
                'verbose_name_plural': 'Espaços financeiros',
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=80, verbose_name='Nome')),
                ('type', models.CharField(choices=[('INCOME', 'Entrada'), ('EXPENSE', 'Gasto')], default='EXPENSE', max_length=7, verbose_name='Tipo')),
                ('active', models.BooleanField(default=True, verbose_name='Ativa')),
                ('financial_space', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='finance.financialspace')),
            ],
            options={
                'verbose_name': 'Categoria',
                'verbose_name_plural': 'Categorias',
                'ordering': ['type', 'name', 'pk'],
            },
        ),
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100, verbose_name='Nome')),
                ('type', models.CharField(choices=[('CHECKING', 'Conta corrente'), ('WALLET', 'Carteira'), ('SAVINGS', 'Poupança'), ('CARD', 'Cartão'), ('DIGITAL', 'Conta digital')], default='CHECKING', max_length=10, verbose_name='Tipo')),
                ('institution', models.CharField(blank=True, max_length=100, verbose_name='Instituição')),
                ('opening_balance', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=14, verbose_name='Saldo inicial')),
                ('active', models.BooleanField(default=True, verbose_name='Ativa')),
                ('financial_space', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='finance.financialspace')),
            ],
            options={
                'verbose_name': 'Conta',
                'verbose_name_plural': 'Contas',
                'ordering': ['name', 'pk'],
            },
        ),
        migrations.CreateModel(
            name='InstallmentGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('description', models.CharField(max_length=160, verbose_name='Compra')),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=14, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], verbose_name='Valor total')),
                ('count', models.PositiveSmallIntegerField(verbose_name='Quantidade')),
                ('first_date', models.DateField(verbose_name='Primeiro vencimento')),
                ('financial_space', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='finance.financialspace')),
            ],
            options={
                'verbose_name': 'Compra parcelada',
                'verbose_name_plural': 'Compras parceladas',
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('type', models.CharField(choices=[('INCOME', 'Entrada'), ('EXPENSE', 'Gasto'), ('TRANSFER', 'Transferência')], default='EXPENSE', max_length=8, verbose_name='Tipo')),
                ('description', models.CharField(max_length=160, verbose_name='Descrição')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=14, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], verbose_name='Valor')),
                ('date', models.DateField(default=django.utils.timezone.localdate, verbose_name='Data')),
                ('notes', models.TextField(blank=True, max_length=2000, verbose_name='Observações')),
                ('source', models.CharField(choices=[('MANUAL', 'Manual'), ('CSV', 'CSV'), ('OFX', 'OFX'), ('RECEIPT', 'Comprovante'), ('API', 'API')], default='MANUAL', editable=False, max_length=7)),
                ('recurring', models.BooleanField(default=False, editable=False)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transactions', to='finance.account', verbose_name='Conta')),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='finance.category', verbose_name='Categoria')),
                ('destination_account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='incoming_transfers', to='finance.account', verbose_name='Conta de destino')),
                ('financial_space', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='finance.financialspace')),
                ('installment_group', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='finance.installmentgroup')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Lançamento',
                'verbose_name_plural': 'Lançamentos',
                'ordering': ['-date', '-pk'],
            },
        ),
        migrations.CreateModel(
            name='Parcela',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveSmallIntegerField(verbose_name='Número')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='installments', to='finance.installmentgroup', verbose_name='Compra')),
                ('transaction', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='installment', to='finance.transaction', verbose_name='Lançamento')),
            ],
            options={
                'verbose_name': 'Parcela',
                'verbose_name_plural': 'Parcelas',
                'ordering': ['number'],
            },
        ),
        migrations.AddConstraint(
            model_name='category',
            constraint=models.UniqueConstraint(fields=('financial_space', 'name', 'type'), name='unique_category_name'),
        ),
        migrations.AddConstraint(
            model_name='account',
            constraint=models.UniqueConstraint(fields=('financial_space', 'name'), name='unique_account_name'),
        ),
        migrations.AddConstraint(
            model_name='installmentgroup',
            constraint=models.CheckConstraint(condition=models.Q(('total_amount__gt', 0)), name='positive_purchase_total'),
        ),
        migrations.AddConstraint(
            model_name='installmentgroup',
            constraint=models.CheckConstraint(condition=models.Q(('count__gte', 2), ('count__lte', 120)), name='valid_installment_count'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['financial_space', 'date'], name='finance_tra_financi_4f1a49_idx'),
        ),
        migrations.AddConstraint(
            model_name='transaction',
            constraint=models.CheckConstraint(condition=models.Q(('amount__gt', 0)), name='positive_transaction_amount'),
        ),
        migrations.AddConstraint(
            model_name='transaction',
            constraint=models.CheckConstraint(condition=models.Q(models.Q(('category__isnull', True), ('destination_account__isnull', False), ('type', 'TRANSFER'), models.Q(('account', models.F('destination_account')), _negated=True)), models.Q(('category__isnull', False), ('destination_account__isnull', True), ('type__in', ['INCOME', 'EXPENSE'])), _connector='OR'), name='valid_transaction_kind'),
        ),
        migrations.AddConstraint(
            model_name='parcela',
            constraint=models.UniqueConstraint(fields=('group', 'number'), name='unique_installment_number'),
        ),
        migrations.AddConstraint(
            model_name='parcela',
            constraint=models.CheckConstraint(condition=models.Q(('number__gte', 1)), name='positive_installment_number'),
        ),
    ]
