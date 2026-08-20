from django.db import models
from rest_framework import viewsets, permissions, status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import action
from .models import (
    User, Ciudad, CircuitoCreativo, PuntoInteres, DatoHistorico,
    GaleriaMultimedia, UsuarioPuntoVisitado, Empresa, OportunidadInversion,
    InversionTurista, Evento, EventoAsistencia, Publicacion, PublicacionImagen,
    ComentarioPublicacion
)
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    CiudadSerializer,
    CircuitoCreativoSerializer,
    PuntoInteresSerializer,
    DatoHistoricoSerializer,
    GaleriaMultimediaSerializer,
    UsuarioPuntoVisitadoSerializer,
    EmpresaSerializer,
    OportunidadInversionSerializer,
    InversionTuristaSerializer,
    EventoSerializer,
    PublicacionSerializer,
    PublicacionImagenSerializer,
    ComentarioPublicacionSerializer
)


class IsAutorOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado que solo permite al autor del objeto (o a un administrador) modificarlo o eliminarlo.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return hasattr(obj, 'autor') and (obj.autor == request.user or (request.user and request.user.is_staff))



class RegisterView(generics.CreateAPIView):
    """
    Endpoint para registrar un nuevo usuario.
    Retorna los datos del usuario creado y sus tokens JWT (access y refresh).
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        user_data = UserSerializer(user, context=self.get_serializer_context()).data

        return Response({
            'message': 'Usuario registrado exitosamente.',
            'user': user_data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    Endpoint para iniciar sesión.
    Acepta username (o correo) y password. Retorna tokens JWT y datos del usuario.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        user_data = UserSerializer(user, context={'request': request}).data

        return Response({
            'message': 'Inicio de sesión exitoso.',
            'user': user_data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Endpoint para obtener y actualizar el perfil del usuario autenticado actual.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


class CiudadViewSet(viewsets.ModelViewSet):
    queryset = Ciudad.objects.all().order_by('id')
    serializer_class = CiudadSerializer
    permission_classes = [permissions.AllowAny]


class CircuitoCreativoViewSet(viewsets.ModelViewSet):
    queryset = CircuitoCreativo.objects.all().order_by('id')
    serializer_class = CircuitoCreativoSerializer
    permission_classes = [permissions.AllowAny]


class PuntoInteresViewSet(viewsets.ModelViewSet):
    queryset = PuntoInteres.objects.all().order_by('orden')
    serializer_class = PuntoInteresSerializer
    permission_classes = [permissions.AllowAny]


class DatoHistoricoViewSet(viewsets.ModelViewSet):
    queryset = DatoHistorico.objects.all().order_by('id')
    serializer_class = DatoHistoricoSerializer
    permission_classes = [permissions.AllowAny]


class GaleriaMultimediaViewSet(viewsets.ModelViewSet):
    queryset = GaleriaMultimedia.objects.all().order_by('id')
    serializer_class = GaleriaMultimediaSerializer
    permission_classes = [permissions.AllowAny]


class VisitaViewSet(viewsets.ModelViewSet):
    """
    Endpoint para registrar y consultar las visitas del usuario autenticado.
    - POST /api/visitas/ -> Guarda una visita para el usuario actual. Body: {"punto_interes_id": 1}
    - GET /api/visitas/ -> Lista completa de visitas del usuario autenticado.
    - GET /api/visitas/ids/ -> Lista array simple de IDs de los puntos de interés visitados por el usuario.
    """
    serializer_class = UsuarioPuntoVisitadoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return UsuarioPuntoVisitado.objects.all().order_by('-fecha_visita')
        return UsuarioPuntoVisitado.objects.filter(usuario=user).order_by('-fecha_visita')

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        # Soporte para parametro query ?ids_only=true o ?only_ids=true
        if request.query_params.get('ids_only') == 'true' or request.query_params.get('only_ids') == 'true':
            ids = list(queryset.values_list('punto_interes_id', flat=True))
            return Response(ids)

        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='ids')
    def obtener_ids_visitados(self, request):
        """
        Retorna la lista directa de IDs de los puntos de interés recorridos por el usuario autenticado.
        Ejemplo respuesta: [1, 5, 8]
        """
        queryset = self.get_queryset()
        ids = list(queryset.values_list('punto_interes_id', flat=True))
        return Response(ids)


class EmpresaViewSet(viewsets.ModelViewSet):
    """
    Endpoint para consultar y administrar Empresas y Destinos Turísticos.
    - Lectura (GET): Pública para cualquier usuario/turista.
    - Creación / Edición (POST/PUT/DELETE): Requiere autenticación.
    """
    queryset = Empresa.objects.all().order_by('-fecha_creacion')
    serializer_class = EmpresaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        acepta_inv = self.request.query_params.get('acepta_inversiones')
        if acepta_inv is not None:
            if acepta_inv.lower() in ['true', '1']:
                queryset = queryset.filter(acepta_inversiones=True)
            elif acepta_inv.lower() in ['false', '0']:
                queryset = queryset.filter(acepta_inversiones=False)
        usuario_id = self.request.query_params.get('usuario')
        if usuario_id:
            queryset = queryset.filter(usuario_id=usuario_id)
        ciudad_id = self.request.query_params.get('ciudad')
        if ciudad_id:
            queryset = queryset.filter(ciudad_id=ciudad_id)
        return queryset


class OportunidadInversionViewSet(viewsets.ModelViewSet):
    """
    Endpoint para oportunidades de inversión publicadas por empresas.
    Solo muestra y permite crear oportunidades en empresas que aceptan inversión.
    """
    queryset = OportunidadInversion.objects.filter(empresa__acepta_inversiones=True, esta_activa=True).order_by('-fecha_publicacion')
    serializer_class = OportunidadInversionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        empresa_id = self.request.query_params.get('empresa')
        if empresa_id:
            queryset = queryset.filter(empresa_id=empresa_id)
        tipo_inversor = self.request.query_params.get('tipo_inversor')
        if tipo_inversor:
            queryset = queryset.filter(tipo_inversor_permitido__in=['Todos', tipo_inversor])
        return queryset


class InversionTuristaViewSet(viewsets.ModelViewSet):
    """
    Endpoint para registrar e inspeccionar solicitudes de inversión realizadas por turistas.
    - POST: Permite a turistas autenticados enviar su intención/monto de inversión.
    - GET: Retorna las inversiones enviadas por el usuario actual o las recibidas por las empresas del usuario protagonista.
    """
    serializer_class = InversionTuristaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return InversionTurista.objects.all().order_by('-fecha_solicitud')
        return InversionTurista.objects.filter(
            models.Q(inversionista=user) | models.Q(oportunidad__empresa__usuario=user)
        ).distinct().order_by('-fecha_solicitud')

    def perform_create(self, serializer):
        serializer.save(inversionista=self.request.user)


class EventoViewSet(viewsets.ModelViewSet):
    """
    Endpoint para consultar y registrar eventos creados por protagonistas, empresas o administradores.
    - Los administradores (staff) pueden registrar eventos oficiales de las ciudades.
    - Soporta filtrado por mural de publicación (?en_mural=true o ?mural=true) y eventos oficiales (?es_oficial=true).
    """
    queryset = Evento.objects.filter(esta_activo=True).order_by('-fecha_inicio')
    serializer_class = EventoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        user = self.request.user
        es_oficial_data = serializer.validated_data.get('es_oficial', None)
        if es_oficial_data is None:
            es_oficial = user.is_staff
        else:
            es_oficial = es_oficial_data if user.is_staff else False
        serializer.save(creador=user, es_oficial=es_oficial)

    def get_queryset(self):
        from django.utils import timezone

        queryset = Evento.objects.all().order_by('-fecha_inicio')
        if not self.request.user.is_staff:
            queryset = queryset.filter(esta_activo=True)

        ciudad_id = self.request.query_params.get('ciudad')
        if ciudad_id:
            queryset = queryset.filter(ciudad_id=ciudad_id)

        empresa_id = self.request.query_params.get('empresa')
        if empresa_id:
            queryset = queryset.filter(empresa_id=empresa_id)

        es_oficial = self.request.query_params.get('es_oficial') or self.request.query_params.get('solo_oficiales')
        if es_oficial is not None:
            if es_oficial.lower() in ['true', '1']:
                queryset = queryset.filter(es_oficial=True)
            elif es_oficial.lower() in ['false', '0']:
                queryset = queryset.filter(es_oficial=False)

        en_mural = self.request.query_params.get('en_mural') or self.request.query_params.get('mural')
        if en_mural is not None and en_mural.lower() in ['true', '1']:
            mural_ids = [e.id for e in queryset if e.en_mural]
            queryset = queryset.filter(id__in=mural_ids)

        return queryset

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated], url_path='grano-cafe')
    def grano_cafe(self, request, pk=None):
        """
        Endpoint para alternar (toggle) la reacción de grano de café en un evento.
        POST /api/eventos/{id}/grano-cafe/
        """
        evento = self.get_object()
        user = request.user
        if evento.granos_cafe.filter(id=user.id).exists():
            evento.granos_cafe.remove(user)
            ha_dado_grano = False
            mensaje = "Reacción de grano de café eliminada del evento."
        else:
            evento.granos_cafe.add(user)
            ha_dado_grano = True
            mensaje = "Reacción de grano de café agregada al evento."
        return Response({
            'message': mensaje,
            'ha_dado_grano_cafe': ha_dado_grano,
            'total_granos_cafe': evento.total_granos_cafe
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated], url_path='asistir')
    def asistir(self, request, pk=None):
        """
        Endpoint para alternar (toggle) la asistencia a un evento.
        POST /api/eventos/{id}/asistir/
        """
        evento = self.get_object()
        user = request.user
        asistencia, created = EventoAsistencia.objects.get_or_create(usuario=user, evento=evento)
        if not created:
            asistencia.delete()
            va_a_asistir = False
            mensaje = "Has cancelado tu asistencia al evento."
        else:
            va_a_asistir = True
            mensaje = "Has registrado tu asistencia al evento."
        return Response({
            'message': mensaje,
            'va_a_asistir': va_a_asistir,
            'total_asistentes': evento.total_asistentes
        }, status=status.HTTP_200_OK)


class PublicacionViewSet(viewsets.ModelViewSet):
    """
    Endpoint para consultar y crear publicaciones de turistas y protagonistas/empresas.
    - Soporta la subida de múltiples imágenes secundarias mediante el parámetro FILES 'imagenes'.
    - Reacción de me gusta mediante POST /api/publicaciones/{id}/like/
    """
    queryset = Publicacion.objects.filter(esta_activa=True).order_by('-fecha_creacion')
    serializer_class = PublicacionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        publicacion = serializer.save(autor=self.request.user)
        imagenes = self.request.FILES.getlist('imagenes')
        for img in imagenes:
            PublicacionImagen.objects.create(publicacion=publicacion, imagen=img)

    def get_queryset(self):
        queryset = Publicacion.objects.all().order_by('-fecha_creacion')
        if not (self.request.user and self.request.user.is_staff):
            queryset = queryset.filter(esta_activa=True)

        ciudad_id = self.request.query_params.get('ciudad')
        if ciudad_id:
            queryset = queryset.filter(ciudad_id=ciudad_id)

        empresa_id = self.request.query_params.get('empresa')
        if empresa_id:
            queryset = queryset.filter(empresa_id=empresa_id)

        evento_id = self.request.query_params.get('evento')
        if evento_id:
            queryset = queryset.filter(evento_id=evento_id)

        autor_id = self.request.query_params.get('autor')
        if autor_id:
            queryset = queryset.filter(autor_id=autor_id)

        return queryset

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated], url_path='like')
    def toggle_like(self, request, pk=None):
        """
        Endpoint para alternar (toggle) el like en una publicación.
        POST /api/publicaciones/{id}/like/
        """
        publicacion = self.get_object()
        user = request.user
        if publicacion.likes.filter(id=user.id).exists():
            publicacion.likes.remove(user)
            ha_dado_like = False
            mensaje = "Like eliminado de la publicación."
        else:
            publicacion.likes.add(user)
            ha_dado_like = True
            mensaje = "Like agregado a la publicación."
        return Response({
            'message': mensaje,
            'ha_dado_like': ha_dado_like,
            'total_likes': publicacion.total_likes
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get', 'post'], permission_classes=[permissions.IsAuthenticatedOrReadOnly], url_path='comentarios')
    def comentarios(self, request, pk=None):
        """
        Endpoint para listar (GET) y agregar (POST) comentarios a una publicación específica.
        GET /api/publicaciones/{id}/comentarios/
        POST /api/publicaciones/{id}/comentarios/ -> {'contenido': 'Texto del comentario'}
        """
        publicacion = self.get_object()

        if request.method == 'GET':
            comentarios = publicacion.comentarios.filter(esta_activo=True).order_by('fecha_creacion')
            serializer = ComentarioPublicacionSerializer(comentarios, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method == 'POST':
            if not request.user or not request.user.is_authenticated:
                return Response({'detail': 'Las credenciales de autenticación no se proveyeron.'}, status=status.HTTP_401_UNAUTHORIZED)
            
            serializer = ComentarioPublicacionSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save(autor=request.user, publicacion=publicacion)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ComentarioPublicacionViewSet(viewsets.ModelViewSet):
    """
    Endpoint CRUD para gestionar comentarios en publicaciones.
    - GET /api/comentarios-publicaciones/?publicacion={publicacion_id}
    - POST /api/comentarios-publicaciones/
    - PUT /api/comentarios-publicaciones/{id}/
    - PATCH /api/comentarios-publicaciones/{id}/
    - DELETE /api/comentarios-publicaciones/{id}/
    """
    queryset = ComentarioPublicacion.objects.filter(esta_activo=True).order_by('fecha_creacion')
    serializer_class = ComentarioPublicacionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAutorOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)

    def get_queryset(self):
        queryset = ComentarioPublicacion.objects.all().order_by('fecha_creacion')
        if not (self.request.user and self.request.user.is_staff):
            queryset = queryset.filter(esta_activo=True)

        publicacion_id = self.request.query_params.get('publicacion')
        if publicacion_id:
            queryset = queryset.filter(publicacion_id=publicacion_id)

        return queryset



