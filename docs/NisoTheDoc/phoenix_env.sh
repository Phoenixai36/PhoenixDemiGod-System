#!/bin/bash
# Phoenix DemiGod v8.7 - Environment Configuration

# Base paths
export PHOENIX_HOME="$HOME/phoenix-demigod-v8.7"
export PHOENIX_CONFIG="$PHOENIX_HOME/config"
export PHOENIX_MODELS="$PHOENIX_HOME/models"
export PHOENIX_LOGS="$PHOENIX_HOME/logs"
export PHOENIX_BACKUPS="$PHOENIX_HOME/backups"

# API Endpoints
export JAN_API_BASE="http://localhost:1337"
export OLLAMA_HOST="http://localhost:11434"
export N8N_HOST="http://localhost:5678"
export WINDMILL_HOST="http://localhost:3000"

# MCP Configuration
export MCP_SERVERS_CONFIG="$PHOENIX_CONFIG/mcp_config.json"

# Python configuration
export PYTHONPATH="$PHOENIX_HOME:$PYTHONPATH"
export PYTHON_UNBUFFERED=1

# GPU Configuration
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# Optimization flags
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8

# Logging
export PHOENIX_LOG_LEVEL="INFO"
export PHOENIX_LOG_FORMAT="%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Model configuration
export LLAMA_MODEL="llama3.2:8b"
export QWEN_MODEL="qwen2.5-coder:7b"
export DEEPSEEK_MODEL="deepseek-r1:7b"

# Performance tuning
export TOKENIZERS_PARALLELISM=false
export TRANSFORMERS_OFFLINE=1

echo "Phoenix DemiGod v8.7 environment loaded successfully"
echo "Base path: $PHOENIX_HOME"
echo "API endpoints configured"
