from fastapi import FastAPI, HTTPException
from context_windows.zone_context_manager import ContextManager
import subprocess
import os

app = FastAPI(title="Phoenix Quimera Model Router")

MODELS = {
    "phi3:mini": {"image": "ollama/ollama:latest", "port": 11434},
    "gemma2:2b": {"image": "ollama/ollama:latest", "port": 11435},
    # Agrega más modelos según tu inventario real
}

context_manager = ContextManager()

def is_model_running(model_name):
    result = subprocess.run(
        ["podman", "ps", "--filter", f"name={model_name}", "--format", "{{.ID}}"],
        capture_output=True, text=True
    )
    return bool(result.stdout.strip())

def start_model_container(model_name):
    model = MODELS[model_name]
    if not is_model_running(model_name):
        subprocess.run([
            "podman", "run", "-d", "--name", model_name,
            "-p", f"{model['port']}:11434",
            model["image"]
        ])
    return f"http://localhost:{model['port']}"

def pull_model_if_needed(model_name):
    # Hook Kiro: descarga el modelo si no existe localmente
    model = MODELS[model_name]
    subprocess.run(["ollama", "pull", model_name])

@app.post("/request_model")
def request_model(request: dict):
    model_name = request.get("preferred_model")
    zone = request.get("zone", "default")
    task_context = request.get("context", {})

    if model_name not in MODELS:
        raise HTTPException(status_code=404, detail="Modelo no soportado.")

    # Guardar contexto lightweight para la zona
    context_manager.update_context(zone, task_context)

    # Ingeniería de contexto: adaptar prompt/config según contexto de zona
    full_context = context_manager.get_context(zone)
    # Aquí puedes modificar el prompt, recursos, etc. según el contexto

    pull_model_if_needed(model_name)
    endpoint = start_model_container(model_name)
    return {
        "endpoint": endpoint,
        "status": "ready",
        "zone_context": full_context
    }

@app.get("/status")
def status():
    status_dict = {}
    for name in MODELS:
        status_dict[name] = "running" if is_model_running(name) else "stopped"
    return status_dict

@app.post("/stop_model")
def stop_model(request: dict):
    model_name = request.get("model")
    if is_model_running(model_name):
        subprocess.run(["podman", "stop", model_name])
        subprocess.run(["podman", "rm", model_name])
    return {"model": model_name, "status": "stopped"}

@app.get("/context/{zone}")
def get_zone_context(zone: str):
    return context_manager.get_context(zone).
