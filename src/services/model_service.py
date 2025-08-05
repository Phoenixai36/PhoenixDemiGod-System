#!/usr/bin/env python3
"""
Phoenix Hydra Model Service
FastAPI service for model management and inference
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..core.model_manager import (
    ModelStatus,
    ModelType,
    PhoenixModelManager,
    download_all_models,
    get_active_model,
    health_check,
    list_models,
    load_model,
    model_manager,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Phoenix Hydra Model Service",
    description="Local AI model management and inference service",
    version="1.0.0"
)

# Pydantic models for API
class ModelDownloadRequest(BaseModel):
    model_names: Optional[List[str]] = None
    parallel: bool = True
    max_concurrent: int = 3

class ModelLoadRequest(BaseModel):
    model_name: str

class ModelSetActiveRequest(BaseModel):
    model_type: str
    model_name: str

class InferenceRequest(BaseModel):
    model_type: str
    prompt: str
    parameters: Optional[Dict[str, Any]] = None

class InferenceResponse(BaseModel):
    model_name: str
    response: str
    tokens_used: Optional[int] = None
    inference_time_ms: float
    timestamp: str

# API Routes

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Phoenix Hydra Model Service",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_endpoint():
    """Health check endpoint"""
    try:
        health_status = await health_check()
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def list_models_endpoint(model_type: Optional[str] = None):
    """List all models or models of specific type"""
    try:
        model_type_enum = ModelType(model_type) if model_type else None
        models = list_models(model_type_enum)
        return {"models": models}
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid model type: {model_type}")
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/{model_name}/status")
async def get_model_status(model_name: str):
    """Get status of specific model"""
    try:
        status = model_manager.get_model_status(model_name)
        if status is None:
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
        
        return {
            "model_name": model_name,
            "status": status.value,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/download")
async def download_models(request: ModelDownloadRequest, background_tasks: BackgroundTasks):
    """Download models"""
    try:
        if request.model_names:
            # Download specific models
            results = {}
            for model_name in request.model_names:
                if model_name not in model_manager.models:
                    results[model_name] = False
                    continue
                
                if request.parallel:
                    background_tasks.add_task(model_manager.download_model, model_name)
                    results[model_name] = "downloading"
                else:
                    results[model_name] = await model_manager.download_model(model_name)
        else:
            # Download all models
            if request.parallel:
                background_tasks.add_task(
                    download_all_models,
                    parallel=request.parallel,
                    max_concurrent=request.max_concurrent
                )
                results = {"status": "downloading_all"}
            else:
                results = await download_all_models(
                    parallel=request.parallel,
                    max_concurrent=request.max_concurrent
                )
        
        return {"results": results, "timestamp": datetime.now().isoformat()}
        
    except Exception as e:
        logger.error(f"Error downloading models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/{model_name}/load")
async def load_model_endpoint(model_name: str, background_tasks: BackgroundTasks):
    """Load a specific model"""
    try:
        if model_name not in model_manager.models:
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
        
        # Load model in background
        background_tasks.add_task(load_model, model_name)
        
        return {
            "model_name": model_name,
            "status": "loading",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/active")
async def set_active_model(request: ModelSetActiveRequest):
    """Set active model for a type"""
    try:
        model_type = ModelType(request.model_type)
        success = model_manager.set_active_model(model_type, request.model_name)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to set active model")
        
        return {
            "model_type": request.model_type,
            "active_model": request.model_name,
            "timestamp": datetime.now().isoformat()
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid model type: {request.model_type}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting active model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/active")
async def get_active_models():
    """Get all active models"""
    try:
        active_models = {}
        for model_type in ModelType:
            active_model = get_active_model(model_type)
            if active_model:
                active_models[model_type.value] = active_model
        
        return {
            "active_models": active_models,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting active models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/inference")
async def inference_endpoint(request: InferenceRequest):
    """Perform inference with specified model type"""
    start_time = datetime.now()
    
    try:
        # Get active model for the requested type
        model_type = ModelType(request.model_type)
        active_model_name = get_active_model(model_type)
        
        if not active_model_name:
            raise HTTPException(
                status_code=404, 
                detail=f"No active model found for type {request.model_type}"
            )
        
        # Get model instance
        model_instance = model_manager.models.get(active_model_name)
        if not model_instance or model_instance.status != ModelStatus.LOADED:
            raise HTTPException(
                status_code=503,
                detail=f"Model {active_model_name} is not loaded"
            )
        
        # Perform inference based on model type
        response_text = await _perform_inference(
            model_instance, request.prompt, request.parameters or {}
        )
        
        # Calculate inference time
        end_time = datetime.now()
        inference_time_ms = (end_time - start_time).total_seconds() * 1000
        
        return InferenceResponse(
            model_name=active_model_name,
            response=response_text,
            inference_time_ms=inference_time_ms,
            timestamp=end_time.isoformat()
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid model type: {request.model_type}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during inference: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _perform_inference(model_instance, prompt: str, parameters: Dict[str, Any]) -> str:
    """Perform inference with the given model instance"""
    model_config = model_instance.config
    model_object = model_instance.model_object
    
    if model_config.type == ModelType.SSM:
        # SSM model inference
        if hasattr(model_object, 'analyze_components'):
            # Convert prompt to component data format
            component_data = {"text": prompt, "timestamp": datetime.now().isoformat()}
            result = await model_object.analyze_components([component_data])
            return str(result)
        else:
            return "SSM model inference not implemented"
    
    elif model_config.type == ModelType.VISION:
        # Vision model inference
        if "clip" in model_config.name.lower():
            # CLIP text-image similarity
            return f"CLIP vision inference for: {prompt}"
        elif "yolo" in model_config.name.lower():
            # YOLO object detection
            return f"YOLO object detection for: {prompt}"
        else:
            return f"Vision inference for: {prompt}"
    
    elif model_config.type == ModelType.AUDIO:
        # Audio/TTS inference
        return f"Audio synthesis for: {prompt}"
    
    elif model_config.type == ModelType.BIOMIMETIC:
        # Biomimetic agent inference
        if hasattr(model_object, 'process_input'):
            return await model_object.process_input(prompt)
        else:
            return f"Biomimetic agent processing: {prompt}"
    
    elif model_config.ollama_name:
        # Ollama model inference
        try:
            process = await asyncio.create_subprocess_exec(
                "ollama", "run", model_config.ollama_name, prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return stdout.decode().strip()
            else:
                logger.error(f"Ollama inference failed: {stderr.decode()}")
                return f"Error: {stderr.decode()}"
                
        except Exception as e:
            logger.error(f"Ollama inference error: {e}")
            return f"Error: {str(e)}"
    
    elif isinstance(model_object, dict) and "model" in model_object:
        # Hugging Face transformers model
        try:
            from transformers import pipeline
            
            # Create appropriate pipeline based on model type
            if model_config.type == ModelType.CODING:
                pipe = pipeline("text-generation", 
                              model=model_object["model"], 
                              tokenizer=model_object["tokenizer"])
            else:
                pipe = pipeline("text-generation", 
                              model=model_object["model"], 
                              tokenizer=model_object["tokenizer"])
            
            result = pipe(prompt, 
                         max_length=parameters.get("max_tokens", 512),
                         temperature=parameters.get("temperature", 0.7),
                         do_sample=True)
            
            return result[0]["generated_text"]
            
        except Exception as e:
            logger.error(f"Transformers inference error: {e}")
            return f"Error: {str(e)}"
    
    else:
        return f"Inference not implemented for model type: {model_config.type.value}"

@app.get("/system/requirements")
async def get_system_requirements():
    """Get system requirements for current model configuration"""
    try:
        requirements = model_manager.get_system_requirements()
        return {
            "requirements": requirements,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system requirements: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/system/optimize")
async def optimize_system():
    """Optimize system for current model load"""
    try:
        # Basic optimization - unload unused models
        unloaded_models = []
        
        for name, instance in model_manager.models.items():
            if (instance.status == ModelStatus.LOADED and 
                name not in model_manager.active_models.values()):
                # Unload non-active models to free memory
                instance.status = ModelStatus.DOWNLOADED
                instance.model_object = None
                instance.loaded_at = None
                unloaded_models.append(name)
        
        model_manager._save_config()
        
        return {
            "optimized": True,
            "unloaded_models": unloaded_models,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error optimizing system: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize model manager on startup"""
    logger.info("Starting Phoenix Hydra Model Service")
    
    # Load existing configuration
    model_manager.load_config()
    
    # Log system status
    requirements = model_manager.get_system_requirements()
    logger.info(f"System requirements: {requirements}")
    
    logger.info("Phoenix Hydra Model Service started successfully")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Phoenix Hydra Model Service")
    
    # Save current configuration
    model_manager._save_config()
    
    logger.info("Phoenix Hydra Model Service shutdown complete")

if __name__ == "__main__":
    uvicorn.run(
        "src.services.model_service:app",
        host="0.0.0.0",
        port=8090,
        reload=False,
        workers=1
    )