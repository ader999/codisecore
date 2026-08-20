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
    UserProfileView,
    EmpresaViewSet,
    OportunidadInversionViewSet,
    InversionTuristaViewSet,
    EventoViewSet,
    PublicacionViewSet,
    ComentarioPublicacionViewSet
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
router.register(r'empresas', EmpresaViewSet, basename='empresa')
router.register(r'oportunidades-inversion', OportunidadInversionViewSet, basename='oportunidadinversion')
router.register(r'inversiones-turistas', InversionTuristaViewSet, basename='inversionturista')
router.register(r'eventos', EventoViewSet, basename='evento')
router.register(r'publicaciones', PublicacionViewSet, basename='publicacion')
router.register(r'comentarios-publicaciones', ComentarioPublicacionViewSet, basename='comentario-publicacion')

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


