from django.contrib import admin
from django.urls import include, path

from apps.accounts.views import signup
from apps.finance import views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("acesso/cadastro/", signup, name="signup"),
    path("acesso/", include("django.contrib.auth.urls")),
    path("", views.dashboard, name="dashboard"),
    path("parcelas/<int:pk>/", views.installment_detail, name="installment-detail"),
    path("parcelas/<int:pk>/excluir/", views.installment_delete, name="installment-delete"),
]

for kind, route in [("account", "contas"), ("category", "categorias"), ("transaction", "movimentacoes"), ("budget", "planejamento")]:
    urlpatterns += [
        path(f"{route}/", views.resource_list, {"kind": kind}, name=f"{kind}-list"),
        path(f"{route}/adicionar/", views.resource_edit, {"kind": kind}, name=f"{kind}-create"),
        path(f"{route}/<int:pk>/editar/", views.resource_edit, {"kind": kind}, name=f"{kind}-edit"),
        path(f"{route}/<int:pk>/excluir/", views.resource_delete, {"kind": kind}, name=f"{kind}-delete"),
    ]
