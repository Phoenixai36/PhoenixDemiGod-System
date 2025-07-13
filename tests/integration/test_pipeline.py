import pytest

# Ejemplo de prueba de integración para el pipeline principal

def test_pipeline_end_to_end():
    """
    Prueba básica de integración: ejecuta el pipeline principal y verifica que produce una salida válida.
    Modifica este test según la interfaz real de tu pipeline.
    """
    try:
        # Importa el agente principal o pipeline según tu arquitectura
        from BooPhoenix369.src.core.demigod_agent import DemigodAgent
        agent = DemigodAgent()
        # Ejecuta el pipeline con un input de prueba
        result = agent.run_pipeline("input de prueba")
        assert result is not None
    except ImportError:
        pytest.skip("No se pudo importar el pipeline principal. Ajusta el import según tu estructura.")
    except Exception as e:
        pytest.fail(f"Error inesperado al ejecutar el pipeline: {e}")
