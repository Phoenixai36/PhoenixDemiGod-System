# auto_venv.ps1
# Busca y activa un entorno virtual en el directorio actual o en los directorios padres.

# Define una función para buscar el directorio del entorno virtual
function Find-VirtualEnv {
    param (
        [string]$startPath = "."
    )

    $currentPath = Get-Location
    $envPath = Resolve-Path $startPath

    while ($envPath) {
        if (Test-Path (Join-Path $envPath "venv")) {
            return Join-Path $envPath "venv"
        }
        elseif (Test-Path (Join-Path $envPath ".venv")) {
            return Join-Path $envPath ".venv"
        }

        # Sube un nivel en el directorio
        $parentPath = Split-Path $envPath
        if ($parentPath -eq $envPath) {
            # Hemos llegado a la raíz
            break
        }
        $envPath = $parentPath
    }

    return $null
}

# Busca el entorno virtual
$virtualEnvPath = Find-VirtualEnv

# Si se encuentra un entorno virtual, actívalo
if ($virtualEnvPath) {
    Write-Host "Entorno virtual encontrado en: $($virtualEnvPath)"
    $activatePath = Join-Path $virtualEnvPath "Scripts\Activate.ps1"
    if (Test-Path $activatePath) {
        & $activatePath
    } else {
        Write-Warning "No se encontró el script de activación en: $($activatePath)"
    }
} else {
    Write-Host "No se encontró ningún entorno virtual en este directorio o en los directorios padres."
}
