from django.db import transaction

from apps.finance.models import Category, FinancialSpace


DEFAULT_CATEGORIES = {
    Category.Type.INCOME: ["Salário", "Freelance", "Rendimentos", "Reembolso", "Outros"],
    Category.Type.EXPENSE: ["Alimentação", "Mercado", "Moradia", "Transporte", "Saúde", "Educação", "Lazer", "Compras", "Assinaturas", "Contas", "Viagem", "Dívidas", "Outros"],
}


@transaction.atomic
def create_personal_space(user):
    space = FinancialSpace.objects.create(owner=user)
    Category.objects.bulk_create([
        Category(financial_space=space, name=name, type=kind)
        for kind, names in DEFAULT_CATEGORIES.items() for name in names
    ])
    return space
