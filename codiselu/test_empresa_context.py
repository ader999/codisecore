from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from codiselu.models import User, Ciudad, Empresa, EmpresaMiembro, Publicacion, Evento


class EmpresaContextualTests(APITestCase):

    def setUp(self):
        patcher = patch('codiselu.translation_service.auto_completar_traducciones')
        self.mock_translate = patcher.start()
        self.addCleanup(patcher.stop)

        # Ciudad de prueba
        self.ciudad = Ciudad.objects.create(
            nombre="Granada",
            descripcion="Granada colonial",
            latitud_centro=11.93,
            longitud_centro=-85.95
        )

        # Usuarios de prueba
        self.user_propietario = User.objects.create_user(
            username="propietario_juan",
            email="juan@empresa.com",
            password="Password123!",
            first_name="Juan",
            last_name="Pérez",
            es_protagonista=False,
            es_turista=False
        )

        self.user_editor = User.objects.create_user(
            username="editor_pedro",
            email="pedro@empresa.com",
            password="Password123!",
            first_name="Pedro",
            last_name="Gómez",
            es_protagonista=False,
            es_turista=False
        )

        self.user_turista = User.objects.create_user(
            username="turista_maria",
            email="maria@turista.com",
            password="Password123!",
            first_name="María",
            last_name="López",
            es_protagonista=False,
            es_turista=True
        )

        # Empresa creada por Juan (sin mock en este caso para probar el save() real)
        self.empresa = Empresa.objects.create(
            usuario=self.user_propietario,
            ciudad=self.ciudad,
            nombre="Café El Convento",
            descripcion="Cafetería de especialidad en el centro de Granada",
            categoria="Gastronomia"
        )

    def test_creacion_empresa_asigna_owner_y_hace_protagonista(self):
        """
        Al registrar una Empresa, el creador debe recibir automáticamente el rol OWNER
        y su campo es_protagonista debe pasar a True.
        """
        # Verificar que el usuario propietario ahora es protagonista
        self.user_propietario.refresh_from_db()
        self.assertTrue(self.user_propietario.es_protagonista)

        # Verificar que existe la membresía con rol OWNER
        miembro = EmpresaMiembro.objects.filter(empresa=self.empresa, usuario=self.user_propietario).first()
        self.assertIsNotNone(miembro)
        self.assertEqual(miembro.rol, EmpresaMiembro.ROL_OWNER)

    def test_endpoint_mis_empresas(self):
        """
        GET /api/empresas/mis_empresas/ debe listar las empresas donde el usuario autenticado es miembro.
        """
        self.client.force_authenticate(user=self.user_propietario)
        res = self.client.get('/api/empresas/mis_empresas/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], self.empresa.id)
        self.assertEqual(res.data[0]['nombre'], "Café El Convento")
        self.assertEqual(res.data[0]['rol'], EmpresaMiembro.ROL_OWNER)

        # Para un turista sin empresas debe devolver lista vacía
        self.client.force_authenticate(user=self.user_turista)
        res_turista = self.client.get('/api/empresas/mis_empresas/')
        self.assertEqual(res_turista.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_turista.data), 0)

    def test_agregar_miembro_a_empresa(self):
        """
        El propietario puede agregar un editor a su empresa y este pasa a ser protagonista.
        """
        self.client.force_authenticate(user=self.user_propietario)
        res = self.client.post(f'/api/empresas/{self.empresa.id}/miembros/', {
            'usuario_id': self.user_editor.id,
            'rol': 'EDITOR'
        }, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['rol'], 'EDITOR')

        # El editor ahora debe figurar como protagonista
        self.user_editor.refresh_from_db()
        self.assertTrue(self.user_editor.es_protagonista)

        # Un turista ajeno no puede agregar miembros (403)
        self.client.force_authenticate(user=self.user_turista)
        res_forbidden = self.client.post(f'/api/empresas/{self.empresa.id}/miembros/', {
            'usuario_id': self.user_turista.id,
            'rol': 'ADMIN'
        }, format='json')
        self.assertEqual(res_forbidden.status_code, status.HTTP_403_FORBIDDEN)

    def test_publicacion_personal_usuario(self):
        """
        Sin encabezado X-Company-Id, la publicación se crea en modo personal (tipo_autor = 'USUARIO').
        """
        self.client.force_authenticate(user=self.user_turista)
        payload = {
            'descripcion': '¡Qué bella es la ciudad de Granada!'
        }
        res = self.client.post('/api/publicaciones/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['tipo_autor'], 'USUARIO')
        self.assertIsNone(res.data['empresa_id'])
        self.assertEqual(res.data['autor_nombre'], "María López")
        self.assertEqual(res.data['creado_por'], self.user_turista.id)

    def test_publicacion_con_contexto_empresa_header(self):
        """
        Con encabezado X-Company-Id, la publicación se crea en nombre de la empresa (tipo_autor = 'EMPRESA').
        """
        self.client.force_authenticate(user=self.user_propietario)
        payload = {
            'titulo': 'Nuevo Menú de Café',
            'descripcion': 'Ven a probar nuestro nuevo capuchino con canela.'
        }
        # Enviar con el header X-Company-Id
        res = self.client.post(
            '/api/publicaciones/',
            payload,
            format='json',
            HTTP_X_COMPANY_ID=str(self.empresa.id)
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['tipo_autor'], 'EMPRESA')
        self.assertEqual(res.data['empresa_id'], self.empresa.id)
        self.assertEqual(res.data['empresa_nombre'], "Café El Convento")
        self.assertEqual(res.data['autor_nombre'], "Café El Convento")
        self.assertEqual(res.data['creado_por'], self.user_propietario.id)
        self.assertEqual(res.data['creado_por_username'], "propietario_juan")

    def test_publicacion_empresa_no_autorizada_retorna_403(self):
        """
        Si un usuario intenta enviar X-Company-Id de una empresa a la que no pertenece, recibe 403.
        """
        self.client.force_authenticate(user=self.user_turista)
        payload = {
            'descripcion': 'Intento publicar a nombre de otra empresa'
        }
        res = self.client.post(
            '/api/publicaciones/',
            payload,
            format='json',
            HTTP_X_COMPANY_ID=str(self.empresa.id)
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_edicion_publicacion_empresa_por_miembro(self):
        """
        Un post hecho a nombre de la empresa puede ser editado por otro miembro de la empresa,
        pero no por un usuario no perteneciente a la misma.
        """
        # Asociar al editor
        EmpresaMiembro.objects.create(
            empresa=self.empresa,
            usuario=self.user_editor,
            rol=EmpresaMiembro.ROL_EDITOR
        )

        # Crear publicación de la empresa
        pub = Publicacion.objects.create(
            autor=self.user_propietario,
            creado_por=self.user_propietario,
            empresa=self.empresa,
            tipo_autor='EMPRESA',
            descripcion="Post original de la empresa"
        )

        # El editor intenta modificar la publicación de la empresa
        self.client.force_authenticate(user=self.user_editor)
        res_edit = self.client.patch(
            f'/api/publicaciones/{pub.id}/',
            {'descripcion': 'Post editado por el editor'},
            format='json'
        )
        self.assertEqual(res_edit.status_code, status.HTTP_200_OK)
        self.assertEqual(res_edit.data['descripcion'], 'Post editado por el editor')

        # Un turista intenta editar la publicación de la empresa (403)
        self.client.force_authenticate(user=self.user_turista)
        res_fail = self.client.patch(
            f'/api/publicaciones/{pub.id}/',
            {'descripcion': 'Hackeando post'},
            format='json'
        )
        self.assertEqual(res_fail.status_code, status.HTTP_403_FORBIDDEN)

    def test_creacion_evento_con_contexto_empresa(self):
        """
        Al crear un evento con encabezado X-Company-Id, el evento queda asociado automáticamente a la empresa.
        """
        self.client.force_authenticate(user=self.user_propietario)
        payload = {
            'titulo': 'Noche de Café y Poesía',
            'descripcion': 'Evento cultural en el café',
            'fecha_inicio': '2026-10-15T18:00:00Z',
            'ubicacion': 'Calle El Consulado, Granada'
        }
        res = self.client.post(
            '/api/eventos/',
            payload,
            format='json',
            HTTP_X_COMPANY_ID=str(self.empresa.id)
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['empresa'], self.empresa.id)
        self.assertEqual(res.data['empresa_nombre'], "Café El Convento")
