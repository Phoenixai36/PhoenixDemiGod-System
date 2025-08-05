#!/usr/bin/env python3
"""
Phoenix Hydra Local Processing Demo
Demonstrates local AI model processing capabilities
"""

import asyncio
import json

# Add src to path
import sys
import time
from pathlib import Path
from typing import Any, Dict

import requests

sys.path.append(str(Path(__file__).parent.parent))

from src.core.model_manager import ModelType, model_manager


class PhoenixLocalProcessingDemo:
    """Demo class for Phoenix Hydra local processing"""
    
    def __init__(self, model_service_url: str = "http://localhost:8090"):
        self.model_service_url = model_service_url
        self.session = requests.Session()
    
    def check_service_health(self) -> bool:
        """Check if model service is running"""
        try:
            response = self.session.get(f"{self.model_service_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_available_models(self) -> Dict[str, Any]:
        """List all available models"""
        try:
            response = self.session.get(f"{self.model_service_url}/models")
            return response.json()
        except Exception as e:
            print(f"Error listing models: {e}")
            return {"models": []}
    
    def get_active_models(self) -> Dict[str, Any]:
        """Get currently active models"""
        try:
            response = self.session.get(f"{self.model_service_url}/models/active")
            return response.json()
        except Exception as e:
            print(f"Error getting active models: {e}")
            return {"active_models": {}}
    
    def perform_inference(self, model_type: str, prompt: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Perform inference with specified model type"""
        try:
            payload = {
                "model_type": model_type,
                "prompt": prompt,
                "parameters": parameters or {}
            }
            
            response = self.session.post(
                f"{self.model_service_url}/inference",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def download_models(self, model_names: list = None) -> Dict[str, Any]:
        """Download specified models or all models"""
        try:
            payload = {
                "model_names": model_names,
                "parallel": True,
                "max_concurrent": 3
            }
            
            response = self.session.post(
                f"{self.model_service_url}/models/download",
                json=payload,
                timeout=300  # 5 minutes for downloads
            )
            
            return response.json()
            
        except Exception as e:
            return {"error": str(e)}
    
    def run_comprehensive_demo(self):
        """Run comprehensive local processing demo"""
        print("🚀 Phoenix Hydra Local Processing Demo")
        print("=" * 50)
        
        # Check service health
        print("\n1. Checking Model Service Health...")
        if not self.check_service_health():
            print("❌ Model service is not running!")
            print("Please start the service with: python -m src.services.model_service")
            return
        print("✅ Model service is healthy")
        
        # List available models
        print("\n2. Listing Available Models...")
        models_data = self.list_available_models()
        models = models_data.get("models", [])
        
        if not models:
            print("❌ No models found!")
            return
        
        print(f"📊 Found {len(models)} models:")
        for model in models[:5]:  # Show first 5
            status_emoji = "✅" if model["status"] == "loaded" else "⏳" if model["status"] == "downloaded" else "❌"
            print(f"  {status_emoji} {model['name']} ({model['type']}) - {model['status']}")
        
        # Get active models
        print("\n3. Active Models Configuration...")
        active_models = self.get_active_models()
        active = active_models.get("active_models", {})
        
        if active:
            print("🎯 Active models by type:")
            for model_type, model_name in active.items():
                print(f"  • {model_type}: {model_name}")
        else:
            print("⚠️  No active models configured")
        
        # Demo different model types
        print("\n4. Local Processing Demonstrations...")
        
        # Reasoning Demo
        print("\n🧠 Reasoning Model Demo:")
        reasoning_result = self.perform_inference(
            "reasoning",
            "Explain the benefits of local AI processing for privacy and energy efficiency.",
            {"max_tokens": 200, "temperature": 0.7}
        )
        
        if "error" not in reasoning_result:
            print(f"✅ Response: {reasoning_result.get('response', 'No response')[:200]}...")
            print(f"⚡ Inference time: {reasoning_result.get('inference_time_ms', 0):.2f}ms")
        else:
            print(f"❌ Error: {reasoning_result['error']}")
        
        # Coding Demo
        print("\n💻 Coding Model Demo:")
        coding_result = self.perform_inference(
            "coding",
            "Write a Python function to calculate the Fibonacci sequence efficiently.",
            {"max_tokens": 300, "temperature": 0.1}
        )
        
        if "error" not in coding_result:
            print(f"✅ Code generated successfully")
            print(f"⚡ Inference time: {coding_result.get('inference_time_ms', 0):.2f}ms")
            print("📝 Generated code preview:")
            print(coding_result.get('response', 'No response')[:300] + "...")
        else:
            print(f"❌ Error: {coding_result['error']}")
        
        # SSM Demo (if available)
        print("\n🔬 SSM Analysis Demo:")
        ssm_result = self.perform_inference(
            "ssm",
            "Analyze system component health and performance patterns.",
            {"d_model": 256, "d_state": 32}
        )
        
        if "error" not in ssm_result:
            print(f"✅ SSM analysis completed")
            print(f"⚡ Inference time: {ssm_result.get('inference_time_ms', 0):.2f}ms")
        else:
            print(f"❌ Error: {ssm_result['error']}")
        
        # Performance Summary
        print("\n5. Performance Summary...")
        total_time = sum([
            reasoning_result.get('inference_time_ms', 0),
            coding_result.get('inference_time_ms', 0),
            ssm_result.get('inference_time_ms', 0)
        ])
        
        print(f"🏁 Total inference time: {total_time:.2f}ms")
        print(f"⚡ Average per inference: {total_time/3:.2f}ms")
        print("🌱 All processing done locally with energy-efficient models!")
        
        # System Requirements
        print("\n6. System Resource Usage...")
        try:
            response = self.session.get(f"{self.model_service_url}/system/requirements")
            if response.status_code == 200:
                requirements = response.json()["requirements"]
                print(f"💾 Memory usage: {requirements['total_memory_mb']}MB")
                print(f"🔧 CPU threads: {requirements['max_cpu_threads']}")
                print(f"🎮 GPU required: {'Yes' if requirements['gpu_required'] else 'No'}")
                print(f"📊 Loaded models: {requirements['loaded_models']}")
        except:
            print("⚠️  Could not retrieve system requirements")
        
        print("\n🎉 Demo completed successfully!")
        print("🔗 Access the model service at: http://localhost:8090")
        print("📚 API documentation at: http://localhost:8090/docs")

def main():
    """Main demo function"""
    demo = PhoenixLocalProcessingDemo()
    demo.run_comprehensive_demo()

if __name__ == "__main__":
    main()