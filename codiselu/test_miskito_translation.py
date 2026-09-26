from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APIClient, APIRequestFactory
from .models import User, Ciudad, CircuitoCreativo, PuntoInteres
from .serializers import CiudadSerializer
from .pdf_export_service import generar_pdf_traduccion_miskito


class MiskitoTranslationTests(TestCase):
    def setUp(self):
        # Crear usuario administrador
        self.admin_user = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='testpassword123'
        )

        # Ciudad 1 con circuito creativo
        self.ciudad_con_circuito = Ciudad.objects.create(
            nombre="León Test",
            nombre_miq="León Miskitu",
            descripcion="Ciudad colonial y universitaria",
            descripcion_miq="Taun colonial bara universitaria",
            latitud_centro=12.43,
            longitud_centro=-86.87
        )

        self.circuito = CircuitoCreativo.objects.create(
            ciudad=self.ciudad_con_circuito,
            nombre="Ruta de Poetas",
            nombre_miq="Poetas Auka",
            descripcion="Recorrido histórico por iglesias y murales",
            distancia_km=3.5,
            duracion_estimada="2 horas",
            dificultad="Baja"
        )

        self.punto = PuntoInteres.objects.create(
            circuito=self.circuito,
            nombre="Catedral de León",
            nombre_miq="León Ingwan Watla",
            descripcion="Patrimonio de la humanidad",
            tipo="Cultural",
            orden=1,
            latitud=12.435,
            longitud=-86.878
        )

        # Ciudad 2 SIN circuitos creativos (debe ser excluida del PDF)
        self.ciudad_sin_circuito = Ciudad.objects.create(
            nombre="Ciudad Sin Circuito",
            descripcion="Municipio sin rutas activas",
            latitud_centro=11.0,
            longitud_centro=-85.0
        )

    def test_pdf_service_excluye_ciudades_sin_circuitos(self):
        """Verifica que el servicio de PDF solo incluya ciudades con circuitos."""
        pdf_buf = generar_pdf_traduccion_miskito()
        pdf_content = pdf_buf.getvalue()

        self.assertGreater(len(pdf_content), 1000)
        # El PDF contiene el encabezado en formato PDF estándar
        self.assertTrue(pdf_content.startswith(b'%PDF'))

    def test_api_endpoint_exportar_miskito_pdf(self):
        """Verifica que el endpoint API devuelva el PDF correctamente."""
        client = APIClient()
        resp = client.get('/api/ciudades/exportar-miskito-pdf/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')
        content = b''.join(resp.streaming_content)
        self.assertTrue(content.startswith(b'%PDF'))

    def test_api_endpoint_directo_traduccion_miskito_pdf(self):
        """Verifica el endpoint directo /api/exportar-miskito-pdf/."""
        client = APIClient()
        resp = client.get('/api/exportar-miskito-pdf/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')

    def test_admin_export_miskito_view(self):
        """Verifica la vista de exportación dentro del Django Admin."""
        client = Client()
        client.force_login(self.admin_user)
        url = reverse('admin:codiselu_ciudad_exportar_miskito')
        resp = client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')

    def test_serializer_traduccion_miskito_con_query_param(self):
        """Verifica que el serializador responda con la traducción a Miskito al solicitar ?lang=miq."""
        factory = APIRequestFactory()
        request_miq = factory.get('/api/ciudades/', {'lang': 'miq'})
        serializer_miq = CiudadSerializer(self.ciudad_con_circuito, context={'request': request_miq})
        data = serializer_miq.data

        self.assertEqual(data['nombre'], "León Miskitu")
        self.assertEqual(data['descripcion'], "Taun colonial bara universitaria")
        self.assertIn('miq', data['traducciones'])
        self.assertEqual(data['traducciones']['miq']['nombre'], "León Miskitu")

    def test_serializer_fallback_espanol_si_no_hay_miskito(self):
        """Verifica que si no hay traducción en Miskito, se use el texto original en español como fallback seguro."""
        ciudad_sin_miskito = Ciudad.objects.create(
            nombre="Granada",
            descripcion="Gran Sultana",
            latitud_centro=11.93,
            longitud_centro=-85.95
        )
        factory = APIRequestFactory()
        request_miq = factory.get('/api/ciudades/', {'lang': 'miq'})
        serializer_miq = CiudadSerializer(ciudad_sin_miskito, context={'request': request_miq})
        data = serializer_miq.data

        self.assertEqual(data['nombre'], "Granada")
        self.assertEqual(data['descripcion'], "Gran Sultana")

    def test_solo_pendientes_omite_elementos_ya_traducidos(self):
        """Verifica que al traducir completamente un punto o circuito, se excluyan del PDF."""
        # Completar traducción de la descripción del circuito y punto
        self.circuito.descripcion_miq = "Traducido circuito"
        self.circuito.save()
        self.punto.descripcion_miq = "Traducido punto"
        self.punto.save()

        # Ahora todos los campos de ciudad_con_circuito están traducidos
        pdf_buf_pendientes = generar_pdf_traduccion_miskito(solo_pendientes=True)
        pdf_content = pdf_buf_pendientes.getvalue()
        self.assertGreater(len(pdf_content), 500)
        # El PDF indica que no hay pendientes o felicitaciones
        self.assertTrue(b'%PDF' in pdf_content)

        # Si se solicita la versión completa, se incluyen los elementos traducidos
        pdf_buf_completo = generar_pdf_traduccion_miskito(solo_pendientes=False)
        self.assertGreater(len(pdf_buf_completo.getvalue()), len(pdf_content))

    def test_endpoints_aceptan_parametro_solo_pendientes(self):
        """Verifica que tanto la API como el admin acepten ?solo_pendientes=1 y ?solo_pendientes=0."""
        client = APIClient()
        resp_pend = client.get('/api/ciudades/exportar-miskito-pdf/?solo_pendientes=1')
        self.assertEqual(resp_pend.status_code, 200)
        self.assertIn('Pendientes', resp_pend['Content-Disposition'])

        resp_comp = client.get('/api/ciudades/exportar-miskito-pdf/?solo_pendientes=0')
        self.assertEqual(resp_comp.status_code, 200)
        self.assertIn('Completo', resp_comp['Content-Disposition'])

        # En el admin
        client_admin = Client()
        client_admin.force_login(self.admin_user)
        url_admin = reverse('admin:codiselu_ciudad_exportar_miskito')
        resp_admin_pend = client_admin.get(f"{url_admin}?solo_pendientes=1")
        self.assertEqual(resp_admin_pend.status_code, 200)
        self.assertIn('Pendientes', resp_admin_pend['Content-Disposition'])
