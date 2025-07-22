#!/usr/bin/env python3
"""
Phoenix DemiGod v8.7 - MCP Router Principal
Router central para coordinación entre componentes del sistema
"""

import asyncio
import json
import aiohttp
from typing import Dict, Any, List
import logging
from datetime import datetime

class PhoenixMCPRouter:
    def __init__(self):
        self.jan_api_base = "http://localhost:1337"
        self.n8n_base = "http://localhost:5678"
        self.windmill_base = "http://localhost:3000"
        self.ollama_base = "http://localhost:11434"

        self.setup_logging()
        self.active_sessions = {}

    def setup_logging(self):
        """Configure logging for MCP router"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - Phoenix MCP Router - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/mcp_router.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    async def route_to_jan(self, prompt: str, model: str = "llama3.2:8b") -> Dict[str, Any]:
        """Route requests to Jan.ai API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.jan_api_base}/v1/chat/completions",
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 2000
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.logger.info(f"Jan.ai response successful for model {model}")
                        return result
                    else:
                        self.logger.error(f"Jan.ai API error: {response.status}")
                        return {"error": f"API error: {response.status}"}
        except Exception as e:
            self.logger.error(f"Jan.ai connection failed: {e}")
            return {"error": str(e)}

    async def execute_workflow(self, workflow_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute n8n workflow"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.n8n_base}/webhook/{workflow_name}",
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.logger.info(f"Workflow {workflow_name} executed successfully")
                        return result
                    else:
                        return {"error": f"Workflow error: {response.status}"}
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            return {"error": str(e)}

    async def run_windmill_script(self, script_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Windmill automation script"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.windmill_base}/api/w/phoenix/jobs/run/f/{script_name}",
                    json=params
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.logger.info(f"Windmill script {script_name} executed")
                        return result
                    else:
                        return {"error": f"Windmill error: {response.status}"}
        except Exception as e:
            return {"error": str(e)}

    async def health_check(self) -> Dict[str, bool]:
        """Check health of all system components"""
        health_status = {}

        # Check Jan.ai
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.jan_api_base}/v1/models") as response:
                    health_status['jan_api'] = response.status == 200
        except:
            health_status['jan_api'] = False

        # Check n8n
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.n8n_base}/healthz") as response:
                    health_status['n8n'] = response.status == 200
        except:
            health_status['n8n'] = False

        # Check Windmill
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.windmill_base}/api/version") as response:
                    health_status['windmill'] = response.status == 200
        except:
            health_status['windmill'] = False

        return health_status

if __name__ == "__main__":
    router = PhoenixMCPRouter()
    print("Phoenix MCP Router iniciado - Puerto 8000")
    # Aquí iría la implementación del servidor MCP
