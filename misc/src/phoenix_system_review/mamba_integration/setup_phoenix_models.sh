#!/bin/bash

# Phoenix DemiGod Model Setup Script
# Descarga y configura modelos Mamba/SSM para procesamiento 100% local

set -e

echo "🚀 Phoenix DemiGod - Setup de Modelos Mamba/SSM"
echo "================================================"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Verificar que Ollama está instalado
if ! command -v ollama &> /dev/null; then
    echo -e "${RED}❌ Ollama no está instalado${NC}"
    echo "Instala Ollama desde: https://ollama.ai"
    exit 1
fi

echo -e "${GREEN}✅ Ollama encontrado${NC}"

# Verificar que Ollama está corriendo
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo -e "${YELLOW}⚠️  Iniciando Ollama...${NC}"
    ollama serve &
    sleep 5
fi

echo -e "${GREEN}✅ Ollama está corriendo${NC}"

# Función para descargar modelo con verificación
download_model() {
    local model_name=$1
    local description=$2
    
    echo -e "${BLUE}📥 Descargando $description ($model_name)...${NC}"
    
    if ollama list | grep -q "$model_name"; then
        echo -e "${YELLOW}⚠️  $model_name ya está descargado${NC}"
    else
        if ollama pull "$model_name"; then
            echo -e "${GREEN}✅ $model_name descargado correctamente${NC}"
        else
            echo -e "${RED}❌ Error descargando $model_name${NC}"
            return 1
        fi
    fi
}

# Descargar modelos según especificación
echo -e "${BLUE}🧠 Descargando modelos Mamba/SSM y fallbacks...${NC}"

# Modelo principal para código (Mamba-based)
download_model "deepseek-coder:6.7b" "Modelo principal para análisis de código"

# Modelo Mamba para razonamiento (si está disponible)
# Nota: Algunos modelos Mamba pueden no estar en Ollama aún
download_model "llama3.2:8b" "Modelo de razonamiento (fallback transformer)"

# Modelo de fallback general
download_model "llama3.2:3b" "Modelo de fallback ligero"

# Modelo especialista en código
download_model "qwen2.5-coder:7b" "Especialista en código avanzado"

# Verificar modelos descargados
echo -e "${BLUE}📋 Modelos disponibles:${NC}"
ollama list

# Crear archivo de configuración .env
echo -e "${BLUE}⚙️  Creando configuración...${NC}"

cat > .env << EOF
# Phoenix DemiGod Model Configuration
# Configuración de modelos para router multi-modelo

# Modelo principal (más eficiente)
DEFAULTMODEL=deepseek-coder:6.7b

# Modelo para razonamiento (Mamba cuando esté disponible)
AGENTICMODEL=llama3.2:8b

# Modelo de fallback
FALLBACKMODEL=llama3.2:3b

# Especialista en código
SPECIALISTMODEL=qwen2.5-coder:7b

# Configuración de inferencia
QUANTIZATION=4bit
INFERENCEMODE=LOCAL
AGENTMODE=true
ENABLEFALLBACK=true

# Ollama configuration
OLLAMA_BASE_URL=http://localhost:11434

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true

# Energy efficiency targets
ENERGY_REDUCTION_TARGET=65
MAX_WATTS_PER_INFERENCE=150
EOF

echo -e "${GREEN}✅ Archivo .env creado${NC}"

# Crear script de test
echo -e "${BLUE}🧪 Creando script de test...${NC}"

cat > test_phoenix_router.py << 'EOF'
#!/usr/bin/env python3
"""
Test script para Phoenix DemiGod Model Router
Verifica que todos los modelos funcionan correctamente
"""

import asyncio
import httpx
import json
import time

async def test_phoenix_router():
    """Test del router multi-modelo"""
    
    base_url = "http://localhost:8000"
    
    # Test queries
    test_queries = [
        {
            "task": "Explica la eficiencia de Mamba vs Transformers",
            "task_type": "reasoning",
            "description": "Test de razonamiento"
        },
        {
            "task": "Analiza este código Python: def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
            "task_type": "code_analysis", 
            "description": "Test de análisis de código"
        },
        {
            "task": "¿Cuáles son las mejores prácticas para contenedores Docker?",
            "task_type": "general_query",
            "description": "Test de consulta general"
        }
    ]
    
    print("🧪 Testing Phoenix DemiGod Model Router")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        # Test health check
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                health = response.json()
                print(f"✅ Health Check: {health['status']}")
                print(f"📊 Ollama Connection: {health['ollama_connection']}")
                print(f"🤖 Available Models: {len(health['available_models'])}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return
        except Exception as e:
            print(f"❌ Cannot connect to Phoenix Router: {e}")
            print("💡 Make sure to run: python phoenix_model_router.py")
            return
        
        # Test queries
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Test {i}: {query['description']}")
            print(f"📝 Query: {query['task'][:50]}...")
            
            start_time = time.time()
            
            try:
                response = await client.post(
                    f"{base_url}/phoenixquery",
                    json=query
                )
                
                if response.status_code == 200:
                    result = response.json()
                    duration = time.time() - start_time
                    
                    print(f"✅ Success!")
                    print(f"🤖 Model Used: {result['model_used']}")
                    print(f"⚡ Inference Time: {result['inference_time_ms']:.1f}ms")
                    print(f"🔋 Energy Consumed: {result['energy_consumed_wh']:.4f}Wh")
                    print(f"🎯 Confidence: {result['confidence_score']:.2f}")
                    print(f"🔄 Fallback Used: {result['fallback_used']}")
                    print(f"📊 Total Duration: {duration:.2f}s")
                    print(f"💬 Response: {result['response'][:100]}...")
                    
                else:
                    print(f"❌ Request failed: {response.status_code}")
                    print(f"Error: {response.text}")
                    
            except Exception as e:
                print(f"❌ Test failed: {e}")
        
        # Get performance stats
        print(f"\n📈 Performance Statistics")
        print("=" * 30)
        
        try:
            response = await client.get(f"{base_url}/stats")
            if response.status_code == 200:
                stats = response.json()
                print(f"📊 Total Inferences: {stats.get('total_inferences', 0)}")
                print(f"✅ Success Rate: {stats.get('success_rate', 0):.2%}")
                print(f"🔄 Fallback Rate: {stats.get('fallback_rate', 0):.2%}")
                print(f"⚡ Avg Inference Time: {stats.get('average_inference_time_ms', 0):.1f}ms")
                print(f"🔋 Energy Efficiency vs Transformer: {stats.get('energy_efficiency_vs_transformer', 'N/A')}")
        except Exception as e:
            print(f"❌ Stats failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_phoenix_router())
EOF

chmod +x test_phoenix_router.py

echo -e "${GREEN}✅ Script de test creado${NC}"

# Crear docker-compose para monitorización
echo -e "${BLUE}📊 Creando configuración de monitorización...${NC}"

cat > docker-compose.monitoring.yml << 'EOF'
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: phoenix-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    networks:
      - phoenix-monitoring

  grafana:
    image: grafana/grafana:latest
    container_name: phoenix-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=phoenix123
    volumes:
      - grafana-storage:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources
    networks:
      - phoenix-monitoring

volumes:
  grafana-storage:

networks:
  phoenix-monitoring:
    driver: bridge
EOF

# Crear configuración de Prometheus
mkdir -p monitoring
cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'phoenix-router'
    static_configs:
      - targets: ['host.docker.internal:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
EOF

echo -e "${GREEN}✅ Configuración de monitorización creada${NC}"

# Instrucciones finales
echo -e "${GREEN}"
echo "🎉 Setup completado!"
echo "==================="
echo -e "${NC}"
echo "📋 Próximos pasos:"
echo ""
echo "1. 🚀 Iniciar el router:"
echo "   python src/phoenix_system_review/mamba_integration/phoenix_model_router.py"
echo ""
echo "2. 🧪 Ejecutar tests:"
echo "   python test_phoenix_router.py"
echo ""
echo "3. 📊 Iniciar monitorización (opcional):"
echo "   docker-compose -f docker-compose.monitoring.yml up -d"
echo "   Grafana: http://localhost:3000 (admin/phoenix123)"
echo "   Prometheus: http://localhost:9090"
echo ""
echo "4. 🔍 Test manual:"
echo "   curl -X POST http://localhost:8000/phoenixquery \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"task\": \"Explica la eficiencia de Mamba\"}'"
echo ""
echo -e "${BLUE}📚 Documentación:${NC}"
echo "   - Health Check: http://localhost:8000/health"
echo "   - Stats: http://localhost:8000/stats"
echo "   - Models: http://localhost:8000/models"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo -e "${GREEN}✨ Phoenix DemiGod está listo para procesamiento 100% local!${NC}"