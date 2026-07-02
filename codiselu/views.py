from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User, Ciudad, CircuitoCreativo
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    CiudadSerializer,
    CircuitoCreativoListSerializer,
    CircuitoCreativoSerializer,
)


class RegisterView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                UserSerializer(user).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class CiudadViewSet(viewsets.ModelViewSet):
    queryset = Ciudad.objects.all()
    serializer_class = CiudadSerializer

    @action(detail=True, methods=['get'])
    def circuitos(self, request, pk=None):
        ciudad = self.get_object()
        circuitos = ciudad.circuitos.all()
        serializer = CircuitoCreativoListSerializer(circuitos, many=True)
        return Response(serializer.data)


class CircuitoCreativoViewSet(viewsets.ModelViewSet):
    queryset = CircuitoCreativo.objects.all()
    serializer_class = CircuitoCreativoSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return CircuitoCreativoListSerializer
        return CircuitoCreativoSerializer
