from django.http import Http404


def personal_space(user):
    space = user.financial_spaces.order_by("pk").first()
    if space is None:
        raise Http404("Espaço financeiro não encontrado. Faça seu cadastro para começar.")
    return space
