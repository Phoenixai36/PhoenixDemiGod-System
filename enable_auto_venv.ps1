# enable_auto_venv.ps1
# Agrega la ejecución del script auto_venv.ps1 al perfil de PowerShell.

# Define la ruta al script auto_venv.ps1 (relativa al script enable_auto_venv.ps1)
$autoVenvScriptPath = Join-Path -Path $PSScriptRoot -ChildPath "auto_venv.ps1"

# Verifica si el script auto_venv.ps1 existe
if (-not (Test-Path -Path $autoVenvScriptPath)) {
    Write-Error "El script auto_venv.ps1 no se encuentra en: $($autoVenvScriptPath)"
    exit 1
}

# Agrega la ejecución del script al perfil de PowerShell
try {
    # Lee el contenido actual del perfil
    $profileContent = Get-Content -Path $PROFILE

    # Verifica si la línea ya existe en el perfil
    if ($profileContent -notcontains ". '$autoVenvScriptPath'") {
        # Agrega la línea al perfil
        Add-Content -Path $PROFILE -Value ". '$autoVenvScriptPath'"
        Write-Host "Se ha agregado la ejecución del script auto_venv.ps1 al perfil de PowerShell."
    } else {
        Write-Host "La ejecución del script auto_venv.ps1 ya está configurada en el perfil de PowerShell."
    }
}
catch {
    Write-Error "Error al modificar el perfil de PowerShell: $($_.Exception.Message)"
    exit 1
}
