@echo off
setlocal

REM validate_build.bat
REM Script para validar los artefactos generados por el pipeline de construcción.

REM --- Configuración ---
set "BUILD_DIR=..\scripts\build_output"

REM --- Ejecución Principal ---
echo ========================================
echo Iniciando Validación de Artefactos
echo ========================================

if not exist "%BUILD_DIR%" (
    echo Directorio de construcción no encontrado. Ejecuta el build_pipeline.bat primero.
    exit /b 1
)

call :assert_file_exists_and_not_empty "%BUILD_DIR%\fpga\accelerator.bin"
if !errorlevel! neq 0 exit /b !errorlevel!
call :assert_file_exists_and_not_empty "%BUILD_DIR%\firmware\bootloader.bin"
if !errorlevel! neq 0 exit /b !errorlevel!
call :assert_file_exists_and_not_empty "%BUILD_DIR%\wasm\copilot_logic.wasm"
if !errorlevel! neq 0 exit /b !errorlevel!
call :assert_file_exists_and_not_empty "%BUILD_DIR%\genome\genome.bin"
if !errorlevel! neq 0 exit /b !errorlevel!

echo ----------------------------------------
echo Todos los artefactos han sido validados con éxito.
echo ========================================
goto :eof


REM --- Funciones de Validación ---

:assert_file_exists_and_not_empty
set "file_path=%~1"
for %%I in ("%file_path%") do set "file_name=%%~nxI"

echo|set /p="Verificando fichero: %file_name%... "
if not exist "%file_path%" (
    echo ¡FALLÓ! El fichero no existe: %file_path%
    exit /b 1
)
for %%A in ("%file_path%") do (
    if %%~zA==0 (
        echo ¡FALLÓ! El fichero está vacío: %file_path%
        exit /b 1
    )
)
echo OK.
goto :eof