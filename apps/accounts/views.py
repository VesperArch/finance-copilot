from django.contrib import messages
from django.contrib.auth import login
from django.db import transaction
from django.shortcuts import redirect, render

from apps.accounts.forms import SignupForm
from apps.finance.services.spaces import create_personal_space


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = SignupForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            user = form.save()
            create_personal_space(user)
        login(request, user)
        messages.success(request, "Tudo pronto! Adicione sua primeira conta para começar.")
        return redirect("account-create")
    return render(request, "registration/signup.html", {"form": form})
