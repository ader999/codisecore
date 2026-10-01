from django.utils.functional import SimpleLazyObject
from .empresa_context import obtener_empresa_activa


class CompanyContextMiddleware:
    """
    Middleware opcional para asociar de manera perezosa (lazy) la empresa activa al request
    si viene el encabezado 'X-Company-Id'.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Exponer funciones o propiedades en el objeto request de Django
        request.get_empresa_activa = lambda: obtener_empresa_activa(request)
        response = self.get_response(request)
        return response
