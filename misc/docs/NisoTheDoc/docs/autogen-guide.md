# Guía de AutoGen

## Propósito
AutoGen es un sistema diseñado para la generación automática de diversos artefactos del proyecto, incluyendo scripts de automatización, documentación técnica y casos de prueba. Su objetivo principal es acelerar el desarrollo y mantener la consistencia, reduciendo la carga manual y minimizando errores.

## Uso
### Generación de Scripts
Para generar un script, puedes usar el siguiente comando `curl`, reemplazando `${AUTO_GEN_ENDPOINT}` con la URL de tu servicio AutoGen:
```bash
curl -X POST "${AUTO_GEN_ENDPOINT}" -H "Content-Type: application/json" -d '{"prompt":"Genera un script Bash para desplegar una aplicación Node.js", "task":"script"}'
```
El campo `prompt` debe describir claramente el script deseado, y el campo `task` especifica el tipo de artefacto a generar (en este caso, "script").

### Generación de Documentación
Para generar documentación, como una guía de usuario o una descripción de una API, utiliza el siguiente formato:
```bash
curl -X POST "${AUTO_GEN_ENDPOINT}" -H "Content-Type: application/json" -d '{"prompt":"Crea la documentación para el módulo de memoria", "task":"documentation"}'
```
El sistema intentará generar un documento Markdown basado en la descripción proporcionada.

### Generación de Pruebas
AutoGen también puede generar casos de prueba para módulos específicos. Por ejemplo, para generar pruebas para el `demigod-agent`:
```bash
curl -X POST "${AUTO_GEN_ENDPOINT}" -H "Content-Type: application/json" -d '{"prompt":"Genera pruebas unitarias para el demigod-agent", "task":"test"}'
```
Las pruebas generadas seguirán las convenciones del proyecto y se almacenarán en el directorio `autogen/tests/`.

## Configuración
El comportamiento de AutoGen se puede ajustar a través de variables de entorno y archivos de configuración internos. Asegúrate de que `AUTO_GEN_ENDPOINT` esté correctamente configurado en tu archivo `.env`.