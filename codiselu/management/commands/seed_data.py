from django.core.management.base import BaseCommand
from codiselu.models import User, Ciudad, CircuitoCreativo, PuntoInteres, DatoHistorico, GaleriaMultimedia

class Command(BaseCommand):
    help = "Populates database with sample Users, Ciudades Creativas de Nicaragua, Circuitos, Puntos de Interés, Datos Históricos y Galería."

    def handle(self, *args, **options):
        self.stdout.write("Seeding sample data for Ciudades Creativas de Nicaragua...")

        # 1. Users (10)
        users_data = [
            {"username": "ana_arte", "email": "ana@example.com", "first_name": "Ana", "last_name": "García", "es_protagonista": True, "es_turista": False, "telefono": "+50588880001"},
            {"username": "carlos_turista", "email": "carlos@example.com", "first_name": "Carlos", "last_name": "Mendoza", "es_protagonista": False, "es_turista": True, "telefono": "+50588880002"},
            {"username": "maria_creativa", "email": "maria@example.com", "first_name": "María", "last_name": "Rodríguez", "es_protagonista": True, "es_turista": True, "telefono": "+50588880003"},
            {"username": "luis_explorador", "email": "luis@example.com", "first_name": "Luis", "last_name": "Morales", "es_protagonista": False, "es_turista": True, "telefono": "+50588880004"},
            {"username": "sofia_diseno", "email": "sofia@example.com", "first_name": "Sofía", "last_name": "Chaves", "es_protagonista": True, "es_turista": False, "telefono": "+50588880005"},
        ]

        for u in users_data:
            user, created = User.objects.get_or_create(
                username=u["username"],
                defaults={
                    "email": u["email"],
                    "first_name": u["first_name"],
                    "last_name": u["last_name"],
                    "es_protagonista": u["es_protagonista"],
                    "es_turista": u["es_turista"],
                    "telefono": u["telefono"],
                }
            )
            if created:
                user.set_password("Pass1234!")
                user.save()

        # 2. Ciudades Creativas de Nicaragua (10)
        ciudades_data = [
            {"nombre": "León", "descripcion": "Ciudad universitaria y capital cultural, cuna de poetas y arquitectura colonial.", "latitud_centro": 12.4379, "longitud_centro": -86.8780},
            {"nombre": "Masaya", "descripcion": "Capital del folclore nicaragüense, cuna de artesanías, marimbas y tradición.", "latitud_centro": 11.9744, "longitud_centro": -86.0942},
            {"nombre": "Granada", "descripcion": "La Gran Sultana, célebre por su arquitectura colonial, isletas y gastronomía.", "latitud_centro": 11.9299, "longitud_centro": -85.9560},
            {"nombre": "Estelí", "descripcion": "Diamante de las Segovias, famosa por su muralismo urbano y tabaco artesanal.", "latitud_centro": 13.0918, "longitud_centro": -86.3538},
            {"nombre": "Managua", "descripcion": "Capital creativa y centro cultural vibrante a orillas del lago Xolotlán.", "latitud_centro": 12.1364, "longitud_centro": -86.2514},
            {"nombre": "Nagarote", "descripcion": "Ciudad limpia y taurina, conocida por su queso quesillo tradicional y parques.", "latitud_centro": 12.2659, "longitud_centro": -86.5647},
            {"nombre": "San Juan de Oriente", "descripcion": "Cuna de la cerámica utilitaria y artística precolombina de Nicaragua.", "latitud_centro": 11.9061, "longitud_centro": -86.0740},
            {"nombre": "Juigalpa", "descripcion": "Capital chontaleña de la cultura ganadera, petroglifos y museos.", "latitud_centro": 12.1063, "longitud_centro": -85.3646},
            {"nombre": "Matagalpa", "descripcion": "La Perla del Septentrión, conocida por su producción de café y patrimonio de montaña.", "latitud_centro": 12.9256, "longitud_centro": -85.9178},
            {"nombre": "Bluefields", "descripcion": "Capital de la Costa Caribe Sur, riqueza pluriétnica, mayo ya y calipso.", "latitud_centro": 12.0137, "longitud_centro": -83.7635},
        ]

        nombres_validos = [c["nombre"] for c in ciudades_data]
        Ciudad.objects.exclude(nombre__in=nombres_validos).delete()

        ciudades_instances = {}
        for c in ciudades_data:
            ciudad, _ = Ciudad.objects.get_or_create(
                nombre=c["nombre"],
                defaults={
                    "descripcion": c["descripcion"],
                    "latitud_centro": c["latitud_centro"],
                    "longitud_centro": c["longitud_centro"],
                }
            )
            ciudades_instances[c["nombre"]] = ciudad


        # 3. Circuitos Creativos
        leon = ciudades_instances.get("León")
        masaya = ciudades_instances.get("Masaya")

        circuito_leon, _ = CircuitoCreativo.objects.get_or_create(
            ciudad=leon,
            nombre="Ruta de los Poetasy Murales Históricos",
            defaults={
                "descripcion": "Un recorrido caminando por la arquitectura colonial, murales cívicos y la casa museo Rubén Darío.",
                "distancia_km": 3.20,
                "duracion_estimada": "2 horas",
                "dificultad": "Baja",
            }
        )

        circuito_masaya, _ = CircuitoCreativo.objects.get_or_create(
            ciudad=masaya,
            nombre="Circuito de Artesanías y Saberes Populares",
            defaults={
                "descripcion": "Recorrido inmersivo por talleres de hamacas, calzado artesanal y el Mercado de Artesanías.",
                "distancia_km": 2.50,
                "duracion_estimada": "1.5 horas",
                "dificultad": "Baja",
            }
        )

        # 4. Puntos de Interés
        p1, _ = PuntoInteres.objects.get_or_create(
            circuito=circuito_leon,
            nombre="Insigne y Real Basílica Catedral de León",
            defaults={
                "descripcion": "Patrimonio de la Humanidad por la UNESCO. Sitio emblemático de arquitectura barroca y neoclásica.",
                "tipo": "Historico",
                "orden": 1,
                "latitud": 12.4350,
                "longitud": -86.8790,
            }
        )

        p2, _ = PuntoInteres.objects.get_or_create(
            circuito=circuito_leon,
            nombre="Casa Museo Rubén Darío",
            defaults={
                "descripcion": "Casa donde creció el Príncipe de las Letras Castellanas, conservando manuscritos e información histórica.",
                "tipo": "Cultural",
                "orden": 2,
                "latitud": 12.4370,
                "longitud": -86.8770,
            }
        )

        # 5. Múltiples Datos Históricos (Asociados a Ciudad y a Puntos de Interés)
        DatoHistorico.objects.get_or_create(
            ciudad=leon,
            titulo="Fundación de León y Traslado desde León Viejo",
            defaults={
                "tipo": "Hito",
                "epoca_o_ano": "1610",
                "contenido": "Tras la erupción del volcán Momotombo y terremotos en 1610, la ciudad de León se trasladó a su ubicación actual al lado del poblado indígena de Subtiava."
            }
        )

        DatoHistorico.objects.get_or_create(
            ciudad=leon,
            titulo="La Gigantona y el Pepe Cabezón",
            defaults={
                "tipo": "Leyenda",
                "epoca_o_ano": "Época Colonial",
                "contenido": "Expresión folclórica y satírica surgida en León donde la Gigantona representa a la mujer española y el Pepe Cabezón al mestizo o criollo."
            }
        )

        DatoHistorico.objects.get_or_create(
            punto_interes=p1,
            titulo="Tumba del Poeta Rubén Darío en la Catedral",
            defaults={
                "tipo": "Hito",
                "epoca_o_ano": "1916",
                "contenido": "Bajo la estatua de un león doliente esculpido por el italiano Jorge Navas Cordonero descansan los restos del célebre poeta Rubén Darío."
            }
        )

        # 6. Múltiples Galerías Multimedia (Imágenes y Videos)
        GaleriaMultimedia.objects.get_or_create(
            ciudad=leon,
            titulo="Panorámica del Centro Histórico de León",
            defaults={
                "tipo": "Imagen",
                "video_url": None,
            }
        )

        GaleriaMultimedia.objects.get_or_create(
            ciudad=leon,
            titulo="Documental: León, Cuna de la Revolución y Poesía",
            defaults={
                "tipo": "Video",
                "video_url": "https://www.youtube.com/watch?v=ejemplo_leon_creativo",
            }
        )

        GaleriaMultimedia.objects.get_or_create(
            punto_interes=p2,
            titulo="Manuscritos originales de Rubén Darío",
            defaults={
                "tipo": "Imagen",
                "video_url": None,
            }
        )

        self.stdout.write(self.style.SUCCESS("Successfully seeded database with Ciudades Creativas, Circuitos, Puntos, Datos Históricos y Multimedia!"))

