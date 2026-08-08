from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserViewSet,
    CiudadViewSet,
    CircuitoCreativoViewSet,
    PuntoInteresViewSet,
    DatoHistoricoViewSet,
    GaleriaMultimediaViewSet,
    VisitaViewSet,
    RegisterView,
    LoginView,
    UserProfileView
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'ciudades', CiudadViewSet, basename='ciudad')
router.register(r'circuitos', CircuitoCreativoViewSet, basename='circuito')
router.register(r'circuitos-creativos', CircuitoCreativoViewSet, basename='circuitocreativo')
router.register(r'puntos-interes', PuntoInteresViewSet, basename='puntointeres')
router.register(r'datos-historicos', DatoHistoricoViewSet, basename='datohistorico')
router.register(r'galeria-multimedia', GaleriaMultimediaViewSet, basename='galeriamultimedia')
router.register(r'visitas', VisitaViewSet, basename='visita')
router.register(r'usuario-puntos-visitados', VisitaViewSet, basename='usuariopuntosvisitados')

urlpatterns = [
    path('', RedirectView.as_view(url='/api/', permanent=False)),
    path('admin/', admin.site.urls),
    path('api/auth/register/', RegisterView.as_view(), name='auth_register'),
    path('api/auth/login/', LoginView.as_view(), name='auth_login'),
    path('api/auth/me/', UserProfileView.as_view(), name='auth_me'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Accesos directos alternativos
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/', include(router.urls)),
]


