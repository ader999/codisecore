from django.db import models
from rest_framework import viewsets, permissions, status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import action
from .models import (
    User, Ciudad, CircuitoCreativo, PuntoInteres, DatoHistorico,
    GaleriaMultimedia, UsuarioPuntoVisitado, Empresa, OportunidadInversion,
    InversionTurista, Evento
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
    EventoSerializer
)


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

