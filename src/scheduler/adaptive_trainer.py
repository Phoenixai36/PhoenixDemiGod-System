# adaptive_trainer.py
# Ubicación: src/scheduler/adaptive_trainer.py

import os
import time
import json
import logging
import numpy as np
import psutil
import torch
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from queue import PriorityQueue
from dataclasses import dataclass

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AdaptiveTrainer")

@dataclass
class TrainingJob:
    """Definición de trabajo de entrenamiento."""
    model: str
    batch_size: int
    duration: Dict[str, int]  # hours, minutes, seconds
    priority: str  # HIGH, MEDIUM, LOW
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
    
    def get_priority_value(self) -> int:
        """Convierte prioridad textual a valor numérico."""
        priority_map = {"HIGH": 1, "MEDIUM": 2, "LOW": 3}
        return priority_map.get(self.priority, 3)
    
    def get_duration_seconds(self) -> int:
        """Calcula duración total en segundos."""
        hours = self.duration.get("hours", 0)
        minutes = self.duration.get("minutes", 0)
        seconds = self.duration.get("seconds", 0)
        return hours * 3600 + minutes * 60 + seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "model": self.model,
            "batch_size": self.batch_size,
            "duration": self.duration,
            "priority": self.priority,
            "created_at": self.created_at
        }


class ResourceMonitor:
    """Monitor de recursos del sistema."""
    
    def __init__(self, update_interval: int = 5):
        self.update_interval = update_interval
        self.last_update = 0
        self.resources = self._get_resources()
        
    def _get_resources(self) -> Dict[str, float]:
        """Obtiene recursos actuales del sistema."""
        cpu_idle = 100 - psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        mem_available = mem.available / mem.total * 100
        
        # Verificar GPU si está disponible
        gpu_idle = 100.0
        if torch.cuda.is_available():
            try:
                # Esto requiere que nvidia-smi esté instalado
                import subprocess
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'],
                    stdout=subprocess.PIPE,
                    text=True
                )
                gpu_usage = float(result.stdout.strip())
                gpu_idle = 100.0 - gpu_usage
            except Exception as e:
                logger.warning(f"Could not get GPU usage: {e}")
        
        disk = psutil.disk_usage('/')
        disk_free = disk.free / disk.total * 100
        
        return {
            "cpu_idle": cpu_idle,
            "mem_available": mem_available,
            "gpu_idle": gpu_idle,
            "disk_free": disk_free,
            "timestamp": time.time()
        }
    
    def get_current_resources(self) -> Dict[str, float]:
        """Obtiene recursos actuales, actualizando si es necesario."""
        current_time = time.time()
        if current_time - self.last_update > self.update_interval:
            self.resources = self._get_resources()
            self.last_update = current_time
            
        return self.resources


class ModelRegistry:
    """Registro de modelos disponibles para entrenamiento."""
    
    def __init__(self, models_dir: str = None):
        self.models_dir = models_dir or os.path.join(os.path.dirname(__file__), "../../models")
        self.models = {}
        self._load_models()
        
    def _load_models(self):
        """Carga información de modelos disponibles."""
        if not os.path.exists(self.models_dir):
            os.makedirs(self.models_dir, exist_ok=True)
            
        # Modelos predefinidos para demostración
        self.models = {
            "phoenix_core": {
                "path": os.path.join(self.models_dir, "phoenix_core"),
                "type": "transformer",
                "parameters": 1.3e9,  # 1.3B parámetros
                "last_trained": datetime.now().timestamp() - 86400,  # Ayer
                "versions": ["v1.0", "v1.1", "v1.2"]
            },
            "xamba_quant": {
                "path": os.path.join(self.models_dir, "xamba_quant"),
                "type": "quantized",
                "parameters": 7e9,  # 7B parámetros
                "last_trained": datetime.now().timestamp() - 172800,  # Hace 2 días
                "versions": ["v0.9", "v1.0"]
            },
            "mia_agent": {
                "path": os.path.join(self.models_dir, "mia_agent"),
                "type": "agent",
                "parameters": 0.3e9,  # 300M parámetros
                "last_trained": datetime.now().timestamp() - 43200,  # Hace 12 horas
                "versions": ["v0.5", "v0.6"]
            }
        }
        
        # Crear directorios para modelos si no existen
        for model_name, model_info in self.models.items():
            os.makedirs(model_info["path"], exist_ok=True)
    
    def get_model(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Obtiene información de un modelo específico."""
        return self.models.get(model_name)
    
    def get_all_models(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene información de todos los modelos."""
        return self.models
    
    def update_model_timestamp(self, model_name: str):
        """Actualiza timestamp de último entrenamiento."""
        if model_name in self.models:
            self.models[model_name]["last_trained"] = datetime.now().timestamp()


class AdaptiveTrainer:
    """Entrenador adaptativo que optimiza recursos del sistema."""
    
    def __init__(self):
        """Inicializa el entrenador adaptativo."""
        self.resource_monitor = ResourceMonitor()
        self.training_queue = PriorityQueue()
        self.model_registry = ModelRegistry()
        
        # Estado del sistema
        self.is_night = False
        self.is_performance = False
        self.performance_schedule = []
        
        # Directorios para datos
        self.data_dir = os.path.join(os.path.dirname(__file__), "../../data")
        self.training_dir = os.path.join(self.data_dir, "training")
        os.makedirs(self.training_dir, exist_ok=True)
        
        logger.info("AdaptiveTrainer initialized")
        
    def update_system_state(self):
        """Actualiza estado del sistema (hora, performances programadas)."""
        current_hour = datetime.now().hour
        
        # Noche definida como 22:00 - 06:00
        self.is_night = 22 <= current_hour or current_hour < 6
        
        # Verificar si hay performance programada en próximas 2 horas
        self.is_performance = self._check_upcoming_performance(hours=2)
        
        logger.debug(f"System state updated: is_night={self.is_night}, is_performance={self.is_performance}")
    
    def _check_upcoming_performance(self, hours: int = 2) -> bool:
        """Verifica si hay performance programada en próximas horas."""
        # Implementación simulada
        # En producción, verificar calendario real
        return False
    
    def schedule_training(self):
        """Programa tareas de entrenamiento basándose en recursos disponibles."""
        # Actualizar estado del sistema
        self.update_system_state()
        
        # Obtener recursos actuales
        resources = self.resource_monitor.get_current_resources()
        logger.info(f"Current resources: CPU idle={resources['cpu_idle']:.1f}%, GPU idle={resources['gpu_idle']:.1f}%")
        
        # Entrenamiento nocturno completo
        if self.is_night and not self.is_performance:
            logger.info("Night time training (full resources)")
            self.enqueue("phoenix_core", batch_size=32, hours=6, priority="HIGH")
        
        # Entrenamiento medio cuando hay recursos disponibles
        elif resources["cpu_idle"] > 70 and resources["gpu_idle"] > 60:
            logger.info("Medium resources training")
            self.enqueue("xamba_quant", batch_size=16, minutes=30, priority="MEDIUM")
        
        # Micro-entrenamiento con recursos mínimos
        elif resources["cpu_idle"] > 30:
            logger.info("Micro-training with minimal resources")
            self.enqueue("mia_agent", batch_size=4, minutes=5, priority="LOW")
        
        else:
            logger.info("Insufficient resources for training")
    
    def enqueue(self, model: str, batch_size: int, priority: str = "MEDIUM", 
               hours: int = 0, minutes: int = 0, seconds: int = 0):
        """Añade trabajo de entrenamiento a la cola."""
        # Verificar que el modelo existe
        if not self.model_registry.get_model(model):
            logger.error(f"Model {model} not found in registry")
            return False
        
        # Crear trabajo de entrenamiento
        job = TrainingJob(
            model=model,
            batch_size=batch_size,
            duration={"hours": hours, "minutes": minutes, "seconds": seconds},
            priority=priority
        )
        
        # Añadir a la cola con prioridad
        self.training_queue.put((job.get_priority_value(), job))
        
        logger.info(f"Enqueued training job: {model} (priority: {priority})")
        return True
    
    def process_next_job(self) -> bool:
        """Procesa el siguiente trabajo en la cola."""
        if self.training_queue.empty():
            logger.info("No training jobs in queue")
            return False
        
        # Obtener siguiente trabajo
        _, job = self.training_queue.get()
        
        logger.info(f"Processing training job: {job.model} (batch size: {job.batch_size})")
        
        # Simular entrenamiento
        model_info = self.model_registry.get_model(job.model)
        if not model_info:
            logger.error(f"Model {job.model} not found in registry")
            return False
        
        # En producción, aquí se iniciaría el entrenamiento real
        # Para demostración, solo simulamos
        duration_seconds = job.get_duration_seconds()
        logger.info(f"Training {job.model} for {duration_seconds} seconds with batch size {job.batch_size}")
        
        # Simular entrenamiento (no bloquear en producción)
        # time.sleep(min(duration_seconds, 5))  # Máximo 5 segundos para demo
        
        # Actualizar timestamp de último entrenamiento
        self.model_registry.update_model_timestamp(job.model)
        
        # Guardar registro de entrenamiento
        self._save_training_record(job)
        
        logger.info(f"Completed training job: {job.model}")
        return True
    
    def process_performance_data(self, performance_data: Dict[str, Any]):
        """Procesa y almacena datos de performance para entrenamiento futuro."""
        # Extraer características para entrenamiento
        processed_data = self._preprocess_performance_data(performance_data)
        
        # Guardar en dataset apropiado según fase
        phase = processed_data.get("phase", "unknown")
        self._add_to_training_dataset(phase, processed_data)
        
        # Si hay suficientes datos nuevos, programar entrenamiento incremental
        if self._dataset_ready_for_training(phase):
            self._schedule_incremental_training(phase)
    
    def _preprocess_performance_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocesa datos de performance para entrenamiento."""
        # Implementación simplificada
        processed = data.copy()
        
        # Normalización de características numéricas
        for feature in ["bpm", "spectral_centroid", "spectral_bandwidth", "rms"]:
            if feature in processed:
                # Normalización simple para demo
                processed[feature] = processed[feature] / 100.0
        
        # Codificación one-hot de fases
        phase_categories = ["intro", "build-up", "drop", "breakdown", "outro"]
        if "phase" in processed and processed["phase"] in phase_categories:
            phase_idx = phase_categories.index(processed["phase"])
            phase_encoded = [0] * len(phase_categories)
            phase_encoded[phase_idx] = 1
            processed["phase_encoded"] = phase_encoded
        
        # Extracción de características temporales
        if "timestamp" in processed:
            dt = datetime.fromtimestamp(processed["timestamp"])
            processed["hour"] = dt.hour / 24.0  # Normalizado entre 0-1
            processed["day_of_week"] = dt.weekday() / 6.0  # Normalizado entre 0-1
        
        return processed
    
    def _add_to_training_dataset(self, phase: str, data: Dict[str, Any]):
        """Añade datos procesados al dataset de entrenamiento."""
        # Crear directorio para fase si no existe
        phase_dir = os.path.join(self.training_dir, phase)
        os.makedirs(phase_dir, exist_ok=True)
        
        # Guardar datos
        timestamp = int(time.time())
        filename = os.path.join(phase_dir, f"data_{timestamp}.json")
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.debug(f"Added data to {phase} dataset: {filename}")
    
    def _dataset_ready_for_training(self, phase: str) -> bool:
        """Verifica si hay suficientes datos nuevos para entrenamiento."""
        # Implementación simplificada
        # En producción, verificar cantidad y calidad de datos
        phase_dir = os.path.join(self.training_dir, phase)
        if not os.path.exists(phase_dir):
            return False
        
        # Contar archivos en directorio
        files = os.listdir(phase_dir)
        return len(files) >= 10  # Mínimo 10 muestras para entrenar
    
    def _schedule_incremental_training(self, phase: str):
        """Programa entrenamiento incremental para una fase específica."""
        logger.info(f"Scheduling incremental training for phase: {phase}")
        
        # Determinar modelo apropiado según fase
        model_map = {
            "intro": "mia_agent",
            "build-up": "mia_agent",
            "drop": "phoenix_core",
            "breakdown": "xamba_quant",
            "outro": "mia_agent",
            "unknown": "mia_agent"
        }
        
        model = model_map.get(phase, "mia_agent")
        
        # Programar entrenamiento con prioridad media
        self.enqueue(model, batch_size=8, minutes=15, priority="MEDIUM")
    
    def _save_training_record(self, job: TrainingJob):
        """Guarda registro de entrenamiento completado."""
        record = {
            "timestamp": time.time(),
            "job": job.to_dict(),
            "resources": self.resource_monitor.get_current_resources()
        }
        
        # Crear directorio para registros si no existe
        logs_dir = os.path.join(self.data_dir, "training_logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # Guardar registro
        date_str = datetime.now().strftime("%Y%m%d")
        filename = os.path.join(logs_dir, f"training_log_{date_str}.json")
        
        # Añadir a archivo existente o crear nuevo
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(record)
        
        with open(filename, 'w') as f:
            json.dump(logs, f, indent=2)


def test_adaptive_trainer():
    """Función de prueba para AdaptiveTrainer."""
    trainer = AdaptiveTrainer()
    
    # Programar entrenamiento
    print("Scheduling training based on current resources...")
    trainer.schedule_training()
    
    # Procesar trabajos en cola
    print("\nProcessing training jobs in queue...")
    while not trainer.training_queue.empty():
        trainer.process_next_job()
    
    # Simular datos de performance
    print("\nProcessing performance data...")
    performance_data = {
        "bpm": 140.5,
        "phase": "drop",
        "midi_activity": {"note_density": 0.75},
        "audio_features": {
            "rms": 0.85,
            "spectral_centroid": 2500.0,
            "spectral_bandwidth": 1800.0
        },
        "chaos_active": False,
        "timestamp": time.time()
    }
    
    trainer.process_performance_data(performance_data)
    
    print("\nTest completed successfully!")


if __name__ == "__main__":
    test_adaptive_trainer()
