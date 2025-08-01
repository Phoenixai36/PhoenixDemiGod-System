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
        "docs": ["testing_guide.md", "agent_hooks_migration_plan.md"]
    }

    # Crea los directorios necesarios
    for dir in structure.keys():
        if not os.path.exists(dir):
            os.makedirs(dir)

    # Mueve los archivos a los directorios correctos
    for dir, files in structure.items():
        for file in files:
            source = (
                file
                if os.path.exists(file)
                else os.path.join("docs", file)
            )
            destination = os.path.join(dir, file)
            try:
                shutil.move(source, destination)
                print(f"Moved {source} to {destination}")
            except FileNotFoundError:
                print(f"File not found: {source}")
            except Exception as e:
                print(f"Error moving {source} to {destination}: {e}")

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