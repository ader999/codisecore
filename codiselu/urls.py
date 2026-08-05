from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, CiudadViewSet, CircuitoCreativoViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'ciudades', CiudadViewSet, basename='ciudad')
router.register(r'circuitos', CircuitoCreativoViewSet, basename='circuito')
router.register(r'circuitos-creativos', CircuitoCreativoViewSet, basename='circuitocreativo')
router.register(r'circuitocreativos', CircuitoCreativoViewSet, basename='circuitocreativos')

urlpatterns = [
    path('', RedirectView.as_view(url='/api/', permanent=False)),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]
