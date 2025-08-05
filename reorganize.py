import os
import shutil


def reorganize():
    # Define la estructura de directorios deseada
    structure = {
        "docs/event_routing": [
            "event_routing_architecture.md",
            "event_routing_configuration.md"
        ],
        "docs/local_processing": ["local_processing_mamba_architecture.md"],
        "docs/podman": ["podman_deployment_guide.md"],
        "docs": ["testing_guide.md", "agent_hooks_migration_plan.md"],
    }

    # Crea los directorios necesarios
    if not os.path.exists("misc"):
        os.makedirs("misc")

    # Mueve los archivos a los directorios correctos
    for dir, files in structure.items():
        for file in files:
            source = (
                os.path.join("docs", file)
                if os.path.exists(os.path.join("docs", file))
                else None
            )
            if source:
                destination = os.path.join(dir, file)
                try:
                    shutil.move(source, destination)
                    print(f"Moved {source} to {destination}")
                except FileNotFoundError:
                    print(f"File not found: {source}")
                except Exception as e:
                    print(f"Error moving {source} to {destination}: {e}")
            else:
                print(f"Source file not found for {file}")

    # Mueve todos los archivos restantes en la raíz al directorio misc
    structure_files = [
        item for sublist in structure.values() for item in sublist
    ]
    for file in os.listdir("."):
        if (
            file not in structure_files
            and file != "misc"
            and not os.path.isdir(file)
            and file != ".git"
        ):
            destination = os.path.join("misc", file)
            try:
                shutil.move(file, destination)
                print(f"Moved {file} to {destination}")
            except Exception as e:
                print(f"Error moving {file} to misc: {e}")

    # Elimina el directorio .kiro/pytest_cache
    if os.path.exists(".kiro/pytest_cache"):
        try:
            shutil.rmtree(".kiro/pytest_cache")
            print("Deleted .kiro/pytest_cache")
        except Exception as e:
            print(f"Error deleting .kiro/pytest_cache: {e}")
    else:
        print("Directory not found: .kiro/pytest_cache")

    # Limpia los archivos innecesarios
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith((".tmp", ".bak", ".log")):
                filepath = os.path.join(root, file)
                try:
                    os.remove(filepath)
                    print(f"Deleted {filepath}")
                except Exception as e:
                    print(f"Error deleting {filepath}: {e}")


if __name__ == "__main__":
    reorganize()