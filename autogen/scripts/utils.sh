#!/bin/bash
# utils.sh
# Funciones de utilidad comunes para los agentes.

PROJECT_ROOT="" # Se establece por load_env para que sea accesible globalmente

# Función para verificar, crear, sincronizar y activar el entorno virtual de Python.
ensure_venv() {
    # Usa las variables de .env o valores por defecto
    local venv_dir="${VENV_DIR:-.venv2}"
    local requirements_file="${REQUIREMENTS_FILE:-requirements.txt}"
    local venv_path="$PROJECT_ROOT/$venv_dir"
    local requirements_path="$PROJECT_ROOT/$requirements_file"
    local receipt_path="$venv_path/.requirements_receipt"

    local python_cmd
    python_cmd=$(command -v python3 || command -v python)
    if [ -z "$python_cmd" ]; then
        log "ERROR: No se encontró 'python' o 'python3'. Por favor, instale Python." "SYSTEM"
        exit 1
    fi

    # 1. Crear venv si no existe
    if [ ! -d "$venv_path" ]; then
        log "Entorno virtual no encontrado. Creando en '$venv_path'..." "SYSTEM"
        "$python_cmd" -m venv "$venv_path"
    fi

    # Determinar la ruta del ejecutable de pip dentro del venv
    local venv_pip_path
    if [[ -f "$venv_path/bin/pip" ]]; then
        venv_pip_path="$venv_path/bin/pip"
    elif [[ -f "$venv_path/Scripts/pip.exe" ]]; then
        venv_pip_path="$venv_path/Scripts/pip.exe"
    else
        log "ERROR: No se pudo encontrar 'pip' en el entorno virtual '$venv_path'." "SYSTEM"
        exit 1
    fi

    # 2. Sincronizar dependencias si requirements.txt ha cambiado
    if [ ! -f "$receipt_path" ] || ! cmp -s "$requirements_path" "$receipt_path"; then
        log "Detectado cambio en dependencias. Instalando/actualizando desde '$requirements_path'..." "SYSTEM"
        "$venv_pip_path" install -r "$requirements_path"
        # Crear un "recibo" para futuras comprobaciones
        cp "$requirements_path" "$receipt_path"
        log "Dependencias sincronizadas." "SYSTEM"
    fi

    # 3. Activar el venv para la sesión actual del script
    local activate_script
    if [[ -f "$venv_path/bin/activate" ]]; then
        activate_script="$venv_path/bin/activate"
    elif [[ -f "$venv_path/Scripts/activate" ]]; then
        activate_script="$venv_path/Scripts/activate"
    else
        log "ERROR: No se pudo encontrar el script 'activate' en el entorno virtual '$venv_path'." "SYSTEM"
        exit 1
    fi

    log "Activando entorno virtual: $activate_script" "SYSTEM"
    source "$activate_script"
}

# Cargar variables de entorno
# Carga el .env y establece PROJECT_ROOT, pero NO activa el venv.
# Es útil para scripts como 'clean.sh' que no necesitan un entorno Python.
load_env_only() {
  # Find the project root by searching upwards from the script that called this function
  # for a marker file, in this case, '.env'.
  local source_dir
  # Note: BASH_SOURCE[1] is the caller of this function.
  source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[1]}")" &> /dev/null && pwd)
  local current_dir="$source_dir"

  while [[ "$current_dir" != "/" ]] && [[ ! -f "$current_dir/.env" ]]; do
    current_dir=$(dirname "$current_dir")
  done

  if [[ -f "$current_dir/.env" ]]; then
    PROJECT_ROOT="$current_dir"
    export PROJECT_ROOT
    # Export variables from .env without sourcing the file directly
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Ignore comments and empty lines
        if [[ ! "$line" =~ ^\s*# ]] && [[ -n "$line" ]]; then
            export "$line"
        fi
    done < "$current_dir/.env"
  else
    echo "ERROR: No se pudo encontrar el archivo .env en '$source_dir' o directorios superiores." >&2
    exit 1
  fi
}

# Carga el .env Y se asegura de que el venv esté listo.
# Esta es la función estándar para la mayoría de los scripts de agentes.
load_env() {
  load_env_only
  # Una vez cargado el .env, nos aseguramos de que el venv exista,
  # esté sincronizado y activado en el PATH.
  ensure_venv # Esta es la nueva función mejorada
}

# Función de logging estructurado
log() {
  local message="${1}"
  # El segundo argumento es el nombre del agente, por defecto es el nombre del script que llama.
  local agent_name="${2:-$(basename "${BASH_SOURCE[1]}")}"
  # El tercer argumento es la ruta relativa del archivo de log.
  local log_file_rel_path="${3:-}"

  if [ -z "$PROJECT_ROOT" ]; then
    echo "ERROR (log): PROJECT_ROOT no está definido. Asegúrese de que load_env() se haya llamado primero." >&2
    return 1
  fi

  # Usar el archivo de log por defecto si no se especifica uno
  if [ -z "$log_file_rel_path" ]; then
    log_file_rel_path="omas/logs/system.log" # Un log genérico si no se especifica
  fi

  local log_file_abs_path="$PROJECT_ROOT/$log_file_rel_path"

  # Asegurarse de que el directorio de logs exista
  mkdir -p "$(dirname "$log_file_abs_path")"

  # Verify that the log file is writable
  if ! touch "$log_file_abs_path" 2>/dev/null; then
      echo "ERROR (log): No se puede escribir en el archivo de log: $log_file_abs_path. Verifique los permisos." >&2
      return 1
  fi

  echo "{\"timestamp\":\"$(date -u --iso-8601=seconds)\",\"agent\":\"$agent_name\",\"message\":\"$message\"}" >> "$log_file_abs_path"
}

# --- System & Command Helpers ---

# Check if a command exists
command_exists() {
    # Redirect debug output to stderr to not pollute stdout
    command -v "$1" >/dev/null 2>&1
}

# Detect operating system
detect_os() {
    case "$(uname -s)" in
        Linux*)     echo "Linux";;
        Darwin*)    echo "Mac";;
        CYGWIN*)    echo "Windows";;
        MINGW*)     echo "Windows";;
        MSYS*)      echo "Windows";;
        *)          echo "Unknown";;
    esac
}

# Configure Podman path based on OS and export PODMAN_CMD
# This function ensures that scripts can find and use podman, especially on Windows.
configure_podman_path() {
    # Do nothing if PODMAN_CMD is already a valid command
    if command_exists "${PODMAN_CMD:-}"; then
        return 0
    fi

    local os
    os=$(detect_os)
    local podman_cmd_found=""

    if [[ "$os" == "Windows" ]]; then
        local podman_paths=(
            "/c/Program Files/RedHat/Podman"
            "/c/Program Files (x86)/RedHat/Podman"
            "$HOME/AppData/Local/Podman"
        )
        
        for path in "${podman_paths[@]}"; do
            if [[ -d "$path" && ":$PATH:" != *":$path:"* ]]; then
                export PATH="$PATH:$path"
            fi
        done
        
        local podman_exes=("podman.exe" "podman")
        for exe in "${podman_exes[@]}"; do
            if command_exists "$exe"; then
                podman_cmd_found="$exe"
                break
            fi
        done
    else # Linux or Mac
        if command_exists "podman"; then
            podman_cmd_found="podman"
        fi
    fi

    if [[ -n "$podman_cmd_found" ]]; then
        export PODMAN_CMD="$podman_cmd_found"
    fi
}