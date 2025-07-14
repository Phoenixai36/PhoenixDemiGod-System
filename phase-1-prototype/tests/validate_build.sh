#!/bin/bash

# validate_build.sh
# Script para validar los artefactos generados por el pipeline de construcción.

# --- Configuración ---
set -e
set -u

BUILD_DIR="../scripts/build_output"

# --- Funciones de Validación ---

# Valida que un fichero exista y no esté vacío.
assert_file_exists_and_not_empty() {
    local file_path=$1
    local file_name=$(basename "$file_path")

    echo -n "Verificando fichero: ${file_name}... "
    if [ ! -s "${file_path}" ]; then
        echo "¡FALLÓ! El fichero no existe o está vacío: ${file_path}"
        exit 1
    fi
    echo "OK."
}

# Valida el contenido del módulo WASM.
validate_wasm_module() {
    local wasm_file="${BUILD_DIR}/wasm/copilot_logic.wasm"
    echo -n "Validando cabecera del módulo WASM... "
    
    # Un fichero WASM válido empieza con los bytes mágicos `\0asm`.
    if ! head -c 4 "${wasm_file}" | grep -q $'\0asm'; then
        echo "¡FALLÓ! La cabecera del módulo WASM es incorrecta."
        exit 1
    fi
    echo "OK."
}

# --- Ejecución Principal ---
main() {
    echo "========================================"
    echo "Iniciando Validación de Artefactos"
    echo "========================================"

    if [ ! -d "${BUILD_DIR}" ]; then
        echo "Directorio de construcción no encontrado. Ejecuta el build_pipeline.sh primero."
        exit 1
    fi

    # 1. Validar artefactos individuales
    assert_file_exists_and_not_empty "${BUILD_DIR}/fpga/accelerator.bin"
    assert_file_exists_and_not_empty "${BUILD_DIR}/firmware/bootloader.bin"
    assert_file_exists_and_not_empty "${BUILD_DIR}/wasm/copilot_logic.wasm"
    
    # 2. Validar contenido específico del WASM
    validate_wasm_module

    # 3. Validar el genoma empaquetado final
    assert_file_exists_and_not_empty "${BUILD_DIR}/genome/genome.bin"

    echo "----------------------------------------"
    echo "Todos los artefactos han sido validados con éxito."
    echo "========================================"
}

# Invocar la función principal
main