"""
Métricas de Prometheus para Phoenix DemiGod.

Este módulo centraliza la definición de todas las métricas de Prometheus
para facilitar su gestión y reutilización a través del sistema.
"""

try:
    from prometheus_client import Counter, Histogram, Gauge
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

# --- Definición de Métricas ---

# Contador para el número total de inferencias.
# Etiquetas:
# - model: El nombre del modelo utilizado (e.g., "devstral", "llama3.2-3b").
# - task_type: El tipo de tarea para la que se realizó la inferencia (e.g., "code_analysis").
INFERENCE_COUNTER = Counter(
    'phoenix_inferences_total',
    'Número total de inferencias procesadas',
    ['model', 'task_type']
) if PROMETHEUS_AVAILABLE else None

# Histograma para la duración de las inferencias.
# Mide la latencia de las respuestas del modelo en segundos.
# Etiquetas:
# - model: El nombre del modelo para el cual se mide la duración.
INFERENCE_DURATION = Histogram(
    'phoenix_inference_duration_seconds',
    'Duración de la inferencia en segundos',
    ['model']
) if PROMETHEUS_AVAILABLE else None

# Gauge para el consumo de energía.
# Mide el consumo de energía estimado por inferencia en vatios-hora (Wh).
# No tiene etiquetas, ya que representa el consumo instantáneo o más reciente.
ENERGY_GAUGE = Gauge(
    'phoenix_energy_consumption_wh',
    'Consumo de energía por inferencia en Wh'
) if PROMETHEUS_AVAILABLE else None

# Contador para los fallbacks de modelo.
# Registra cuándo un modelo principal falla y se utiliza un modelo de respaldo.
# Etiquetas:
# - from_model: El modelo que falló originalmente.
# - to_model: El modelo de fallback que se utilizó en su lugar.
FALLBACK_COUNTER = Counter(
    'phoenix_fallbacks_total',
    'Número total de fallbacks de modelo',
    ['from_model', 'to_model']
) if PROMETHEUS_AVAILABLE else None

def get_metrics_definitions():
    """
    Devuelve un diccionario con todas las métricas definidas.
    Esto puede ser útil para registrar o verificar las métricas dinámicamente.
    """
    if not PROMETHEUS_AVAILABLE:
        return {}
    return {
        "inferences_total": INFERENCE_COUNTER,
        "inference_duration_seconds": INFERENCE_DURATION,
        "energy_consumption_wh": ENERGY_GAUGE,
        "fallbacks_total": FALLBACK_COUNTER,
    }
