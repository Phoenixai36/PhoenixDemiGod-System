import os
import subprocess

# Lista explícita de archivos y directorios a mover, basada en la solicitud original.
ITEMS_TO_MOVE = [
    ".bevel", ".github", ".kiro", ".refactor_backup", ".roo", ".roomodes",
    ".secrets", ".terraform", ".venv", "agents", "autogen", "build", "configs",
    "docs", "examples", "infra", "logs", "models", "monitoring", "node_modules",
    "omas", "phoenix_demigod_tests.egg-info", "pytest.ini", "reports",
    "scripts", "src", "system-health-monitor", "tests", "windmill-scripts",
    ".env", ".env.secrets", ".gitignore", "manager_token", "auto_venv.ps1",
    "completion_percentage_validation_report.md", "completion_roadmap_generator.py",
    "consolidated_steering_document.md", "CTO_CHECKLIST_HIPERBOLICO_PHOENIX_DEMIGOD.md",
    "final_system_review_validation.py", "NEOTEC_2025_Summary_20250724_154336.md",
    "Phoenix Hydra_ Gua Completa.md", "PHOENIX-HYDRA-STATUS-REPORT.md",
    "PHOENIX-HYDRA-TODO-CHECKLIST.md", "phoenix_hydra_comprehensive_review.py"
]

def reorganize_files():
    """
    Mueve los elementos especificados desde la raíz del proyecto al directorio 'misc'.
    """
    destination_dir = "misc"
    if not os.path.isdir(destination_dir):
        print(f"Error: El directorio de destino '{destination_dir}' no existe.")
        return

    for item_name in ITEMS_TO_MOVE:
        source_path = os.path.abspath(item_name)
        
        if os.path.exists(source_path):
            try:
                # Usar el comando 'move' de Windows a través de subprocess.
                command = ["move", source_path, destination_dir]
                print(f"Ejecutando: {' '.join(command)}")
                subprocess.run(command, check=True, shell=True, capture_output=True, text=True, encoding='latin-1')
                print(f"Se movió '{source_path}' a '{destination_dir}' correctamente.")
            except subprocess.CalledProcessError as e:
                print(f"Error al mover '{source_path}': {e.stderr}")
            except Exception as e:
                print(f"Ocurrió un error inesperado al mover '{source_path}': {e}")
        else:
            print(f"Aviso: El elemento '{source_path}' no se encontró. Omitiendo.")

if __name__ == "__main__":
    print("Iniciando la reorganización de archivos...")
    reorganize_files()
    print("Script de reorganización finalizado.")