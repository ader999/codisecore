import logging
import requests
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Mapeo de códigos de idioma estandarizados
IDIOMAS_SOPORTADOS = {
    'en': 'en',        # Inglés
    'zh': 'zh-CN',     # Chino Mandarín Simplificado
    'zh-cn': 'zh-CN',
    'zh-hans': 'zh-CN',
    'es': 'es',        # Español
}

# Caché en memoria para evitar peticiones duplicadas durante la ejecución
_TRADUCCIONES_CACHE: Dict[str, str] = {}


def obtener_codigo_traductor(codigo_idioma: str) -> Optional[str]:
    """Normaliza un código de idioma (ej. 'zh-hans' -> 'zh-CN', 'en' -> 'en')."""
    if not codigo_idioma:
        return None
    cod = codigo_idioma.lower().strip()
    cod = cod.split(';')[0].split(',')[0].strip()
    if cod in IDIOMAS_SOPORTADOS:
        return IDIOMAS_SOPORTADOS[cod]
    prefijo = cod[:2]
    return IDIOMAS_SOPORTADOS.get(prefijo)


def _traducir_con_gtx(texto: str, target: str, source: str = 'es') -> Optional[str]:
    """
    Traduce usando el endpoint público de Google Translate GTX.
    Retorna None si ocurre algún error de conexión.
    """
    try:
        url = 'https://translate.googleapis.com/translate_a/single'
        params = {
            'client': 'gtx',
            'sl': source,
            'tl': target,
            'dt': 't',
            'q': texto
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }
        resp = requests.get(url, params=params, headers=headers, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            traducido = ''.join([part[0] for part in data[0] if part and len(part) > 0 and part[0]])
            if traducido and traducido.strip():
                return traducido.strip()
    except Exception as e:
        logger.debug(f"GTX falló para '{texto[:20]}...': {e}")
    return None


def _traducir_con_mymemory(texto: str, target: str, source: str = 'es') -> Optional[str]:
    """
    Fallback usando MyMemoryTranslator de deep-translator.
    """
    try:
        from deep_translator import MyMemoryTranslator
        # Ajustar códigos para MyMemory (requiere pares con país o estándar)
        source_mm = 'es-ES' if source == 'es' else source
        target_mm = 'en-GB' if target == 'en' else ('zh-CN' if 'zh' in target else target)
        res = MyMemoryTranslator(source=source_mm, target=target_mm).translate(texto)
        if res and res.strip():
            return res.strip()
    except Exception as e:
        logger.debug(f"MyMemory falló para '{texto[:20]}...': {e}")
    return None


def traducir_texto(texto: str, target: str = 'en', source: str = 'es') -> str:
    """
    Traduce un texto desde el idioma origen al idioma destino (inglés o chino mandarín).
    Utiliza Google GTX con fallback a MyMemory.
    Si ambos fallan o no hay conexión, devuelve el texto original en español como fallback seguro.
    """
    if not texto or not texto.strip():
        return texto or ""

    texto_limpio = texto.strip()
    target_norm = obtener_codigo_traductor(target) or 'en'
    source_norm = obtener_codigo_traductor(source) or 'es'

    if target_norm == source_norm:
        return texto_limpio

    cache_key = f"{source_norm}:{target_norm}:{texto_limpio}"
    if cache_key in _TRADUCCIONES_CACHE:
        return _TRADUCCIONES_CACHE[cache_key]

    # Intento 1: Google GTX
    resultado = _traducir_con_gtx(texto_limpio, target=target_norm, source=source_norm)

    # Intento 2: MyMemory (fallback)
    if not resultado:
        resultado = _traducir_con_mymemory(texto_limpio, target=target_norm, source=source_norm)

    if resultado:
        _TRADUCCIONES_CACHE[cache_key] = resultado
        return resultado

    # Fallback seguro: devolver el texto original
    logger.warning(f"[Traducción] No se pudo traducir a {target_norm}, usando texto original.")
    return texto_limpio


def auto_completar_traducciones(instancia, campos: list[str], force: bool = False) -> bool:
    """
    Examina los campos en español de una instancia de modelo. Si los campos _en o _zh
    están vacíos (o si force=True), genera y asigna las traducciones automáticamente.
    """
    cambios = False
    for campo in campos:
        valor_es = getattr(instancia, campo, None)
        if not valor_es:
            continue

        # Campo en Inglés
        campo_en = f"{campo}_en"
        if hasattr(instancia, campo_en):
            valor_actual_en = getattr(instancia, campo_en)
            if not valor_actual_en or force:
                traduccion_en = traducir_texto(valor_es, target='en', source='es')
                setattr(instancia, campo_en, traduccion_en)
                cambios = True

        # Campo en Chino Mandarín
        campo_zh = f"{campo}_zh"
        if hasattr(instancia, campo_zh):
            valor_actual_zh = getattr(instancia, campo_zh)
            if not valor_actual_zh or force:
                traduccion_zh = traducir_texto(valor_es, target='zh-CN', source='es')
                setattr(instancia, campo_zh, traduccion_zh)
                cambios = True

    return cambios
