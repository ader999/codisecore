from rest_framework import viewsets, permissions, status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Ciudad, CircuitoCreativo, PuntoInteres, DatoHistorico, GaleriaMultimedia
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    CiudadSerializer,
    CircuitoCreativoSerializer,
    PuntoInteresSerializer,
    DatoHistoricoSerializer,
    GaleriaMultimediaSerializer
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


