# utils.py
# Utilidades generales
import logging
import sys

# Configuración básica de logging para que imprima en la consola.
# En una aplicación real, esto podría ser mucho más complejo, leyendo
# la configuración desde un archivo.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)


def log(message, level=logging.INFO):
    """Función de utilidad para registrar mensajes con el sistema de logging."""
    # Llama al sistema de logging de Python con el nivel y mensaje proporcionados.
    logging.log(level, message)


if __name__ == "__main__":
    print("Ejecutando pruebas para utils.py...")
    log("Este es un mensaje de información (por defecto).")
    log("Este es un mensaje de advertencia.", level=logging.WARNING)
