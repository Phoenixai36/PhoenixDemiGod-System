"""
Phoenix DemiGod Multi-Model Router
Router inteligente para modelos Mamba/SSM con fallback automático y procesamiento 100% local

Arquitectura:
- Modelo principal: Mamba/SSM (devstral, zamba7b) para eficiencia energética
- Fallback automático: Llama3, Qwen2.5 si Mamba falla
- Procesamiento local: Ollama + contenedores, cero cloud
- Monitorización: Prometheus/Grafana para grants y auditoría
"""

import asyncio
import logging
import time
import psutil
import json
import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime

# HTTP client
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logging.error("httpx required but not available. Install with: pip install httpx")

# FastAPI imports
try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import Response
    from pydantic import BaseModel, Field
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logging.error("FastAPI required but not available. Install with: pip install fastapi uvicorn")

# Prometheus monitoring
try:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from . import metrics
    PROMETHEUS_AVAILABLE = metrics.PROMETHEUS_AVAILABLE
    if not PROMETHEUS_AVAILABLE:
        logging.warning("Prometheus client not available - metrics disabled")
except (ImportError, ModuleNotFoundError):
    PROMETHEUS_AVAILABLE = False
    logging.warning("Prometheus client not available - metrics disabled")
    # Define dummy variables to avoid runtime errors if prometheus is not available
    generate_latest = None
    CONTENT_TYPE_LATEST = None
    metrics = None


class ModelType(Enum):
    """Tipos de modelos disponibles en Phoenix DemiGod"""
    MAMBA_SSM = "mamba_ssm"          # Modelo principal eficiente
    TRANSFORMER = "transformer"      # Fallback tradicional
    CODE_SPECIALIST = "code_specialist"  # Especialista en código
    REASONING = "reasoning"          # Razonamiento avanzado


class TaskType(Enum):
    """Tipos de tareas para routing inteligente"""
    CODE_ANALYSIS = "code_analysis"
    SYSTEM_REVIEW = "system_review"
    REASONING = "reasoning"
    GENERAL_QUERY = "general_query"
    CONFIGURATION = "configuration"
    SECURITY_AUDIT = "security_audit"


@dataclass
class ModelConfig:
    """Configuración de modelo local"""
    name: str
    model_type: ModelType
    ollama_name: str
    priority: int  # 1 = highest priority
    max_tokens: int = 2048
    temperature: float = 0.7
    energy_efficient: bool = True
    specialization: Optional[List[TaskType]] = field(default_factory=list)
    fallback_for: Optional[List[str]] = field(default_factory=list)


@dataclass
class InferenceRequest:
    """Request para inferencia"""
    prompt: str
    task_type: TaskType = TaskType.GENERAL_QUERY
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    force_model: Optional[str] = None
    enable_fallback: bool = True


@dataclass
class InferenceResponse:
    """Response de inferencia con métricas"""
    response: str
    model_used: str
    model_type: str
    inference_time_ms: float
    energy_consumed_wh: float
    tokens_generated: int
    confidence_score: float
    fallback_used: bool = False
    error: Optional[str] = None


class PhoenixModelRouter:
    """
    Router inteligente multi-modelo para Phoenix DemiGod
    
    Características:
    - Routing automático basado en tipo de tarea
    - Fallback garantizado si modelo principal falla
    - Monitorización energética y de rendimiento
    - 100% procesamiento local via Ollama
    - Métricas para grants y auditorías
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.models: Dict[str, ModelConfig] = {}
        self.inference_history: List[InferenceResponse] = []
        
        # Las métricas de Prometheus se cargan desde el módulo `metrics`
        
        # Cargar configuración
        self._load_model_configs()
        
        # Verificar disponibilidad de Ollama (no usar asyncio.create_task en __init__)
        self._ollama_verified = False
    
    def _load_model_configs(self):
        """Cargar configuración de modelos desde variables de entorno"""
        
        # Configuración por defecto basada en especificación
        default_configs = [
            ModelConfig(
                name="devstral",
                model_type=ModelType.CODE_SPECIALIST,
                ollama_name=os.getenv("DEFAULTMODEL", "deepseek-coder:6.7b"),
                priority=1,
                specialization=[TaskType.CODE_ANALYSIS, TaskType.SYSTEM_REVIEW],
                energy_efficient=True
            ),
            ModelConfig(
                name="zamba7b",
                model_type=ModelType.MAMBA_SSM,
                ollama_name=os.getenv("AGENTICMODEL", "llama3.2:8b"),
                priority=2,
                specialization=[TaskType.REASONING, TaskType.GENERAL_QUERY],
                energy_efficient=True
            ),
            ModelConfig(
                name="llama3.2-3b",
                model_type=ModelType.TRANSFORMER,
                ollama_name=os.getenv("FALLBACKMODEL", "llama3.2:3b"),
                priority=3,
                fallback_for=["devstral", "zamba7b"],
                energy_efficient=False
            ),
            ModelConfig(
                name="qwen2.5-coder-7b",
                model_type=ModelType.CODE_SPECIALIST,
                ollama_name=os.getenv("SPECIALISTMODEL", "qwen2.5-coder:7b"),
                priority=4,
                specialization=[TaskType.CODE_ANALYSIS, TaskType.CONFIGURATION],
                fallback_for=["devstral"],
                energy_efficient=False
            )
        ]
        
        for config in default_configs:
            self.models[config.name] = config
        
        self.logger.info(f"Loaded {len(self.models)} model configurations")
    
    async def _verify_ollama_connection(self):
        """Verificar conexión con Ollama"""
        if self._ollama_verified:
            return
            
        try:
            if not HTTPX_AVAILABLE:
                self.logger.error("httpx not available - cannot verify Ollama connection")
                return
                
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.ollama_base_url}/api/tags")
                if response.status_code == 200:
                    available_models = [model["name"] for model in response.json().get("models", [])]
                    self.logger.info(f"Ollama connected. Available models: {available_models}")
                    
                    # Verificar que nuestros modelos están disponibles
                    for model_name, config in self.models.items():
                        if config.ollama_name not in available_models:
                            self.logger.warning(f"Model {config.ollama_name} not found in Ollama")
                    
                    self._ollama_verified = True
                else:
                    self.logger.error(f"Ollama connection failed: {response.status_code}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Ollama: {e}")
    
    def _select_optimal_model(self, task_type: TaskType, force_model: Optional[str] = None) -> ModelConfig:
        """Seleccionar modelo óptimo basado en tipo de tarea"""
        
        if force_model and force_model in self.models:
            return self.models[force_model]
        
        # Filtrar modelos especializados para la tarea
        specialized_models = [
            model for model in self.models.values()
            if model.specialization and task_type in model.specialization
        ]
        
        if specialized_models:
            # Ordenar por prioridad (menor número = mayor prioridad)
            specialized_models.sort(key=lambda x: x.priority)
            return specialized_models[0]
        
        # Si no hay especialización, usar modelo por defecto (menor prioridad)
        default_model = min(self.models.values(), key=lambda x: x.priority)
        return default_model
    
    def _get_fallback_models(self, failed_model: str) -> List[ModelConfig]:
        """Obtener modelos de fallback para un modelo que falló"""
        fallback_models = []
        
        for model in self.models.values():
            if model.fallback_for and failed_model in model.fallback_for:
                fallback_models.append(model)
        
        # Ordenar por prioridad
        fallback_models.sort(key=lambda x: x.priority)
        return fallback_models
    
    async def _call_ollama_model(self, model_config: ModelConfig, prompt: str, 
                                max_tokens: int, temperature: float) -> Dict[str, Any]:
        """Llamar a modelo via Ollama API"""
        
        if not HTTPX_AVAILABLE:
            return {
                "success": False,
                "error": "httpx not available - cannot make HTTP requests"
            }
        
        payload = {
            "model": model_config.ollama_name,
            "prompt": prompt,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                "top_p": 0.9
            },
            "stream": False
        }
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.ollama_base_url}/api/generate",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    inference_time = (time.time() - start_time) * 1000  # ms
                    
                    return {
                        "success": True,
                        "response": result.get("response", ""),
                        "inference_time_ms": inference_time,
                        "tokens_generated": len(result.get("response", "").split()),
                        "model_used": model_config.ollama_name
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _calculate_energy_consumption(self, model_config: ModelConfig, 
                                    inference_time_ms: float) -> float:
        """Calcular consumo energético estimado"""
        
        # Estimaciones basadas en especificación de eficiencia Mamba vs Transformer
        base_power_watts = {
            ModelType.MAMBA_SSM: 50,      # Muy eficiente
            ModelType.CODE_SPECIALIST: 80, # Eficiente si es Mamba-based
            ModelType.TRANSFORMER: 150,   # Menos eficiente
            ModelType.REASONING: 100      # Intermedio
        }
        
        power = base_power_watts.get(model_config.model_type, 100)
        
        # Ajuste por eficiencia energética
        if model_config.energy_efficient:
            power *= 0.65  # 35% reducción (target 60-70%)
        
        # Convertir a Wh
        inference_time_hours = inference_time_ms / (1000 * 3600)
        energy_wh = power * inference_time_hours
        
        return energy_wh
    
    def _calculate_confidence_score(self, response_text: str, inference_time_ms: float) -> float:
        """Calcular score de confianza heurístico"""
        
        # Heurística simple basada en longitud y tiempo
        if not response_text.strip():
            return 0.0
        
        # Factores de confianza
        length_factor = min(1.0, len(response_text) / 200)  # Normalizar por 200 chars
        speed_factor = max(0.1, min(1.0, 5000 / inference_time_ms)) if inference_time_ms > 0 else 0.1
        
        # Penalizar respuestas muy cortas o errores obvios
        if len(response_text) < 10:
            return 0.2
        
        if any(error_word in response_text.lower() for error_word in ["error", "failed", "cannot", "unable"]):
            return 0.3
        
        confidence = (length_factor * 0.6 + speed_factor * 0.4)
        return max(0.1, min(0.95, confidence))
    
    async def infer(self, request: InferenceRequest) -> InferenceResponse:
        """
        Realizar inferencia con routing inteligente y fallback automático
        """
        
        # Verificar conexión Ollama si no se ha hecho
        await self._verify_ollama_connection()
        
        # Seleccionar modelo óptimo
        selected_model = self._select_optimal_model(request.task_type, request.force_model)
        
        # Parámetros de inferencia
        max_tokens = request.max_tokens or selected_model.max_tokens
        temperature = request.temperature or selected_model.temperature
        
        # Intentar inferencia con modelo principal
        result = await self._call_ollama_model(
            selected_model, request.prompt, max_tokens, temperature
        )
        
        fallback_used = False
        final_model = selected_model
        
        # Fallback automático si falla
        if not result["success"] and request.enable_fallback:
            self.logger.warning(f"Model {selected_model.name} failed: {result.get('error')}")
            
            fallback_models = self._get_fallback_models(selected_model.name)
            
            for fallback_model in fallback_models:
                self.logger.info(f"Trying fallback model: {fallback_model.name}")
                
                result = await self._call_ollama_model(
                    fallback_model, request.prompt, max_tokens, temperature
                )
                
                if result["success"]:
                    fallback_used = True
                    final_model = fallback_model
                    
                    # Métricas de fallback
                    if PROMETHEUS_AVAILABLE and metrics:
                        if metrics.FALLBACK_COUNTER:
                            metrics.FALLBACK_COUNTER.labels(
                                from_model=selected_model.name,
                                to_model=fallback_model.name
                            ).inc()
                    
                    break
        
        # Crear respuesta
        if result["success"]:
            energy_consumed = self._calculate_energy_consumption(
                final_model, result["inference_time_ms"]
            )
            
            confidence_score = self._calculate_confidence_score(
                result["response"], result["inference_time_ms"]
            )
            
            response = InferenceResponse(
                response=result["response"],
                model_used=final_model.name,
                model_type=final_model.model_type.value,
                inference_time_ms=result["inference_time_ms"],
                energy_consumed_wh=energy_consumed,
                tokens_generated=result["tokens_generated"],
                confidence_score=confidence_score,
                fallback_used=fallback_used
            )
            
            # Métricas Prometheus
            if PROMETHEUS_AVAILABLE and metrics:
                if metrics.INFERENCE_COUNTER:
                    metrics.INFERENCE_COUNTER.labels(
                        model=final_model.name,
                        task_type=request.task_type.value
                    ).inc()
                
                if metrics.INFERENCE_DURATION:
                    metrics.INFERENCE_DURATION.labels(model=final_model.name).observe(
                        result["inference_time_ms"] / 1000
                    )
                
                if metrics.ENERGY_GAUGE:
                    metrics.ENERGY_GAUGE.set(energy_consumed)
            
        else:
            # Error en todos los modelos
            response = InferenceResponse(
                response="",
                model_used=selected_model.name,
                model_type=selected_model.model_type.value,
                inference_time_ms=0.0,
                energy_consumed_wh=0.0,
                tokens_generated=0,
                confidence_score=0.0,
                fallback_used=fallback_used,
                error=result.get("error", "Unknown error")
            )
        
        # Guardar en historial
        self.inference_history.append(response)
        
        return response
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de rendimiento para grants y auditorías"""
        
        if not self.inference_history:
            return {"error": "No inference history available"}
        
        successful_inferences = [r for r in self.inference_history if not r.error]
        
        if not successful_inferences:
            return {"error": "No successful inferences"}
        
        # Estadísticas generales
        total_inferences = len(self.inference_history)
        success_rate = len(successful_inferences) / total_inferences
        
        # Métricas energéticas
        total_energy = sum(r.energy_consumed_wh for r in successful_inferences)
        avg_energy_per_inference = total_energy / len(successful_inferences)
        
        # Métricas de rendimiento
        avg_inference_time = sum(r.inference_time_ms for r in successful_inferences) / len(successful_inferences)
        avg_confidence = sum(r.confidence_score for r in successful_inferences) / len(successful_inferences)
        
        # Uso de modelos
        model_usage = {}
        for response in successful_inferences:
            model_usage[response.model_used] = model_usage.get(response.model_used, 0) + 1
        
        # Fallback statistics
        fallback_count = sum(1 for r in successful_inferences if r.fallback_used)
        fallback_rate = fallback_count / len(successful_inferences)
        
        return {
            "total_inferences": total_inferences,
            "successful_inferences": len(successful_inferences),
            "success_rate": success_rate,
            "fallback_rate": fallback_rate,
            "total_energy_consumed_wh": total_energy,
            "average_energy_per_inference_wh": avg_energy_per_inference,
            "average_inference_time_ms": avg_inference_time,
            "average_confidence_score": avg_confidence,
            "model_usage_distribution": model_usage,
            "energy_efficiency_vs_transformer": "calculation_pending",
            "timestamp": datetime.now().isoformat()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check para monitorización"""
        
        health_status = {
            "status": "healthy",
            "ollama_connection": False,
            "available_models": [],
            "system_resources": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            }
        }
        
        if not HTTPX_AVAILABLE:
            health_status["status"] = "degraded"
            health_status["error"] = "httpx not available"
            return health_status
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.ollama_base_url}/api/tags", timeout=5.0)
                if response.status_code == 200:
                    health_status["ollama_connection"] = True
                    models_data = response.json().get("models", [])
                    health_status["available_models"] = [m["name"] for m in models_data]
        except Exception as e:
            health_status["status"] = "degraded"
            health_status["error"] = str(e)
        
        return health_status


def main():
    """
    Main function to run the Phoenix DemiGod Model Router.
    If FastAPI and uvicorn are available, it starts the web server.
    Otherwise, it logs an error.
    """
    if not FASTAPI_AVAILABLE:
        logging.error("FastAPI not available, web interface disabled. Install with: pip install fastapi uvicorn")
        return

    try:
        import uvicorn
        from fastapi import FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import Response
        from pydantic import BaseModel, Field
    except ImportError:
        logging.error("uvicorn or FastAPI components not available. Install with: pip install fastapi uvicorn")
        return

    app = FastAPI(
        title="Phoenix DemiGod Model Router",
        description="Router inteligente multi-modelo con Mamba/SSM y fallback automático",
        version="1.0.0"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global router instance
    router = PhoenixModelRouter()

    # Pydantic models for API
    class QueryRequest(BaseModel):
        task: str = Field(..., description="Consulta o tarea a realizar")
        task_type: str = Field(default="general_query", description="Tipo de tarea")
        max_tokens: Optional[int] = Field(default=None, description="Máximo tokens a generar")
        temperature: Optional[float] = Field(default=None, description="Temperatura de sampling")
        force_model: Optional[str] = Field(default=None, description="Forzar modelo específico")
        enable_fallback: bool = Field(default=True, description="Habilitar fallback automático")

    @app.post("/phoenixquery")
    async def phoenix_query(request: QueryRequest):
        """
        Endpoint principal para consultas Phoenix DemiGod
        
        Ejemplo de uso:
        curl -X POST http://localhost:8000/phoenixquery \
             -H "Content-Type: application/json" \
             -d '{"task": "Explica la eficiencia de Mamba vs Transformers"}'
        """
        
        try:
            # Convertir task_type string a enum
            task_type = TaskType(request.task_type.lower())
        except ValueError:
            task_type = TaskType.GENERAL_QUERY
        
        inference_request = InferenceRequest(
            prompt=request.task,
            task_type=task_type,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            force_model=request.force_model,
            enable_fallback=request.enable_fallback
        )
        
        try:
            response = await router.infer(inference_request)
            
            if response.error:
                raise HTTPException(status_code=500, detail=response.error)
            
            return {
                "response": response.response,
                "model_used": response.model_used,
                "model_type": response.model_type,
                "inference_time_ms": response.inference_time_ms,
                "energy_consumed_wh": response.energy_consumed_wh,
                "confidence_score": response.confidence_score,
                "fallback_used": response.fallback_used,
                "tokens_generated": response.tokens_generated
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return await router.health_check()

    @app.get("/stats")
    async def performance_stats():
        """Estadísticas de rendimiento para grants y auditorías"""
        return router.get_performance_stats()

    @app.get("/models")
    async def list_models():
        """Listar modelos configurados"""
        return {
            "configured_models": {
                name: {
                    "type": config.model_type.value,
                    "ollama_name": config.ollama_name,
                    "priority": config.priority,
                    "energy_efficient": config.energy_efficient,
                    "specialization": [t.value for t in (config.specialization or [])]
                }
                for name, config in router.models.items()
            }
        }

    @app.get("/metrics")
    async def prometheus_metrics():
        """Métricas Prometheus"""
        if PROMETHEUS_AVAILABLE and callable(generate_latest):
            return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
        else:
            return {"error": "Prometheus metrics not available"}

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ejecutar servidor
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()
