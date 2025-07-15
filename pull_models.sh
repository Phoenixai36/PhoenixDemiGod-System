#!/usr/bin/env bash
set -e
podman start ollama 2>/dev/null || true

MODELS=(
  "codestral-mamba-7b-instruct-q4"
  "deepseek-r1-7b-instruct-q4"
  "phi-3mini-4k-instruct-q4"
  "rwkv-7b-world-q4"
  "llama3:8b-instruct-q4"
)

for M in "${MODELS[@]}"; do
  echo "Descargando $M..."
  podman exec ollama ollama pull "$M"
done

echo "✅  Modelos listos."