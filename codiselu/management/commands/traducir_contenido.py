from django.core.management.base import BaseCommand
from codiselu.models import (
    Ciudad, CircuitoCreativo, PuntoInteres, DatoHistorico,
    Empresa, OportunidadInversion, Evento
)
from codiselu.translation_service import auto_completar_traducciones


class Command(BaseCommand):
    help = "Traduce automáticamente a Inglés y Chino Mandarín el contenido dinámico existente en la base de datos."

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la re-traducción de registros incluso si ya tienen traducciones previas.',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        self.stdout.write(self.style.NOTICE("Iniciando proceso de traducción automática (Español -> Inglés y Mandarín)..."))

        modelos = [
            (Ciudad, ['nombre', 'descripcion'], 'Ciudades'),
            (CircuitoCreativo, ['nombre', 'descripcion'], 'Circuitos Creativos'),
            (PuntoInteres, ['nombre', 'descripcion'], 'Puntos de Interés'),
            (DatoHistorico, ['titulo', 'contenido'], 'Datos Históricos'),
            (Empresa, ['nombre', 'descripcion'], 'Empresas'),
            (OportunidadInversion, ['titulo', 'descripcion'], 'Oportunidades de Inversión'),
            (Evento, ['titulo', 'descripcion'], 'Eventos'),
        ]

        total_traducidos = 0

        for model_cls, campos, nombre_plural in modelos:
            qs = model_cls.objects.all()
            count_model = 0
            self.stdout.write(f"Procesando {nombre_plural} ({qs.count()} encontrados)...")

            for item in qs:
                cambio = auto_completar_traducciones(item, campos, force=force)
                if cambio:
                    item.save()
                    count_model += 1
                    total_traducidos += 1

            self.stdout.write(self.style.SUCCESS(f"  -> {count_model} {nombre_plural} actualizados."))

        self.stdout.write(self.style.SUCCESS(f"\n¡Traducción completada con éxito! Total de registros procesados/actualizados: {total_traducidos}"))
