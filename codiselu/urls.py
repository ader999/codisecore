from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'usuarios', views.UserViewSet)
router.register(r'ciudades', views.CiudadViewSet)
router.register(r'circuitos', views.CircuitoCreativoViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/registro/', views.RegisterView.as_view(), name='registro'),
    path('api/', include(router.urls)),
]
