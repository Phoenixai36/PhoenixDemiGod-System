# Phoenix Hydra Local Model Integration

This document provides comprehensive guidance for integrating local AI models into the Phoenix Hydra ecosystem, enabling 100% local processing with energy-efficient State Space Models (SSM).

## Overview

Phoenix Hydra's local model integration provides:

- **Energy Efficient Processing**: 60-70% less energy consumption than Transformer models
- **Complete Privacy**: 100% local processing, no external dependencies
- **Rootless Execution**: Secure container deployment without root privileges
- **Multi-Model Support**: Reasoning, coding, vision, audio, and biomimetic models
- **SSM Architecture**: State Space Models for efficient sequence processing
- **Automatic Fallbacks**: Robust model switching for reliability

## Quick Start

### 1. Automated Integration

Run the complete integration process:

```bash
# Download and integrate all models
python scripts/integrate_local_models.py

# Or use VS Code task: Ctrl+Shift+P → "Integrate Local Models"
```

### 2. Manual Integration Steps

If you prefer manual control:

```bash
# Step 1: Download model stack
bash scripts/download_2025_model_stack.sh

# Step 2: Start model service
python -m src.services.model_service

# Step 3: Test integration
python examples/local_processing_demo.py
```

### 3. Container Deployment

Deploy with Podman containers:

```bash
# Build and start all services including model service
podman-compose -f infra/podman/podman-compose.yaml up --build -d

# Check service health
curl http://localhost:8090/health
```

## Model Categories

### Reasoning Models (Primary: Zamba2-2.7B)
- **zamba2-2.7b**: Energy-efficient reasoning with long context
- **llama3-8b**: Robust fallback for complex reasoning
- **falcon-7b**: Alternative reasoning model

**Use Cases**: Analysis, chatbots, decision making, cross-validation

### Coding Models (Primary: DeepSeek-Coder-v2)
- **deepseek-coder-v2**: Advanced code generation and debugging
- **codestral-mamba-7b**: SSM-based coding with energy efficiency
- **qwen2.5-coder-7b**: Specialized code assistance

**Use Cases**: Code generation, debugging, technical documentation, automation

### General LLM Models
- **llama3.2**: Balanced general-purpose model
- **falcon-mamba-7b**: Energy-efficient general processing
- **mistral-7b**: Robust multilingual support

**Use Cases**: Conversational AI, general text processing, multilingual tasks

### Creative/Multimodal Models
- **phi-3-14b**: Creative text generation and multimodal tasks
- **nous-hermes2-mixtral**: Advanced creative capabilities
- **gemma-7b**: Efficient creative processing

**Use Cases**: Creative writing, art generation, multimedia analysis

### Vision Models
- **clip**: Image-text understanding and similarity
- **yolov11**: Real-time object detection
- **pixtal**: Advanced visual analysis

**Use Cases**: Image analysis, object detection, visual surveillance, bio-inspired vision

### Audio/TTS Models
- **chatterbox**: Multilingual text-to-speech
- **vits**: High-quality voice synthesis
- **coqui-xtts**: Advanced TTS with cloning

**Use Cases**: Voice alerts, audio applications, accessibility, bio-cyber integration

### Context Long/RAG Models
- **minimax-m1**: Ultra-long context processing (80k tokens)
- **command-r**: Advanced retrieval-augmented generation
- **qwen2.5-72b**: Large-scale document analysis

**Use Cases**: Document analysis, knowledge retrieval, long-form content

### CPU Optimized Models
- **rwkv-7b**: CPU-friendly with constant memory usage
- **jamba-1.5-mini**: Efficient edge processing
- **tinyllama**: Ultra-lightweight processing

**Use Cases**: Edge devices, resource-constrained environments, embedded systems

### SSM Models (Phoenix Hydra Specialty)
- **mamba-codestral-7b**: State Space Model for coding
- **state-spaces/mamba-130m**: Lightweight SSM processing
- **Custom SSM engines**: Phoenix-specific implementations

**Use Cases**: Efficient sequence processing, energy-optimized inference, real-time analysis

### Biomimetic Agent Models
- **rubik-agent-base**: Phoenix RUBIK ecosystem agents
- **neural-chat**: Conversational biomimetic agents
- **orca-mini**: Efficient agent processing

**Use Cases**: Multi-agent systems, evolutionary algorithms, bio-inspired computing

## API Usage

### Model Service Endpoints

The model service runs on `http://localhost:8090` with the following endpoints:

#### Health Check
```bash
curl http://localhost:8090/health
```

#### List Models
```bash
curl http://localhost:8090/models
```

#### Get Active Models
```bash
curl http://localhost:8090/models/active
```

#### Perform Inference
```bash
curl -X POST http://localhost:8090/inference \
  -H "Content-Type: application/json" \
  -d '{
    "model_type": "reasoning",
    "prompt": "Explain quantum computing",
    "parameters": {
      "max_tokens": 200,
      "temperature": 0.7
    }
  }'
```

#### Download Models
```bash
curl -X POST http://localhost:8090/models/download \
  -H "Content-Type: application/json" \
  -d '{
    "model_names": ["zamba2-2.7b", "deepseek-coder-v2"],
    "parallel": true,
    "max_concurrent": 3
  }'
```

#### Load Model
```bash
curl -X POST http://localhost:8090/models/zamba2-2.7b/load
```

#### Set Active Model
```bash
curl -X POST http://localhost:8090/models/active \
  -H "Content-Type: application/json" \
  -d '{
    "model_type": "reasoning",
    "model_name": "zamba2-2.7b"
  }'
```

### Python API Usage

```python
from src.core.model_manager import ModelType, model_manager
import asyncio

async def example_usage():
    # List available models
    models = model_manager.list_models(ModelType.REASONING)
    print(f"Reasoning models: {len(models)}")
    
    # Download a model
    success = await model_manager.download_model("zamba2-2.7b")
    print(f"Download success: {success}")
    
    # Load a model
    success = await model_manager.load_model("zamba2-2.7b")
    print(f"Load success: {success}")
    
    # Set active model
    model_manager.set_active_model(ModelType.REASONING, "zamba2-2.7b")
    
    # Health check
    health = await model_manager.health_check()
    print(f"System healthy: {health['overall_healthy']}")

# Run example
asyncio.run(example_usage())
```

## Configuration

### Model Configuration (`config/models.yaml`)

```yaml
models:
  zamba2-2.7b:
    config:
      name: "zamba2-2.7b"
      type: "reasoning"
      primary: true
      ollama_name: "zamba2:2.7b"
      huggingface_name: "Zyphra/Zamba2-2.7B"
      parameters:
        max_tokens: 8192
        temperature: 0.7
      memory_requirement_mb: 3072
      energy_efficient: true
    status: "downloaded"

active_models:
  reasoning: "zamba2-2.7b"
  coding: "deepseek-coder-v2"
  general: "llama3.2"
```

### Service Configuration (`config/model_service.yaml`)

```yaml
service:
  host: "0.0.0.0"
  port: 8090
  workers: 1

models:
  cache_dir: "~/.local/share/phoenix-hydra/models/cache"
  config_file: "config/models.yaml"
  auto_load_priority: true
  energy_efficient: true

inference:
  timeout_seconds: 30
  max_concurrent: 5
  memory_limit_mb: 8192

monitoring:
  health_check_interval: 30
  metrics_enabled: true
  prometheus_port: 8091
```

## Container Integration

### Podman Compose Configuration

The model service is integrated into the main Phoenix Hydra stack:

```yaml
services:
  model-service:
    build:
      context: ../..
      dockerfile: infra/podman/model-service/Containerfile
    ports:
      - "8090:8090"
    environment:
      - TRANSFORMERS_CACHE=/app/models/cache
      - HF_HOME=/app/models/cache
    volumes:
      - model_cache:/app/models/cache:Z
      - model_config:/app/config:Z
    networks:
      - phoenix-net
    security_opt:
      - no-new-privileges:true
    user: "1000:1000"
    restart: unless-stopped
```

### Volume Management

Models and cache are stored in persistent volumes:

```bash
# Model cache location
~/.local/share/phoenix-hydra/models/cache

# Configuration location
~/.local/share/phoenix-hydra/config

# Logs location
~/.local/share/phoenix-hydra/logs
```

## Performance Optimization

### Energy Efficiency

Phoenix Hydra prioritizes energy-efficient models:

- **SSM Architecture**: 60-70% less energy than Transformers
- **Quantization**: FP16 and INT8 model optimization
- **Memory Efficient**: Reduced memory footprint
- **CPU Optimization**: Efficient CPU-only inference

### Resource Management

```python
# Configure resource limits
from src.core.model_manager import SSMAnalysisConfig

config = SSMAnalysisConfig(
    d_model=256,        # Reduced for efficiency
    d_state=32,         # Optimized state dimension
    conv_width=4,       # Efficient convolution
    memory_efficient=True
)
```

### Concurrent Processing

```python
# Enable parallel model downloads
await model_manager.download_all_models(
    parallel=True,
    max_concurrent=3
)
```

## Monitoring and Observability

### Health Monitoring

```bash
# Check overall system health
curl http://localhost:8090/health

# Get system requirements
curl http://localhost:8090/system/requirements

# Optimize system resources
curl -X POST http://localhost:8090/system/optimize
```

### Prometheus Metrics

The model service exports Prometheus metrics:

- Model inference latency
- Memory usage per model
- Request throughput
- Error rates
- Energy consumption estimates

### Logging

Structured logging is available:

```bash
# View model service logs
podman-compose -f infra/podman/podman-compose.yaml logs -f model-service

# View integration logs
tail -f phoenix_model_integration_report.json
```

## Examples and Demos

### Local Processing Demo

```bash
python examples/local_processing_demo.py
```

Demonstrates:
- Model service health checking
- Multi-model inference
- Performance measurement
- Resource usage monitoring

### RUBIK Ecosystem Demo

```bash
python examples/rubik_ecosystem_demo.py
```

Demonstrates:
- Biomimetic agent evolution
- Multi-agent collaboration
- Local AI ecosystem simulation
- Energy-efficient processing

### SSM Analysis Demo

```bash
python examples/ssm_analysis_demo.py
```

Demonstrates:
- State Space Model analysis
- Component health monitoring
- Temporal pattern recognition
- Optimization recommendations

## Troubleshooting

### Common Issues

#### Model Download Failures
```bash
# Check Ollama status
ollama --version

# Check network connectivity
curl -I https://ollama.ai

# Manual model download
ollama pull zamba2:2.7b
```

#### Memory Issues
```bash
# Check available memory
free -h

# Optimize system
curl -X POST http://localhost:8090/system/optimize

# Reduce concurrent models
# Edit config/models.yaml to disable non-essential models
```

#### Permission Errors
```bash
# Check directory permissions
ls -la ~/.local/share/phoenix-hydra/

# Fix permissions
chmod -R 755 ~/.local/share/phoenix-hydra/
```

#### Service Not Starting
```bash
# Check logs
podman-compose -f infra/podman/podman-compose.yaml logs model-service

# Check port availability
netstat -tuln | grep 8090

# Restart service
podman-compose -f infra/podman/podman-compose.yaml restart model-service
```

### Debug Commands

```bash
# Debug model service container
podman exec -it phoenix-hydra_model-service_1 /bin/bash

# Check model files
ls -la ~/.local/share/phoenix-hydra/models/

# Test model loading
python -c "from src.core.model_manager import model_manager; print(model_manager.list_models())"

# Check system resources
python -c "from src.core.model_manager import model_manager; print(model_manager.get_system_requirements())"
```

## VS Code Integration

Available tasks (Ctrl+Shift+P → "Tasks: Run Task"):

- **Download 2025 Model Stack**: Download all models
- **Integrate Local Models**: Complete integration process
- **Start Model Service**: Start the model service
- **Test Local Processing**: Run processing demo
- **Test RUBIK Ecosystem**: Run biomimetic demo
- **Test SSM Analysis**: Run SSM analysis demo
- **Model Service Health Check**: Check service health
- **List Available Models**: Show all models
- **View Model Service Logs**: Monitor service logs

## Security Considerations

### Rootless Execution

All models run in rootless containers:

```dockerfile
# Create non-root user
RUN groupadd -r modeluser && useradd -r -g modeluser -u 1000 modeluser
USER modeluser
```

### Network Isolation

Models are isolated in the Phoenix network:

```yaml
networks:
  phoenix-net:
    driver: bridge
    internal: false
    attachable: true
```

### Resource Limits

Container resource limits prevent abuse:

```yaml
security_opt:
  - no-new-privileges:true
user: "1000:1000"
```

## Future Enhancements

### Planned Features

1. **Model Quantization**: Automatic INT8/INT4 quantization
2. **Distributed Inference**: Multi-node model serving
3. **Model Caching**: Intelligent model swapping
4. **Custom Models**: Support for user-trained models
5. **GPU Acceleration**: Optional GPU support
6. **Model Marketplace**: Community model sharing

### Integration Roadmap

- **Phase 1** (Complete): Basic local model integration
- **Phase 2** (Q2 2025): Advanced SSM models and optimization
- **Phase 3** (Q3 2025): Multi-modal and biomimetic agents
- **Phase 4** (Q4 2025): Distributed and edge deployment

## Support and Resources

### Documentation
- [Phoenix Hydra README](../README.md)
- [Podman Migration Guide](./podman-comprehensive-guide.md)
- [SSM Analysis Engine](../src/core/ssm_analysis_engine.py)

### Community
- GitHub Issues: Report bugs and feature requests
- Discussions: Community support and ideas
- Wiki: Additional documentation and examples

### Commercial Support
- NEOTEC Grant Program: €325k funding available
- Enterprise Support: Custom model integration
- Training Programs: Team onboarding and optimization

---

**Phoenix Hydra Local Model Integration** - Enabling 100% local AI processing with energy-efficient State Space Models for privacy, performance, and sustainability.