import logging
from rest_framework.exceptions import PermissionDenied, ValidationError

logger = logging.getLogger(__name__)


def obtener_empresa_activa(request):
    """
    Detecta el contexto de empresa activa a partir del encabezado HTTP 'X-Company-Id'.
    - Si el encabezado NO está presente: retorna None (modo perfil personal).
    - Si el encabezado está presente:
        * Requiere que request.user esté autenticado.
        * Valida que el ID sea un entero positivo.
        * Valida que request.user sea miembro de la empresa (o administrador staff / creador).
        * Si es válido, asocia `request.empresa_activa` y `request.rol_empresa_activa`.
        * Si no es miembro o la empresa no existe, lanza PermissionDenied.
    """
    if hasattr(request, '_empresa_activa_cache'):
        return request._empresa_activa_cache

    header_val = None
    if hasattr(request, 'headers'):
        header_val = request.headers.get('X-Company-Id')
    if not header_val and hasattr(request, 'META'):
        header_val = request.META.get('HTTP_X_COMPANY_ID')

    if not header_val or str(header_val).strip() == '':
        request.empresa_activa = None
        request.rol_empresa_activa = None
        request._empresa_activa_cache = None
        return None

    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        raise PermissionDenied("Se requiere autenticación para operar en el contexto de una empresa.")

    try:
        company_id = int(str(header_val).strip())
        if company_id <= 0:
            raise ValueError
    except (ValueError, TypeError):
        raise ValidationError({"detail": "El encabezado X-Company-Id debe ser un ID numérico válido mayor a 0."})

    from .models import Empresa, EmpresaMiembro

    # Buscar membresía activa
    miembro = EmpresaMiembro.objects.select_related('empresa').filter(
        empresa_id=company_id,
        usuario=user
    ).first()

    if miembro:
        request.empresa_activa = miembro.empresa
        request.rol_empresa_activa = miembro.rol
        request._empresa_activa_cache = miembro.empresa
        return miembro.empresa

    # Soporte para creador original (retrocompatibilidad)
    empresa = Empresa.objects.filter(id=company_id).first()
    if not empresa:
        raise PermissionDenied("La empresa especificada en X-Company-Id no existe.")

    if empresa.usuario == user:
        miembro, _ = EmpresaMiembro.objects.get_or_create(
            empresa=empresa,
            usuario=user,
            defaults={'rol': EmpresaMiembro.ROL_OWNER}
        )
        request.empresa_activa = empresa
        request.rol_empresa_activa = miembro.rol
        request._empresa_activa_cache = empresa
        return empresa

    # Administradores de plataforma (staff)
    if user.is_staff:
        request.empresa_activa = empresa
        request.rol_empresa_activa = EmpresaMiembro.ROL_OWNER
        request._empresa_activa_cache = empresa
        return empresa

    raise PermissionDenied("No tienes permisos para operar en nombre de la empresa especificada en X-Company-Id.")


class CompanyContextMixin:
    """
    Mixin para ViewSets de Django REST Framework que habilita la detección automática
    del contexto de empresa activa mediante 'X-Company-Id'.
    """
    @property
    def empresa_activa(self):
        return obtener_empresa_activa(self.request)

    @property
    def rol_empresa_activa(self):
        obtener_empresa_activa(self.request)
        return getattr(self.request, 'rol_empresa_activa', None)

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        # Pre-evaluar contexto si el encabezado viene en la petición
        header_val = None
        if hasattr(request, 'headers'):
            header_val = request.headers.get('X-Company-Id')
        if not header_val and hasattr(request, 'META'):
            header_val = request.META.get('HTTP_X_COMPANY_ID')
        if header_val:
            obtener_empresa_activa(request)
