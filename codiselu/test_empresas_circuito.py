from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from codiselu.models import User, Ciudad, CircuitoCreativo, PuntoInteres, Empresa
from codiselu.circuito_service import obtener_empresas_en_ruta_circuito


class EmpresasCircuitoTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.ciudad = Ciudad.objects.create(nombre="León", latitud_centro=12.435, longitud_centro=-86.879)

        # Crear circuito
        self.circuito = CircuitoCreativo.objects.create(
            ciudad=self.ciudad,
            nombre="Ruta de los Poetas",
            descripcion="Circuito colonial",
            distancia_km=2.5,
            duracion_estimada="1.5 horas"
        )

        # Punto de interés en (12.4350, -86.8790)
        self.punto = PuntoInteres.objects.create(
            circuito=self.circuito,
            nombre="Catedral de León",
            descripcion="Patrimonio UNESCO",
            latitud=12.4350,
            longitud=-86.8790,
            orden=1
        )

        # Empresa 1: Muy cerca (a ~50 metros), sin publicidad
        self.empresa_cercana = Empresa.objects.create(
            usuario=self.user,
            ciudad=self.ciudad,
            nombre="Taller El Poeta",
            descripcion="Artesanías",
            latitud=12.4353,
            longitud=-86.8792,
            telefono_contacto="+50588881111",
            numero_whatsapp="+505 8888-1111",
            tiene_publicidad=False
        )

        # Empresa 2: Más alejada (a ~1.8 km), pero con publicidad pagada
        self.empresa_patrocinada = Empresa.objects.create(
            usuario=self.user,
            ciudad=self.ciudad,
            nombre="Restaurante La Casona Real",
            descripcion="Comida típica",
            latitud=12.4450,
            longitud=-86.8900,
            telefono_contacto="+50588882222",
            numero_whatsapp="+50588882222",
            tiene_publicidad=True,
            fecha_fin_publicidad=timezone.now().date() + timezone.timedelta(days=30)
        )

        # Empresa 3: Muy alejada (a ~10 km), sin publicidad
        self.empresa_lejana = Empresa.objects.create(
            usuario=self.user,
            ciudad=self.ciudad,
            nombre="Hotel Afueras",
            descripcion="Alojamiento campestre",
            latitud=12.5200,
            longitud=-86.9500,
            tiene_publicidad=False
        )

    def test_whatsapp_link_property(self):
        self.assertEqual(self.empresa_cercana.link_whatsapp, "https://wa.me/50588881111")
        self.assertEqual(self.empresa_patrocinada.link_whatsapp, "https://wa.me/50588882222")
        self.assertIsNone(self.empresa_lejana.link_whatsapp)

    def test_publicidad_activa_property(self):
        self.assertTrue(self.empresa_patrocinada.tiene_publicidad_activa)
        self.assertFalse(self.empresa_cercana.tiene_publicidad_activa)

        # Si expiró la fecha
        self.empresa_patrocinada.fecha_fin_publicidad = timezone.now().date() - timezone.timedelta(days=1)
        self.empresa_patrocinada.save()
        self.assertFalse(self.empresa_patrocinada.tiene_publicidad_activa)

    def test_obtener_empresas_en_ruta_service(self):
        empresas = obtener_empresas_en_ruta_circuito(self.circuito, radio_metros=800, radio_patrocinado_metros=5000)
        
        # Deben salir la patrocinada y la cercana, pero NO la lejana
        nombres = [e.nombre for e in empresas]
        self.assertIn("Restaurante La Casona Real", nombres)
        self.assertIn("Taller El Poeta", nombres)
        self.assertNotIn("Hotel Afueras", nombres)

        # La patrocinada debe aparecer primero en la lista
        self.assertEqual(empresas[0].nombre, "Restaurante La Casona Real")
        self.assertTrue(empresas[0].es_patrocinada)

        # La cercana debe tener es_patrocinada = False y estar en ruta
        self.assertEqual(empresas[1].nombre, "Taller El Poeta")
        self.assertFalse(empresas[1].es_patrocinada)
        self.assertTrue(empresas[1].en_ruta)

    def test_circuito_detail_api_includes_empresas_en_ruta(self):
        res = self.client.get(f"/api/circuitos/{self.circuito.id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("empresas_en_ruta", res.data)
        self.assertEqual(len(res.data["empresas_en_ruta"]), 2)
        self.assertEqual(res.data["empresas_en_ruta"][0]["nombre"], "Restaurante La Casona Real")
        self.assertTrue(res.data["empresas_en_ruta"][0]["es_patrocinada"])
        self.assertEqual(res.data["empresas_en_ruta"][0]["link_whatsapp"], "https://wa.me/50588882222")

    def test_circuito_empresas_action_endpoint(self):
        res = self.client.get(f"/api/circuitos/{self.circuito.id}/empresas/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
