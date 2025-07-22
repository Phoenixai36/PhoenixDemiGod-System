---
> **IMPORTANTE: NisoTheDoc es la fuente de verdad y contexto central para toda la arquitectura, automatización, onboarding y evolución del sistema Phoenix.**
> 
> - Toda decisión relevante, integración, refactorización o blueprint debe estar reflejada aquí.
> - Usa este directorio como punto de partida para cualquier tarea de desarrollo, auditoría o troubleshooting.
> - Mantén esta documentación siempre actualizada y enlazada con los archivos clave del repositorio.
---

# Sugerencias de Limpieza y Optimización de Arquitectura

## Recomendaciones Generales (2025)

### 1. Centralización y Documentación de Configuración
- Unificar variables comunes en un solo archivo `.env` principal.
- Mantener archivos `.env` específicos solo para configuraciones avanzadas y documentar su propósito.
- Elegir entre `config.yaml` o `config.json` como archivo principal de configuración (preferiblemente YAML).
- Documentar la estructura y propósito de cada archivo de configuración en `NisoTheDoc/docs/configuracion.md`.

### 2. Organización de la Carpeta `models`
- Renombrar `models/models/` a `models/blobs/` y mover el contenido.
- Evitar almacenar claves privadas en la carpeta de modelos; deben ir en un directorio seguro fuera del control de versiones.

### 3. Limpieza de Dependencias
- Revisar y limpiar `requirements.txt` y `pyproject.toml` para eliminar paquetes no utilizados.
- Documentar dependencias esenciales y opcionales en `NisoTheDoc/docs/dependency-refactoring-plan.md`.

---

# Sugerencias de Limpieza de Repositorio

A continuación se presenta una lista de archivos y directorios que se sugiere eliminar o archivar para mantener el repositorio limpio y organizado.

## Archivos de Respaldo

- [`BooPhoenix369/terraform.tfstate.backup`](BooPhoenix369/terraform.tfstate.backup:1): Archivo de respaldo de estado de Terraform. Generalmente, estos archivos no se versionan y pueden contener información sensible.

## Directorio de Notas y Borradores (`Niso`)

El directorio [`BooPhoenix369/Niso/`](BooPhoenix369/Niso/) parece contener una gran cantidad de notas personales, borradores de documentación y scripts experimentales que no forman parte del código fuente final de la aplicación. Se recomienda revisar y archivar o eliminar todo el directorio para reducir el ruido en el repositorio.

**Archivos específicos notables dentro de `Niso`:**

- **Documentos de texto y Markdown:** Archivos como [`ADIEU.md`](BooPhoenix369/Niso/ADIEU.md:1), [`BOBOBO.md`](BooPhoenix369/Niso/BOBOBO.md:1), [`goddmn.txt`](BooPhoenix369/Niso/goddmn.txt:1), y muchos otros con nombres informales o en español parecen ser notas o borradores.
- **Scripts experimentales:** Archivos como [`chart_script_1.py`](BooPhoenix369/Niso/chart_script_1.py:1), [`chart_script.py`](BooPhoenix369/Niso/chart_script.py:1), y [`phoenix_mcp_router.py`](BooPhoenix369/Niso/phoenix_mcp_router.py:1) parecen ser scripts de prueba o experimentales que no están integrados en la aplicación principal.
- **Archivos de configuración duplicados o de prueba:** Archivos como [`package.json`](BooPhoenix369/Niso/package.json:1) y [`gitignore`](BooPhoenix369/Niso/gitignore:1) dentro de este directorio son probablemente innecesarios.


---

## Limpieza de Código Muerto y Refactorización Avanzada

### Automatización de limpieza
- Ejecuta el script `scripts/ci_dead_code_check.sh` para generar un reporte de funciones, clases e imports no utilizados.
- El reporte se guarda en `reports/dead_code_report.txt`.
- Revisa el reporte y elimina el código marcado como muerto tras validar que no es necesario.

### Checklist de limpieza y refactorización
- [ ] Revisar y eliminar funciones, clases e imports no usados.
- [ ] Aplicar `autoflake`, `isort` y `black` para limpieza y formato automático.
- [ ] Añadir tests antes/después de refactorizar.
- [ ] Documentar cambios mayores en `NisoTheDoc`.
- [ ] Verificar que todos los tests y linting pasen antes de hacer deploy.

### Comandos útiles
```bash
autoflake --remove-all-unused-imports --in-place --recursive src/
isort src/
black src/
```

### Recomendación
Antes de eliminar cualquier código, asegúrate de que no sea utilizado por módulos externos, tests o scripts de integración. Documenta siempre los cambios relevantes para mantener la trazabilidad en el equipo.


---

## Deploy Final: Checklist y Guía

### Checklist previo al deploy
- [ ] Todos los tests automatizados y chequeos de linting pasan correctamente.
- [ ] La cobertura de código cumple el mínimo requerido (>80% en módulos críticos).
- [ ] El reporte de código muerto ha sido revisado y eliminado lo innecesario.
- [ ] Documentación y dependencias actualizadas en `NisoTheDoc`.
- [ ] Artefactos de build generados y verificados si aplica (Docker, wheels, etc.).
- [ ] Variables de entorno y secretos correctamente gestionados (sin claves privadas en el repo).

### Comandos recomendados para deploy
```bash
# Ejecutar tests y linting
pytest --cov=src
flake8 src/

# Build de artefactos (ejemplo Docker)
docker build -t phoenixdemigod:latest .

# Despliegue local o en servidor
# (Ajustar según tu stack: Podman, Docker Compose, Kubernetes, etc.)
```

### Recomendación
Realiza siempre un deploy primero en entorno de staging. Verifica logs y monitoreo tras el despliegue. Documenta cualquier incidencia o ajuste en `NisoTheDoc` para futuras iteraciones.

---
- [`BooPhoenix369/tree.file.txt`](BooPhoenix369/tree.file.txt:1): Similar al anterior, parece ser otro volcado de la estructura de archivos.

Se recomienda que el equipo de desarrollo revise estas sugerencias y decida qué archivos deben ser eliminados o archivados fuera del repositorio principal.

---

## Guía de Deploy Final

1.  Pasar todos los tests y chequeos de linting:
    *   Comando: `npm test` (o `yarn test`, dependiendo del gestor de paquetes)
    *   Verificar que todos los tests pasen sin errores.
    *   Comando: `npm run lint` (o `yarn lint`)
    *   Asegurarse de que no haya errores de linting.

2.  Verificar la cobertura de código:
    *   Comando: `npm run coverage` (o `yarn coverage`, o el comando específico configurado en el proyecto)
    *   Revisar el reporte de cobertura para asegurar que se cumplan los umbrales definidos.

3.  Generar los artefactos/productos finales (si aplica):
    *   Comando: `npm run build` (o `yarn build`, o el comando específico para generar los artefactos)
    *   Verificar que los artefactos se generen correctamente en el directorio de salida (ej., `dist`, `build`).

4.  Ejecutar el script de deploy (documentar el proceso):
    *   Comando: `./scripts/deploy.sh` (o el comando específico para ejecutar el script de deploy)
    *   Documentar el proceso de deploy en `NisoTheDoc/docs/cleanup-suggestions.md`, incluyendo:
        *   Pre-requisitos (ej., variables de entorno, credenciales).
        *   Pasos para ejecutar el script.
        *   Verificación del deploy exitoso (ej., acceso a la aplicación, chequeo de logs).
