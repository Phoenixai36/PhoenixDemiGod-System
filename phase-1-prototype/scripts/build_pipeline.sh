#!/bin/bash

# build_pipeline.sh
# Script principal para construir todos los artefactos del proyecto Célula Madre Digital.

# --- Configuración ---
set -e # Salir inmediatamente si un comando falla.
set -o pipefail # El código de salida de un pipeline es el del último comando que falló.
set -u # Tratar las variables no definidas como un error.

# Directorios del proyecto
FIRMWARE_DIR="../firmware"
GENOME_DIR="../genome"
OUTPUT_DIR="./build_output"

# --- Funciones del Pipeline ---

# 1. Síntesis de FPGA (Placeholder)
# En un caso real, esto invocaría a Yosys y nextpnr.
build_fpga_bitstream() {
    echo "--- (1/5) Sintetizando Bitstream de FPGA (Placeholder) ---"
    # Comandos de ejemplo:
    # yosys -p "synth_nexus -top cell_core" cell_design.v
    # nextpnr-nexus --json cell_core.json --lpf constraints.lpf
    # Por ahora, creamos un fichero binario de ejemplo.
    mkdir -p "${OUTPUT_DIR}/fpga"
    echo "FPGA_DATA" > "${OUTPUT_DIR}/fpga/accelerator.bin"
    echo "Bitstream de FPGA generado en: ${OUTPUT_DIR}/fpga/accelerator.bin"
    echo ""
}

# 2. Compilación del Firmware con Zephyr (Placeholder)
# Esto compilaría el bootloader y el firmware principal.
build_firmware() {
    echo "--- (2/5) Compilando Firmware con Zephyr (Placeholder) ---"
    # Comandos de ejemplo:
    # cd zephyr-workspace
    # west build -b lattice_nexus_dev app/phoenix_cell
    # Por ahora, creamos un bootloader binario de ejemplo.
    mkdir -p "${OUTPUT_DIR}/firmware"
    cp "${GENOME_DIR}/capa_a_bootloader/bootloader.c" "${OUTPUT_DIR}/firmware/bootloader.bin"
    echo "Firmware generado en: ${OUTPUT_DIR}/firmware/bootloader.bin"
    echo ""
}

# 3. Compilación del Payload WASM con TinyGo
# Compila la lógica del copiloto a WebAssembly.
build_wasm_payload() {
    echo "--- (3/5) Compilando Payload WASM con TinyGo ---"
    if ! command -v tinygo &> /dev/null
    then
        echo "Error: tinygo no está instalado o no se encuentra en el PATH."
        echo "Por favor, instálalo desde: https://tinygo.org/"
        exit 1
    fi
    
    mkdir -p "${OUTPUT_DIR}/wasm"
    tinygo build -o "${OUTPUT_DIR}/wasm/copilot_logic.wasm" -target=wasm "${FIRMWARE_DIR}/copilot/copilot.go"
    
    echo "Payload WASM generado en: ${OUTPUT_DIR}/wasm/copilot_logic.wasm"
    echo ""
}

# 4. Empaquetado del Genoma Digital (Placeholder)
# Combina todos los artefactos en un único fichero de genoma.
package_genome() {
    echo "--- (4/5) Empaquetando el Genoma Digital (Placeholder) ---"
    # Este script combinaría el bootloader, descriptor, y payload.
    # python3 genome_packager.py --...
    mkdir -p "${OUTPUT_DIR}/genome"
    
    # Concatenamos los artefactos para simular el paquete del genoma
    cat "${OUTPUT_DIR}/firmware/bootloader.bin" \
        "${OUTPUT_DIR}/fpga/accelerator.bin" \
        "${OUTPUT_DIR}/wasm/copilot_logic.wasm" > "${OUTPUT_DIR}/genome/genome.bin"

    echo "Genoma empaquetado en: ${OUTPUT_DIR}/genome/genome.bin"
    echo ""
}

# 5. Simulación con Renode (Placeholder)
# Ejecutaría el genoma completo en un SoC simulado.
run_simulation() {
    echo "--- (5/5) Ejecutando Simulación con Renode (Placeholder) ---"
    # renode-test --robot test_apoptosis.robot
    # renode cell_simulation.resc
    echo "Simulación completada con éxito."
    echo ""
}


# --- Ejecución Principal ---
main() {
    echo "================================================="
    echo "Iniciando Pipeline de Construcción de Célula Madre"
    echo "================================================="
    
    # Limpiar directorio de salida
    rm -rf "${OUTPUT_DIR}"
    mkdir -p "${OUTPUT_DIR}"

    build_fpga_bitstream
    build_firmware
    build_wasm_payload
    package_genome
    run_simulation

    echo "================================================="
    echo "Pipeline de Construcción Finalizado con Éxito."
    echo "Artefactos finales en el directorio: ${OUTPUT_DIR}"
    echo "================================================="
}

# Invocar la función principal
main