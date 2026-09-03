from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from codiselu.models import User


class AuthEndpointsTests(APITestCase):

    def setUp(self):
        self.register_url = reverse('auth_register')
        self.login_url = reverse('auth_login')
        self.me_url = reverse('auth_me')
        self.refresh_token_url = reverse('token_refresh')

        self.user_password = 'TestPassword123!'
        self.user_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': self.user_password,
            'password_confirm': self.user_password,
            'first_name': 'Test',
            'last_name': 'User',
            'es_protagonista': False,
            'es_turista': True,
            'telefono': '123456789'
        }

    def test_register_user_success(self):
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertEqual(response.data['user']['username'], 'testuser')
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_register_password_mismatch(self):
        invalid_data = self.user_data.copy()
        invalid_data['username'] = 'anotheruser'
        invalid_data['email'] = 'anotheruser@example.com'
        invalid_data['password_confirm'] = 'DifferentPassword123!'
        response = self.client.post(self.register_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data)

    def test_login_user_with_username_success(self):
        User.objects.create_user(
            username='loginuser',
            email='loginuser@example.com',
            password=self.user_password
        )
        login_payload = {
            'username': 'loginuser',
            'password': self.user_password
        }
        response = self.client.post(self.login_url, login_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['user']['username'], 'loginuser')

    def test_login_user_with_email_success(self):
        User.objects.create_user(
            username='emailuser',
            email='emailuser@example.com',
            password=self.user_password
        )
        login_payload = {
            'username': 'emailuser@example.com',
            'password': self.user_password
        }
        response = self.client.post(self.login_url, login_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['user']['username'], 'emailuser')

    def test_login_invalid_credentials(self):
        login_payload = {
            'username': 'nonexistent',
            'password': 'WrongPassword123!'
        }
        response = self.client.post(self.login_url, login_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authenticated_user_profile_and_token_refresh(self):
        # Register user and get tokens
        reg_response = self.client.post(self.register_url, self.user_data, format='json')
        access_token = reg_response.data['tokens']['access']
        refresh_token = reg_response.data['tokens']['refresh']

        # Access /api/auth/me/ with Bearer token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)
        me_response = self.client.get(self.me_url)
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data['username'], 'testuser')

        # Test token refresh
        self.client.credentials()  # Clear credentials
        refresh_response = self.client.post(self.refresh_token_url, {'refresh': refresh_token}, format='json')
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)


class CiudadesYContenidoApiTests(APITestCase):

    def test_ciudades_endpoints_with_datos_historicos_y_multimedia(self):
        from codiselu.models import Ciudad, CircuitoCreativo, PuntoInteres, DatoHistorico, GaleriaMultimedia

        # Crear Ciudad
        ciudad = Ciudad.objects.create(
            nombre="León",
            descripcion="Ciudad histórica de Nicaragua",
            latitud_centro=12.4379,
            longitud_centro=-86.8780
        )

        # Crear Circuito y Punto de Interés
        circuito = CircuitoCreativo.objects.create(
            ciudad=ciudad,
            nombre="Ruta Poética",
            descripcion="Circuito cultural por León",
            distancia_km=2.5,
            duracion_estimada="1 hora",
            dificultad="Baja"
        )

        punto = PuntoInteres.objects.create(
            circuito=circuito,
            nombre="Catedral de León",
            descripcion="Insigne y Real Basílica",
            tipo="Historico",
            orden=1,
            latitud=12.435,
            longitud=-86.879
        )

        # Crear Datos Históricos
        DatoHistorico.objects.create(
            ciudad=ciudad,
            titulo="Leyenda de la Mocuana",
            tipo="Leyenda",
            contenido="Mito tradicional leonés"
        )

        DatoHistorico.objects.create(
            punto_interes=punto,
            titulo="Tumba de Rubén Darío",
            tipo="Hito",
            contenido="Restos del ilustre poeta"
        )

        # Crear Galería Multimedia
        GaleriaMultimedia.objects.create(
            ciudad=ciudad,
            titulo="Foto Panorámica León",
            tipo="Imagen"
        )

        # 1. Probar GET /api/ciudades/
        res_ciudades = self.client.get('/api/ciudades/')
        self.assertEqual(res_ciudades.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_ciudades.data), 1)
        ciudad_data = res_ciudades.data[0]
        self.assertEqual(ciudad_data['nombre'], "León")
        self.assertEqual(len(ciudad_data['datos_historicos']), 1)
        self.assertEqual(len(ciudad_data['galeria']), 1)
        self.assertEqual(len(ciudad_data['circuitos']), 1)
        self.assertEqual(len(ciudad_data['circuitos'][0]['puntos_interes']), 1)

        # 2. Probar GET /api/datos-historicos/
        res_datos = self.client.get('/api/datos-historicos/')
        self.assertEqual(res_datos.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_datos.data), 2)

        # 3. Probar GET /api/galeria-multimedia/
        res_galeria = self.client.get('/api/galeria-multimedia/')
        self.assertEqual(res_galeria.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_galeria.data), 1)

        # 4. Probar GET /api/puntos-interes/
        res_puntos = self.client.get('/api/puntos-interes/')
        self.assertEqual(res_puntos.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_puntos.data), 1)
        self.assertEqual(len(res_puntos.data[0]['datos_historicos']), 1)


class VisitaEndpointsTests(APITestCase):

    def setUp(self):
        from codiselu.models import Ciudad, CircuitoCreativo, PuntoInteres, UsuarioPuntoVisitado

        self.user = User.objects.create_user(
            username='turista1',
            email='turista1@example.com',
            password='TestPassword123!'
        )

        self.ciudad = Ciudad.objects.create(
            nombre="Granada",
            descripcion="Granada la Sultana",
            latitud_centro=11.9344,
            longitud_centro=-85.9560
        )
        self.circuito = CircuitoCreativo.objects.create(
            ciudad=self.ciudad,
            nombre="Ruta Colonial",
            descripcion="Recorrido histórico por Granada",
            distancia_km=3.0,
            duracion_estimada="1.5 horas"
        )
        self.punto1 = PuntoInteres.objects.create(
            circuito=self.circuito,
            nombre="Parque Central de Granada",
            descripcion="Parque principal",
            orden=1,
            latitud=11.935,
            longitud=-85.957
        )
        self.punto2 = PuntoInteres.objects.create(
            circuito=self.circuito,
            nombre="Iglesia de Guadalupe",
            descripcion="Iglesia histórica",
            orden=2,
            latitud=11.936,
            longitud=-85.958
        )

    def test_registrar_y_consultar_visita(self):
        # 1. Intentar registrar visita sin autenticación -> 401 Unauthorized
        res_unauth = self.client.post('/api/visitas/', {'punto_interes_id': self.punto1.id}, format='json')
        self.assertEqual(res_unauth.status_code, status.HTTP_401_UNAUTHORIZED)

        # Autenticar usuario
        self.client.force_authenticate(user=self.user)

        # 2. Registrar visita POST /api/visitas/
        res_create = self.client.post('/api/visitas/', {'punto_interes_id': self.punto1.id}, format='json')
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_create.data['punto_interes_id'], self.punto1.id)
        self.assertEqual(res_create.data['usuario_id'], self.user.id)

        # 3. Registrar otra visita POST /api/visitas/ con punto2
        self.client.post('/api/visitas/', {'punto_interes_id': self.punto2.id}, format='json')

        # 4. GET /api/visitas/ -> Lista de visitas
        res_list = self.client.get('/api/visitas/')
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_list.data), 2)

        # 5. GET /api/visitas/ids/ -> Array directo de IDs visitados
        res_ids = self.client.get('/api/visitas/ids/')
        self.assertEqual(res_ids.status_code, status.HTTP_200_OK)
        self.assertIn(self.punto1.id, res_ids.data)
        self.assertIn(self.punto2.id, res_ids.data)

        # 6. GET /api/visitas/?ids_only=true -> Array directo con query param
        res_query_ids = self.client.get('/api/visitas/?ids_only=true')
        self.assertEqual(res_query_ids.status_code, status.HTTP_200_OK)
        self.assertIn(self.punto1.id, res_query_ids.data)

        # 7. Alias /api/usuario-puntos-visitados/
        res_alias = self.client.get('/api/usuario-puntos-visitados/')
        self.assertEqual(res_alias.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_alias.data), 2)

    def test_validacion_geolocalizacion_gps(self):
        self.client.force_authenticate(user=self.user)

        # 1. Enviar coordenadas muy cercanas a punto1 (lat=11.935, lon=-85.957) -> es_validada = True
        payload_cerca = {
            'punto_interes_id': self.punto1.id,
            'latitud_usuario': 11.93505,
            'longitud_usuario': -85.95705
        }
        res_cerca = self.client.post('/api/visitas/', payload_cerca, format='json')
        self.assertEqual(res_cerca.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res_cerca.data['es_validada'])
        self.assertLess(res_cerca.data['distancia_metros'], 200.0)

        # 2. Enviar coordenadas lejanas para punto2 -> es_validada = False
        payload_lejos = {
            'punto_interes_id': self.punto2.id,
            'latitud_usuario': 12.000,
            'longitud_usuario': -86.000
        }
        res_lejos = self.client.post('/api/visitas/', payload_lejos, format='json')
        self.assertEqual(res_lejos.status_code, status.HTTP_201_CREATED)
        self.assertFalse(res_lejos.data['es_validada'])
        self.assertGreater(res_lejos.data['distancia_metros'], 200.0)


class EmpresaYEventosApiTests(APITestCase):

    def setUp(self):
        from codiselu.models import Ciudad, Empresa, OportunidadInversion, Evento

        self.protagonista = User.objects.create_user(
            username='protagonista1',
            email='prota@example.com',
            password='TestPassword123!',
            es_protagonista=True
        )
        self.turista = User.objects.create_user(
            username='turista_inversor',
            email='inversor@example.com',
            password='TestPassword123!',
            es_turista=True
        )

        self.ciudad = Ciudad.objects.create(
            nombre="Masaya",
            descripcion="Ciudad de las Flores",
            latitud_centro=11.9744,
            longitud_centro=-86.0942
        )

    def test_crear_empresa_y_oportunidad_inversion(self):
        self.client.force_authenticate(user=self.protagonista)

        # 1. Crear Empresa que ACEPTA inversiones
        payload_empresa = {
            'nombre': 'Artesanías Monimbó',
            'descripcion': 'Taller artesanal de hamacas y cerámica',
            'categoria': 'Taller',
            'ciudad': self.ciudad.id,
            'acepta_inversiones': True,
            'direccion': 'Barrio Monimbó, Masaya'
        }
        res_empresa = self.client.post('/api/empresas/', payload_empresa, format='json')
        self.assertEqual(res_empresa.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res_empresa.data['acepta_inversiones'])
        empresa_id = res_empresa.data['id']

        # 2. Publicar Oportunidad de Inversión
        payload_oportunidad = {
            'empresa': empresa_id,
            'titulo': 'Expansión de taller de hamacas',
            'descripcion': 'Buscamos capital para exportar hamacas a Europa',
            'monto_requerido': '5000.00',
            'monto_minimo_inversion': '100.00',
            'retorno_estimado': '12% anual',
            'tipo_inversor_permitido': 'Todos'
        }
        res_op = self.client.post('/api/oportunidades-inversion/', payload_oportunidad, format='json')
        self.assertEqual(res_op.status_code, status.HTTP_201_CREATED)
        oportunidad_id = res_op.data['id']

        # 3. Turista realiza inversión
        self.client.force_authenticate(user=self.turista)
        payload_inversion = {
            'oportunidad': oportunidad_id,
            'monto_propuesto': '500.00',
            'tipo_inversor': 'Extranjero',
            'mensaje': 'Interesado en apoyar la artesanía nicaragüense',
            'telefono_inversor': '+50588888888'
        }
        res_inv = self.client.post('/api/inversiones-turistas/', payload_inversion, format='json')
        self.assertEqual(res_inv.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_inv.data['inversionista_username'], 'turista_inversor')

    def test_validacion_empresa_no_acepta_inversiones(self):
        from codiselu.models import Empresa

        empresa_no_inv = Empresa.objects.create(
            usuario=self.protagonista,
            nombre='Restaurante Tradicional',
            descripcion='Comida típica',
            acepta_inversiones=False
        )

        self.client.force_authenticate(user=self.protagonista)
        payload_oportunidad = {
            'empresa': empresa_no_inv.id,
            'titulo': 'Inversión rechazada',
            'descripcion': 'Intento de inversión',
            'monto_requerido': '1000.00'
        }
        res_op = self.client.post('/api/oportunidades-inversion/', payload_oportunidad, format='json')
        self.assertEqual(res_op.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('empresa', res_op.data)

    def test_crear_y_listar_eventos(self):
        self.client.force_authenticate(user=self.protagonista)

        payload_evento = {
            'titulo': 'Feria de la Cerámica Tradicional',
            'descripcion': 'Exposición y venta de piezas únicas',
            'ciudad': self.ciudad.id,
            'fecha_inicio': '2026-09-15T10:00:00Z',
            'ubicacion': 'Plaza Central de Masaya',
            'es_gratuito': True
        }
        res_evento = self.client.post('/api/eventos/', payload_evento, format='json')
        self.assertEqual(res_evento.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_evento.data['titulo'], 'Feria de la Cerámica Tradicional')

        # GET público /api/eventos/
        self.client.logout()
        res_get = self.client.get('/api/eventos/')
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_get.data), 1)

    def test_crear_y_listar_eventos_oficiales_y_mural(self):
        from django.utils import timezone

        admin_user = User.objects.create_superuser(
            username='admin_ciudad',
            email='admin@example.com',
            password='TestPassword123!'
        )

        self.client.force_authenticate(user=admin_user)
        ahora = timezone.now()
        fecha_proxima = ahora + timezone.timedelta(days=3)

        payload_evento_oficial = {
            'titulo': 'Fiesta Patronal Oficial de San Jerónimo',
            'descripcion': 'Celebración oficial apoyada por la alcaldía y comisión de cultura',
            'ciudad': self.ciudad.id,
            'fecha_inicio': fecha_proxima.isoformat(),
            'ubicacion': 'Parque Central de Masaya',
            'dias_previos_mural': 10,
            'es_oficial': True
        }
        res_admin = self.client.post('/api/eventos/', payload_evento_oficial, format='json')
        self.assertEqual(res_admin.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res_admin.data['es_oficial'])
        self.assertTrue(res_admin.data['en_mural'])

        res_mural = self.client.get('/api/eventos/?en_mural=true')
        self.assertEqual(res_mural.status_code, status.HTTP_200_OK)
        self.assertTrue(any(e['id'] == res_admin.data['id'] for e in res_mural.data))

        res_oficiales = self.client.get('/api/eventos/?es_oficial=true')
        self.assertEqual(res_oficiales.status_code, status.HTTP_200_OK)
        self.assertTrue(all(e['es_oficial'] for e in res_oficiales.data))


class InteraccionesEventosYPublicacionesTests(APITestCase):

    def setUp(self):
        from codiselu.models import Ciudad, Evento, Publicacion, GaleriaMultimedia, PublicacionImagen

        self.user_turista = User.objects.create_user(
            username='turista_fan',
            email='turistafan@example.com',
            password='TestPassword123!',
            es_turista=True
        )
        self.user_prota = User.objects.create_user(
            username='prota_artesano',
            email='protaartesano@example.com',
            password='TestPassword123!',
            es_protagonista=True
        )

        self.ciudad = Ciudad.objects.create(
            nombre="Estelí",
            descripcion="Ciudad del Café y los Murales",
            latitud_centro=13.0918,
            longitud_centro=-86.3538
        )

        self.evento = Evento.objects.create(
            creador=self.user_prota,
            ciudad=self.ciudad,
            titulo="Feria Regional del Café",
            descripcion="Degustación y exhibición de café de altura",
            fecha_inicio="2026-09-18T15:00:00Z",
            ubicacion="Plaza de la Cultura, Estelí"
        )

        # Galería para el evento
        self.galeria_evento = GaleriaMultimedia.objects.create(
            evento=self.evento,
            titulo="Carrusel Foto 1",
            tipo="Imagen"
        )

    def test_interacciones_evento_grano_cafe_y_asistir(self):
        self.client.force_authenticate(user=self.user_turista)

        # 1. Grano de café POST /api/eventos/{id}/grano-cafe/
        res_grano = self.client.post(f'/api/eventos/{self.evento.id}/grano-cafe/')
        self.assertEqual(res_grano.status_code, status.HTTP_200_OK)
        self.assertTrue(res_grano.data['ha_dado_grano_cafe'])
        self.assertEqual(res_grano.data['total_granos_cafe'], 1)

        # Toggle grano de café (quitar)
        res_grano_quitar = self.client.post(f'/api/eventos/{self.evento.id}/grano-cafe/')
        self.assertEqual(res_grano_quitar.status_code, status.HTTP_200_OK)
        self.assertFalse(res_grano_quitar.data['ha_dado_grano_cafe'])
        self.assertEqual(res_grano_quitar.data['total_granos_cafe'], 0)

        # 2. Asistir POST /api/eventos/{id}/asistir/
        res_asistir = self.client.post(f'/api/eventos/{self.evento.id}/asistir/')
        self.assertEqual(res_asistir.status_code, status.HTTP_200_OK)
        self.assertTrue(res_asistir.data['va_a_asistir'])
        self.assertEqual(res_asistir.data['total_asistentes'], 1)

        # 3. GET /api/eventos/{id}/ incluye carrusel galeria y contadores
        res_detail = self.client.get(f'/api/eventos/{self.evento.id}/')
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_detail.data['galeria']), 1)
        self.assertTrue(res_detail.data['user_va_a_asistir'])
        self.assertEqual(res_detail.data['total_asistentes'], 1)

    def test_publicaciones_turistas_y_likes(self):
        from codiselu.models import Publicacion, PublicacionImagen

        self.client.force_authenticate(user=self.user_turista)

        # 1. Crear publicación opcionalmente asociada a evento
        payload_pub = {
            'descripcion': 'Hermoso evento del café en Estelí',
            'ciudad': self.ciudad.id,
            'evento': self.evento.id
        }
        res_pub = self.client.post('/api/publicaciones/', payload_pub, format='json')
        self.assertEqual(res_pub.status_code, status.HTTP_201_CREATED)
        pub_id = res_pub.data['id']
        self.assertEqual(res_pub.data['autor_username'], 'turista_fan')

        # 2. Dar like a la publicación
        res_like = self.client.post(f'/api/publicaciones/{pub_id}/like/')
        self.assertEqual(res_like.status_code, status.HTTP_200_OK)
        self.assertTrue(res_like.data['ha_dado_like'])
        self.assertEqual(res_like.data['total_likes'], 1)

        # 3. GET /api/publicaciones/ filtrado por evento
        res_list = self.client.get(f'/api/publicaciones/?evento={self.evento.id}')
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_list.data), 1)
        self.assertEqual(res_list.data[0]['total_likes'], 1)

    def test_crear_publicacion_con_multiples_imagenes(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from codiselu.models import Publicacion, PublicacionImagen
        import io
        from PIL import Image

        self.client.force_authenticate(user=self.user_turista)

        # Generar 10 imágenes simuladas (máximo 10 fotos por publicación)
        imagenes_files = []
        for i in range(1, 11):
            img_io = io.BytesIO()
            img = Image.new('RGB', (50, 50), color=(i * 20, 100, 150))
            img.save(img_io, format='JPEG')
            file_data = SimpleUploadedFile(
                name=f'foto_mural_{i}.jpg',
                content=img_io.getvalue(),
                content_type='image/jpeg'
            )
            imagenes_files.append(file_data)

        # Enviar petición multipart con 10 fotos en 'imagenes'
        payload = {
            'descripcion': 'Publicación con 10 fotografías de mi visita',
            'ciudad': self.ciudad.id,
            'esta_activa': True,
            'imagenes': imagenes_files
        }

        res = self.client.post('/api/publicaciones/', payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        pub_id = res.data['id']
        self.assertEqual(PublicacionImagen.objects.filter(publicacion_id=pub_id).count(), 10)

        # Verificar respuesta GET del detalle de la publicación
        res_detail = self.client.get(f'/api/publicaciones/{pub_id}/')
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_detail.data['imagenes']), 10)

    def test_crear_publicacion_con_imagen_principal_y_coleccion(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from codiselu.models import Publicacion, PublicacionImagen
        import io
        from PIL import Image

        self.client.force_authenticate(user=self.user_prota)

        # Imagen principal
        img_main_io = io.BytesIO()
        Image.new('RGB', (100, 100), color='red').save(img_main_io, format='JPEG')
        imagen_principal = SimpleUploadedFile(
            name='portada.jpg',
            content=img_main_io.getvalue(),
            content_type='image/jpeg'
        )

        # 5 imágenes adicionales
        imagenes_galeria = []
        for i in range(1, 6):
            img_io = io.BytesIO()
            Image.new('RGB', (50, 50), color='blue').save(img_io, format='JPEG')
            imagenes_galeria.append(
                SimpleUploadedFile(name=f'galeria_{i}.jpg', content=img_io.getvalue(), content_type='image/jpeg')
            )

        payload = {
            'titulo': 'Nueva exhibición artesanal',
            'descripcion': 'Colección completa de fotos del taller',
            'ciudad': self.ciudad.id,
            'esta_activa': True,
            'imagen_principal': imagen_principal,
            'imagenes': imagenes_galeria
        }

        res = self.client.post('/api/publicaciones/', payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(res.data['imagen_principal'])

        pub_id = res.data['id']
        res_detail = self.client.get(f'/api/publicaciones/{pub_id}/')
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_detail.data['imagenes']), 5)

    def test_comentarios_en_publicaciones(self):
        from codiselu.models import Publicacion, ComentarioPublicacion

        # 1. Crear una publicación
        self.client.force_authenticate(user=self.user_prota)
        payload_pub = {
            'descripcion': 'Publicación para probar comentarios',
            'ciudad': self.ciudad.id,
            'esta_activa': True
        }
        res_pub = self.client.post('/api/publicaciones/', payload_pub, format='json')
        self.assertEqual(res_pub.status_code, status.HTTP_201_CREATED)
        pub_id = res_pub.data['id']

        # 2. Intentar comentar sin estar autenticado (debe retornar 401)
        self.client.force_authenticate(user=None)
        res_unauth = self.client.post(f'/api/publicaciones/{pub_id}/comentarios/', {'contenido': 'Comentario anónimo'}, format='json')
        self.assertEqual(res_unauth.status_code, status.HTTP_401_UNAUTHORIZED)

        # 3. Comentar usando endpoint directo /api/publicaciones/{id}/comentarios/ autenticado como turista
        self.client.force_authenticate(user=self.user_turista)
        res_comment = self.client.post(f'/api/publicaciones/{pub_id}/comentarios/', {'contenido': '¡Excelente publicación!'}, format='json')
        self.assertEqual(res_comment.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_comment.data['autor_username'], self.user_turista.username)
        self.assertEqual(res_comment.data['contenido'], '¡Excelente publicación!')

        # 4. Comentar usando endpoint /api/comentarios-publicaciones/
        res_comment2 = self.client.post('/api/comentarios-publicaciones/', {
            'publicacion': pub_id,
            'contenido': 'Segundo comentario desde el endpoint global'
        }, format='json')
        self.assertEqual(res_comment2.status_code, status.HTTP_201_CREATED)

        # 5. Consultar los comentarios de la publicación
        res_list = self.client.get(f'/api/publicaciones/{pub_id}/comentarios/')
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_list.data), 2)

        # 6. Consultar detalle de la publicación y verificar total_comentarios y la lista de comentarios
        res_detail = self.client.get(f'/api/publicaciones/{pub_id}/')
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(res_detail.data['total_comentarios'], 2)
        self.assertEqual(len(res_detail.data['comentarios']), 2)

        comment_id = res_comment.data['id']

        # 7. Intentar actualizar comentario ajeno desde user_prota (debe retornar 403 Forbidden)
        self.client.force_authenticate(user=self.user_prota)
        res_update_forbidden = self.client.patch(f'/api/comentarios-publicaciones/{comment_id}/', {'contenido': 'Intento no autorizado'}, format='json')
        self.assertEqual(res_update_forbidden.status_code, status.HTTP_403_FORBIDDEN)

        # 8. Actualizar comentario propio desde user_turista (PATCH /api/comentarios-publicaciones/{id}/)
        self.client.force_authenticate(user=self.user_turista)
        res_update = self.client.patch(f'/api/comentarios-publicaciones/{comment_id}/', {'contenido': '¡Excelente publicación! (Editado)'}, format='json')
        self.assertEqual(res_update.status_code, status.HTTP_200_OK)
        self.assertEqual(res_update.data['contenido'], '¡Excelente publicación! (Editado)')

        # 9. Intentar eliminar comentario ajeno desde user_prota (debe retornar 403 Forbidden)
        self.client.force_authenticate(user=self.user_prota)
        res_delete_forbidden = self.client.delete(f'/api/comentarios-publicaciones/{comment_id}/')
        self.assertEqual(res_delete_forbidden.status_code, status.HTTP_403_FORBIDDEN)

        # 10. Eliminar comentario propio desde user_turista (DELETE /api/comentarios-publicaciones/{id}/)
        self.client.force_authenticate(user=self.user_turista)
        res_delete = self.client.delete(f'/api/comentarios-publicaciones/{comment_id}/')
        self.assertEqual(res_delete.status_code, status.HTTP_204_NO_CONTENT)

        # Verificar que el total de comentarios disminuyó a 1
        res_detail_after = self.client.get(f'/api/publicaciones/{pub_id}/')
        self.assertEqual(res_detail_after.data['total_comentarios'], 1)


class GoogleAuthEndpointsTests(APITestCase):

    def setUp(self):
        self.google_auth_url = reverse('auth_google')
        self.google_login_url = reverse('auth_google_url')
        self.google_callback_url = reverse('auth_google_callback')

    def test_google_login_url_generation(self):
        with self.settings(GOOGLE_CLIENT_ID='test-client-id-123.apps.googleusercontent.com'):
            response = self.client.get(self.google_login_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('url', response.data)
            self.assertIn('test-client-id-123', response.data['url'])
            self.assertIn('accounts.google.com', response.data['url'])

    def test_google_auth_missing_token(self):
        response = self.client.post(self.google_auth_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_google_auth_new_user_success(self, mock_verify):
        mock_verify.return_value = {
            'email': 'googleuser@example.com',
            'given_name': 'Google',
            'family_name': 'Tester',
            'picture': '',
            'email_verified': True,
        }

        payload = {'id_token': 'fake-valid-google-id-token'}
        response = self.client.post(self.google_auth_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertTrue(response.data['is_new_user'])
        self.assertEqual(response.data['user']['email'], 'googleuser@example.com')
        self.assertEqual(response.data['user']['first_name'], 'Google')
        self.assertTrue(User.objects.filter(email='googleuser@example.com').exists())

    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_google_auth_existing_user_login(self, mock_verify):
        existing_user = User.objects.create_user(
            username='existing_user',
            email='existing@example.com',
            password='Password123!'
        )

        mock_verify.return_value = {
            'email': 'existing@example.com',
            'given_name': 'Existing',
            'family_name': 'User',
            'picture': '',
            'email_verified': True,
        }

        payload = {'id_token': 'fake-valid-google-id-token'}
        response = self.client.post(self.google_auth_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_new_user'])
        self.assertEqual(response.data['user']['id'], existing_user.id)
        self.assertEqual(response.data['user']['email'], 'existing@example.com')

    def test_google_callback_without_code(self):
        response = self.client.get(self.google_callback_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)









