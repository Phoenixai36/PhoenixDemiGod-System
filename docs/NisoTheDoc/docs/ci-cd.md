# Documentación del Pipeline de CI/CD

Este documento describe el pipeline de Integración y Despliegue Continuo (CI/CD) del proyecto.

## Disparadores (Triggers)

El pipeline se activa automáticamente en los siguientes eventos:

- **push**: Cada vez que se suben cambios a la rama `main`.
- **pull_request**: Cada vez que se crea o actualiza un Pull Request dirigido a la rama `main`.

## Trabajos (Jobs)

El pipeline consta de tres trabajos (`jobs`) que se ejecutan en paralelo para optimizar el tiempo de feedback.

### 1. `format` (Formateo de Código)

Este trabajo verifica que todo el código Rust del proyecto siga las guías de estilo estándar.

- **Runner**: `ubuntu-latest`
- **Pasos**:
  1. **Checkout**: Clona el repositorio.
  2. **Instalar toolchain de Rust**: Instala la versión estable de Rust y el componente `rustfmt`.
  3. **Verificar formateo**: Ejecuta `cargo fmt -- --check` para asegurarse de que el código está correctamente formateado. Si el comando encuentra código que no cumple con el formato, el trabajo falla.

### 2. `lint` (Análisis Estático de Código)

Este trabajo utiliza Clippy, el linter de Rust, para detectar errores comunes y código no idiomático.

- **Runner**: `ubuntu-latest`
- **Pasos**:
  1. **Checkout**: Clona el repositorio.
  2. **Instalar toolchain de Rust**: Instala la versión estable de Rust y el componente `clippy`.
  3. **Cacheo de dependencias**: Restaura la caché de las dependencias de Cargo para acelerar la ejecución. La caché se basa en el contenido del archivo `Cargo.lock`.
  4. **Ejecutar Linter**: Ejecuta `cargo clippy -- -D warnings` para analizar el código. La opción `-D warnings` trata las advertencias como errores, haciendo que el trabajo falle si se encuentra alguna.

### 3. `test` (Tests y Cobertura)

Este trabajo ejecuta la suite de tests y genera un informe de cobertura de código.

- **Runner**: `ubuntu-latest`
- **Pasos**:
  1. **Checkout**: Clona el repositorio.
  2. **Instalar toolchain de Rust**: Instala la versión estable de Rust.
  3. **Instalar tarpaulin**: Instala `cargo-tarpaulin`, la herramienta para medir la cobertura de tests.
  4. **Cacheo de dependencias**: Restaura la caché de las dependencias de Cargo.
  5. **Generar reporte de cobertura**: Ejecuta los tests y genera un informe de cobertura en formato XML (`cobertura.xml`).
  6. **Subir artefacto de cobertura**: Sube el informe de cobertura como un artefacto del workflow. Este artefacto puede ser descargado y utilizado por otras herramientas o para análisis manual.

## Interpretación de Resultados

- Si todos los trabajos finalizan con éxito, significa que el código está bien formateado, no tiene lints, y todos los tests pasan.
- Si alguno de los trabajos falla, se debe revisar el log correspondiente para identificar y corregir el problema antes de volver a integrar los cambios.

## 🛡️ Seguridad en el Pipeline

**Advertencia de Seguridad:** Bajo ninguna circunstancia se deben imprimir secretos, tokens, claves de API o cualquier otra credencial en los logs del pipeline.

Los trabajos de CI/CD están configurados para fallar si detectan código que no cumple con las guías, pero es responsabilidad del desarrollador asegurarse de que el código no exponga información sensible.

- **Utiliza Secretos de GitHub/GitLab:** Almacena las credenciales como secretos en la configuración del repositorio de CI/CD y úsalas como variables de entorno en los trabajos.
- **Enmascaramiento de Logs:** Asegúrate de que las herramientas de CI/CD enmascaren automáticamente los secretos en la salida de los logs.
- **Revisión de Scripts:** Audita regularmente los scripts de despliegue y los comandos del pipeline para prevenir la exposición accidental de datos.
