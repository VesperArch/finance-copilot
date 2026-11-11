from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(exc.message_dict if hasattr(exc, "message_dict") else {"non_field_errors": exc.messages})
    if isinstance(exc, ProtectedError):
        return Response({"detail": "Registro em uso. Desative-o para preservar o histórico."}, status=409)
    if isinstance(exc, IntegrityError):
        return Response({"detail": "Conflito de integridade. Revise os dados e tente novamente."}, status=409)
    return drf_exception_handler(exc, context)
