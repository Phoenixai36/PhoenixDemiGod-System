import pandas as pd
import csv

# Crear tabla detallada de configuración técnica para hackathon intensivo
config_data = {
    'Componente': [
        'Windsurf IDE',
        'Jan.ai API Server',
        'Kilo Code Extension',
        'Ollama + Mamba Models',
        'MCP Servers Phoenix',
        'n8n Workflows',
        'Windmill Automation',
        'Terraform Infrastructure',
        'MAP-E Chatbot',
        'OMAS Multi-Agent System',
        'Rasa Conversational Agents',
        'Gemini CLI Integration'
    ],
    'Comando_Instalación': [
        'Download from windsurf.com',
        'Download from jan.ai → Settings → API Server',
        'VS Code Marketplace: kilocode.ai',
        'curl -fsSL https://ollama.com/install.sh | sh',
        'Custom MCP server configuration',
        'docker run -it --rm --name n8n -p 5678:5678 n8nio/n8n',
        'curl -fsSL https://windmill.dev/install.sh | sh',
        'curl -fsSL https://releases.hashicorp.com/terraform/latest/terraform_linux_amd64.zip',
        'Integración API Jan.ai localhost:1337',
        'pip install rasa && python -m rasa init',
        'python -m rasa shell',
        'pip install google-generativeai'
    ],
    'Puerto_API': [
        'N/A',
        'localhost:1337',
        'N/A',
        'localhost:11434',
        'JSON-RPC',
        'localhost:5678',
        'localhost:3000',
        'N/A',
        'localhost:1337',
        'Custom ports',
        'localhost:5005',
        'CLI'
    ],
    'Configuración_Clave': [
        'MCP Store → Add custom servers',
        'Settings → Advanced → Enable API Server',
        'kilocode.providers.local.type: ollama',
        'ollama pull llama3.2:8b && ollama pull qwen2.5-coder:7b',
        'phoenix_router, rasa_bridge, ollama_bridge',
        'Webhook triggers → API endpoints',
        'Python/TypeScript scripts → Visual workflows',
        'HCL configuration → Resource provisioning',
        'OpenAI compatible API → localhost:1337',
        'Ontology reasoners → Agent communication',
        'NLU pipeline → Intent classification',
        'export GOOGLE_API_KEY=your_key'
    ],
    'Tiempo_Setup': [
        '30 min',
        '45 min',
        '15 min',
        '60 min',
        '90 min',
        '45 min',
        '60 min',
        '30 min',
        '120 min',
        '180 min',
        '90 min',
        '20 min'
    ],
    'Dependencias_Críticas': [
        'Electron, Node.js',
        'llama.cpp engine, GGUF models',
        'VS Code, Ollama running',
        'Docker optional, GPU drivers',
        'Python 3.8+, JSON-RPC libraries',
        'Docker, Node.js runtime',
        'Python 3.8+, PostgreSQL',
        'Go runtime, Cloud credentials',
        'Jan.ai API running',
        'Python 3.8+, Ontology libraries',
        'Python 3.8+, spaCy, TensorFlow',
        'Python 3.8+, google-generativeai'
    ],
    'Comando_Testing': [
        'Open project → Check MCP servers',
        'curl http://localhost:1337/v1/models',
        'Test with local model in VS Code',
        'ollama run llama3.2:8b "Hello world"',
        'Test MCP connection in Windsurf',
        'GET http://localhost:5678/rest/workflows',
        'windmill flow run test_workflow',
        'terraform plan -var-file="config.tfvars"',
        'curl -X POST localhost:1337/v1/chat/completions',
        'python test_agents.py',
        'curl -X POST localhost:5005/webhooks/rest/webhook',
        'gemini "Test query for Phoenix DemiGod"'
    ]
}

df = pd.DataFrame(config_data)
df.to_csv('phoenix_hackathon_config.csv', index=False)

print("Tabla de configuración técnica creada exitosamente")
print("\nPreview de la tabla:")
print(df.head())
print(f"\nTotal de componentes: {len(df)}")
print(f"Tiempo total estimado de setup: {df['Tiempo_Setup'].str.extract('(\d+)').astype(int).sum()[0]} minutos")