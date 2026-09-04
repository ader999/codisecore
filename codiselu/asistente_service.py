"""
Servicio del Asistente Virtual Inteligente con Google Gemini.
Implementa Function Calling / Tool Calling para interactuar con la base de datos Django en tiempo real,
con soporte multi-idioma, fallback de modelos y geolocalización.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from django.conf import settings
from google import genai
from google.genai import types
from .asistente_tools import TODAS_LAS_HERRAMIENTAS

logger = logging.getLogger(__name__)


class GeminiNoConfiguradoError(Exception):
    """Excepción lanzada cuando GEMINI_API_KEY no está configurada."""
    pass


class AsistenteVirtualService:
    """
    Servicio que gestiona la interacción con los modelos Gemini de Google,
    la ejecución automática de herramientas (Function Calling) y el historial conversacional.
    """

    SYSTEM_INSTRUCTION_BASE = """
Eres Eduardo, el Asistente Virtual Oficial y Guía Turístico de la Red de Ciudades Creativas de Nicaragua (Granada, León, Masaya, Estelí, Bluefields, San Juan de Oriente, etc.).

Tu nombre es Eduardo. Preséntate como Eduardo cuando saludes por primera vez o si te preguntan tu nombre o quién eres.
Tu misión es asistir de manera hospitalaria, entusiasta, cultural y precisa a turistas, ciudadanos y emprendedores que usan la aplicación móvil.

REGLAS DE ACTUACIÓN:
1. IDENTIDAD: Tu nombre es Eduardo. Eres cálido, amable, nicaragüense de corazón y orgulloso de la riqueza cultural, patrimonial y turística de Nicaragua.
2. TIENES HERRAMIENTAS DIRECTAS: Para cualquier pregunta sobre qué hacer, ciudades, circuitos turísticos, sitios históricos, eventos culturales, talleres artesanales o negocios, DEBES usar tus herramientas disponibles para consultar la base de datos oficial.
3. NUNCA INVENTES DATOS: Si no encuentras información exacta con tus herramientas, indícalo amablemente e invita al usuario a consultar otras ciudades o categorías.
4. IDIOMA Y CULTURA: Responde SIEMPRE en el idioma indicado por el usuario (Español, Inglés o Chino Mandarín). Si el usuario escribe en inglés, responde en inglés; si escribe en mandarín, responde en mandarín.
5. COORDENADAS Y DISTANCIAS: Si el usuario proporciona su ubicación geográfica y pregunta por lugares cercanos, usa la herramienta `buscar_puntos_cercanos` e indícale las distancias aproximadas.
6. FORMATO: Emplea un formato limpio, con viñetas claras, emojis alusivos y recomendaciones prácticas (duración, dificultad de senderos, precios si aplica).
"""

    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', '').strip()
        self.primary_model = getattr(settings, 'GEMINI_MODEL', 'gemini-3.1-flash-lite').strip()
        self.fallback_model = getattr(settings, 'GEMINI_FALLBACK_MODEL', 'gemini-3.8-flash').strip()

    def _verificar_api_key(self):
        if not self.api_key or self.api_key == 'tu_api_key_aqui':
            raise GeminiNoConfiguradoError(
                "La clave GEMINI_API_KEY no está configurada en las variables de entorno. "
                "Obtén una clave gratuita en https://aistudio.google.com/app/apikey y colócala en tu archivo .env."
            )

    def _construir_historial_genai(self, historial_recibido: Optional[List[Dict[str, Any]]]) -> List[types.Content]:
        """Convierte el historial recibido del cliente móvil en objetos Content de GenAI."""
        historial_convertido = []
        if not historial_recibido:
            return historial_convertido

        for item in historial_recibido:
            role = item.get('role', 'user')
            # Normalizar roles
            if role in ('user', 'human'):
                role_genai = 'user'
            else:
                role_genai = 'model'

            texto = ""
            if 'parts' in item and isinstance(item['parts'], list):
                partes_texto = []
                for p in item['parts']:
                    if isinstance(p, str):
                        partes_texto.append(p)
                    elif isinstance(p, dict) and 'text' in p:
                        partes_texto.append(p['text'])
                texto = "\n".join(partes_texto)
            elif 'content' in item:
                texto = str(item['content'])
            elif 'mensaje' in item:
                texto = str(item['mensaje'])

            if texto.strip():
                historial_convertido.append(
                    types.Content(
                        role=role_genai,
                        parts=[types.Part.from_text(text=texto)]
                    )
                )

        return historial_convertido

    def _ejecutar_chat_con_modelo(
        self,
        modelo: str,
        mensaje_enriquecido: str,
        historial: List[types.Content],
        idioma: str
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Ejecuta la llamada al modelo específico con herramientas y recolecta las tools usadas."""
        client = genai.Client(api_key=self.api_key)

        instruccion_sistema = (
            f"{self.SYSTEM_INSTRUCTION_BASE}\n\n"
            f"[IDIOMA PREFERIDO DEL USUARIO: {idioma.upper()}]. "
            "Asegúrate de formular tu respuesta final en este idioma."
        )

        config = types.GenerateContentConfig(
            system_instruction=instruccion_sistema,
            tools=TODAS_LAS_HERRAMIENTAS,
            temperature=0.7,
        )

        chat = client.chats.create(
            model=modelo,
            config=config,
            history=historial
        )

        # Enviar mensaje con ejecución automática de tools
        response = chat.send_message(mensaje_enriquecido)

        # Extraer las herramientas que fueron ejecutadas durante la conversación
        herramientas_usadas = []
        try:
            for turn in chat.get_history():
                if turn.parts:
                    for part in turn.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            call = part.function_call
                            args_dict = dict(call.args) if call.args else {}
                            herramientas_usadas.append({
                                "nombre": call.name,
                                "argumentos": args_dict
                            })
        except Exception as e_hist:
            logger.debug(f"No se pudieron extraer herramientas del historial: {e_hist}")

        texto_respuesta = response.text or "No se obtuvo respuesta del asistente."
        return texto_respuesta, herramientas_usadas

    def procesar_mensaje(
        self,
        mensaje: str,
        historial: Optional[List[Dict[str, Any]]] = None,
        idioma: str = 'es',
        ubicacion: Optional[Dict[str, float]] = None,
        usuario = None
    ) -> Dict[str, Any]:
        """
        Punto de entrada principal para procesar una consulta del usuario móvil.
        Implementa fallback automático: intenta primero con GEMINI_MODEL (gemini-3.1-flash-lite)
        y si falla recurre a GEMINI_FALLBACK_MODEL (gemini-3.8-flash).
        """
        self._verificar_api_key()

        # Enriquecer el mensaje con contexto disponible (ubicación, datos de usuario)
        contextos = []
        if ubicacion and 'latitud' in ubicacion and 'longitud' in ubicacion:
            lat = ubicacion['latitud']
            lon = ubicacion['longitud']
            contextos.append(
                f"[Coordenadas GPS actuales del usuario: latitud={lat}, longitud={lon}. "
                "Si solicita recomendaciones cercanas, utiliza la herramienta buscar_puntos_cercanos]"
            )

        if usuario and usuario.is_authenticated:
            tipo_usuario = "Protagonista / Emprendedor" if getattr(usuario, 'es_protagonista', False) else "Turista"
            nombre_completo = usuario.get_full_name() or usuario.username
            contextos.append(f"[Usuario autenticado: {nombre_completo} ({tipo_usuario})]")

        if contextos:
            mensaje_enriquecido = f"{' '.join(contextos)}\n\nConsulta del usuario: {mensaje}"
        else:
            mensaje_enriquecido = mensaje

        historial_genai = self._construir_historial_genai(historial)

        # Intentar modelo principal
        modelo_activo = self.primary_model
        try:
            logger.info(f"Iniciando asistente con modelo principal: '{modelo_activo}'")
            texto_respuesta, herramientas = self._ejecutar_chat_con_modelo(
                modelo=modelo_activo,
                mensaje_enriquecido=mensaje_enriquecido,
                historial=historial_genai,
                idioma=idioma
            )
        except Exception as e_primary:
            logger.warning(
                f"Error con modelo principal '{modelo_activo}': {e_primary}. "
                f"Activando fallback al modelo '{self.fallback_model}'..."
            )
            modelo_activo = self.fallback_model
            try:
                texto_respuesta, herramientas = self._ejecutar_chat_con_modelo(
                    modelo=modelo_activo,
                    mensaje_enriquecido=mensaje_enriquecido,
                    historial=historial_genai,
                    idioma=idioma
                )
            except Exception as e_fallback:
                logger.error(f"Error también con modelo de respaldo '{modelo_activo}': {e_fallback}")
                raise e_fallback

        return {
            "nombre_asistente": "Eduardo",
            "respuesta": texto_respuesta,
            "herramientas_utilizadas": herramientas,
            "modelo_utilizado": modelo_activo,
            "idioma": idioma
        }
