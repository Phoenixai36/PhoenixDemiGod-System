@echo off
setlocal enabledelayedexpansion

REM build_pipeline.bat
REM Script principal para construir todos los artefactos del proyecto Célula Madre Digital.

REM --- Configuración ---
set "FIRMWARE_DIR=..\firmware"
set "GENOME_DIR=..\genome"
set "OUTPUT_DIR=.\build_output"

REM --- Ejecución Principal ---
echo =================================================
echo Iniciando Pipeline de Construcción de Célula Madre
echo =================================================

REM Limpiar directorio de salida
if exist "%OUTPUT_DIR%" (
    rd /s /q "%OUTPUT_DIR%"
)
mkdir "%OUTPUT_DIR%"

call :build_fpga_bitstream
call :build_firmware
call :build_wasm_payload
if !ERRORLEVEL! neq 0 exit /b !ERRORLEVEL!
call :package_genome
call :run_simulation

echo =================================================
echo Pipeline de Construcción Finalizado con Éxito.
echo Artefactos finales en el directorio: %OUTPUT_DIR%
echo =================================================
goto :eof

REM --- Funciones del Pipeline ---

:build_fpga_bitstream
echo --- (1/5) Sintetizando Bitstream de FPGA (Placeholder) ---
if not exist "%OUTPUT_DIR%\fpga" mkdir "%OUTPUT_DIR%\fpga"
echo FPGA_DATA > "%OUTPUT_DIR%\fpga\accelerator.bin"
echo Bitstream de FPGA generado en: %OUTPUT_DIR%\fpga\accelerator.bin
echo.
goto :eof

:build_firmware
echo --- (2/5) Compilando Firmware con Zephyr (Placeholder) ---
if not exist "%OUTPUT_DIR%\firmware" mkdir "%OUTPUT_DIR%\firmware"
copy "%GENOME_DIR%\capa_a_bootloader\bootloader.c" "%OUTPUT_DIR%\firmware\bootloader.bin" > nul
echo Firmware generado en: %OUTPUT_DIR%\firmware\bootloader.bin
echo.
goto :eof

:build_wasm_payload
echo --- (3/5) Compilando Payload WASM con TinyGo ---
where tinygo >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: tinygo no está instalado o no se encuentra en el PATH.
    echo Por favor, instálalo desde: https://tinygo.org/
    exit /b 1
)
if not exist "%OUTPUT_DIR%\wasm" mkdir "%OUTPUT_DIR%\wasm"
tinygo build -o "%OUTPUT_DIR%\wasm\copilot_logic.wasm" -target=wasm "%FIRMWARE_DIR%\copilot\copilot.go"
echo Payload WASM generado en: %OUTPUT_DIR%\wasm\copilot_logic.wasm
echo.
goto :eof

:package_genome
echo --- (4/5) Empaquetando el Genoma Digital (Placeholder) ---
if not exist "%OUTPUT_DIR%\genome" mkdir "%OUTPUT_DIR%\genome"
copy /b "%OUTPUT_DIR%\firmware\bootloader.bin" + "%OUTPUT_DIR%\fpga\accelerator.bin" + "%OUTPUT_DIR%\wasm\copilot_logic.wasm" "%OUTPUT_DIR%\genome\genome.bin" > nul
echo Genoma empaquetado en: %OUTPUT_DIR%\genome\genome.bin
echo.
goto :eof

:run_simulation
echo --- (5/5) Ejecutando Simulación con Renode (Placeholder) ---
echo Simulación completada con éxito.
echo.
goto :eof