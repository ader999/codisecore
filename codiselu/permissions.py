from rest_framework import permissions


class IsAutorOrReadOnly(permissions.BasePermission):
    """
    Permiso que solo permite al autor del objeto (o a un administrador staff) modificarlo o eliminarlo.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        autor = getattr(obj, 'autor', None) or getattr(obj, 'creado_por', None) or getattr(obj, 'creador', None)
        return autor == user


class IsEmpresaAdminOrReadOnly(permissions.BasePermission):
    """
    Permiso para Empresas:
    - Métodos seguros (GET, HEAD, OPTIONS): Permitido a todos.
    - Modificación / Eliminación (PUT, PATCH, DELETE):
      Solo permitido a usuarios autenticados que sean OWNER o ADMIN de la empresa,
      o que sean el creador original (obj.usuario), o usuarios staff.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        if getattr(obj, 'usuario', None) == user:
            return True
        # Verificar membresía con rol OWNER o ADMIN
        if hasattr(obj, 'miembros'):
            return obj.miembros.filter(usuario=user, rol__in=['OWNER', 'ADMIN']).exists()
        return False


class IsEmpresaMemberOrReadOnly(permissions.BasePermission):
    """
    Permiso que permite edición a cualquier miembro activo (OWNER, ADMIN, EDITOR) de la empresa o staff.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        if getattr(obj, 'usuario', None) == user:
            return True
        if hasattr(obj, 'miembros'):
            return obj.miembros.filter(usuario=user, rol__in=['OWNER', 'ADMIN', 'EDITOR']).exists()
        return False


class IsPublicacionAuthorOrCompanyMember(permissions.BasePermission):
    """
    Permiso para Publicaciones:
    - Lectura (GET, HEAD, OPTIONS): Permitido a todos.
    - Edición / Eliminación:
      - Si la publicación es de tipo 'EMPRESA' y tiene empresa asociada:
        Permitido a cualquier miembro con rol (OWNER, ADMIN, EDITOR) de esa empresa,
        o al usuario que creó físicamente la publicación, o staff.
      - Si la publicación es personal ('USUARIO'):
        Solo permitido al usuario creador (creado_por o autor) o staff.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_staff:
            return True

        if getattr(obj, 'tipo_autor', 'USUARIO') == 'EMPRESA' and obj.empresa:
            # Miembro de la empresa
            es_miembro = obj.empresa.miembros.filter(
                usuario=user,
                rol__in=['OWNER', 'ADMIN', 'EDITOR']
            ).exists()
            if es_miembro:
                return True
            if obj.empresa.usuario == user:
                return True

        # Fallback al autor/creador individual
        creador = getattr(obj, 'creado_por', None) or getattr(obj, 'autor', None)
        return creador == user


class IsEventoCreatorOrCompanyMember(permissions.BasePermission):
    """
    Permiso para Eventos:
    - Lectura: Permitido a todos.
    - Edición / Eliminación:
      - Si el evento pertenece a una empresa:
        Permitido a miembros autorizados de la empresa (OWNER, ADMIN, EDITOR) o staff.
      - Si es independiente:
        Permitido al creador del evento o staff.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_staff:
            return True

        if obj.empresa:
            es_miembro = obj.empresa.miembros.filter(
                usuario=user,
                rol__in=['OWNER', 'ADMIN', 'EDITOR']
            ).exists()
            if es_miembro or obj.empresa.usuario == user:
                return True

        return obj.creador == user
