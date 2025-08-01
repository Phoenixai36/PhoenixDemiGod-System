#!/bin/bash
# Phoenix DemiGod v8.7 - Complete Installation Script

set -e

echo "🚀 Phoenix DemiGod v8.7 - Instalación Completa"
echo "=============================================="

# Load environment
# source config/phoenix_env.sh

# Create directories
echo "📁 Creando directorios..."
mkdir -p $PHOENIX_LOGS $PHOENIX_BACKUPS models/cache logs

# Install Windsurf
echo "💻 Instalando Windsurf IDE..."
./scripts/setup/install_windsurf.sh

# Setup Jan.ai
echo "🤖 Configurando Jan.ai..."
./scripts/setup/setup_janai.sh

# Install Ollama and models
echo "🦙 Instalando Ollama y modelos..."
./scripts/setup/install_ollama.sh

# Setup MCP servers
echo "🔗 Configurando MCP servers..."
./scripts/setup/setup_mcp.sh

# Install CLI tools
echo "🛠️  Instalando herramientas CLI..."
code --install-extension kilocode.kilocode
code --install-extension saoudrizwan.claude-dev
code --install-extension roo-code.roo-code

# Setup workflows
echo "⚙️  Configurando workflows..."
docker-compose up -d n8n windmill

# Setup OMAS agents
echo "🤝 Configurando agentes OMAS..."
cd agents/rasa-phoenix && rasa train && cd -
python agents/ontology/setup_ontology.py

# Final validation
echo "✅ Validación final..."
./scripts/validation/final_validation.sh

echo "🎉 Instalación completada exitosamente!"
echo "💡 Para iniciar: source config/phoenix_env.sh"
