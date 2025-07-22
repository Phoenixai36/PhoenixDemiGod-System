ESTRUCTURA HIPERBÓLICA PHOENIX DEMIGOD v8.7
==================================================
phoenix-demigod-v8.7
├── README.md
├── .gitignore
├── .github
│   ├── workflows
│   │   ├── ci-cd.yml
│   │   ├── deploy.yml
│   │   └── test.yml
│   └── ISSUE_TEMPLATE
│       ├── bug_report.md
│       └── feature_request.md
├── config
│   ├── phoenix_env.sh
│   ├── jan_config.json
│   ├── windsurf_mcp.json
│   ├── optimal_config.yaml
│   ├── mcp_config.json
│   ├── windmill.toml
│   └── terraform.tfvars
├── scripts
│   ├── setup
│   │   ├── install_windsurf.sh
│   │   ├── setup_janai.sh
│   │   ├── install_ollama.sh
│   │   └── setup_mcp.sh
│   ├── automation
│   │   ├── phoenix_mcp_router.py
│   │   ├── model_optimizer.py
│   │   └── stack_validator.py
│   ├── deployment
│   │   ├── deploy_stack.sh
│   │   ├── backup_config.sh
│   │   └── restore_system.sh
│   └── validation
│       ├── validate_day1.sh
│       ├── validate_day2.sh
│       ├── validate_day3.sh
│       └── final_validation.sh
├── models
│   ├── local
│   │   ├── llama3.2
│   │   │   ├── modelfile
│   │   │   └── config.json
│   │   ├── qwen2.5-coder
│   │   │   ├── modelfile
│   │   │   └── config.json
│   │   └── deepseek-r1
│   │       ├── modelfile
│   │       └── config.json
│   └── mamba
│       ├── phoenix_mamba_optimizer.py
│       └── mamba_configs.yaml
├── workflows
│   ├── n8n
│   │   ├── phoenix_workflows.json
│   │   ├── map_e_integration.json
│   │   └── automation_flows.json
│   └── windmill
│       ├── phoenix_scripts.py
│       ├── automation_workflows.sql
│       └── job_definitions.yaml
├── infrastructure
│   ├── terraform
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── phoenix.tfvars
│   ├── docker
│   │   ├── docker-compose.yml
│   │   ├── Dockerfile.janai
│   │   └── Dockerfile.n8n
│   └── kubernetes
│       ├── namespace.yaml
│       ├── deployments
│       │   ├── janai-deployment.yaml
│       │   ├── n8n-deployment.yaml
│       │   └── windmill-deployment.yaml
│       └── services
│           ├── janai-service.yaml
│           └── n8n-service.yaml
├── agents
│   ├── omas
│   │   ├── omas_system.py
│   │   ├── technical_agent.py
│   │   ├── analysis_agent.py
│   │   ├── conversational_agent.py
│   │   └── orchestrator.py
│   ├── rasa-phoenix
│   │   ├── config.yml
│   │   ├── domain.yml
│   │   ├── data
│   │   │   ├── nlu.yml
│   │   │   ├── rules.yml
│   │   │   └── stories.yml
│   │   └── actions
│   │       └── actions.py
│   ├── ontology
│   │   ├── phoenix_ontology.py
│   │   ├── ontology.owl
│   │   └── reasoning_engine.py
│   └── map_e
│       ├── map_e_chatbot.py
│       ├── conversation_context.py
│       └── intent_classifier.py
├── docs
│   ├── installation.md
│   ├── api.md
│   ├── deployment.md
│   ├── user_guide.md
│   ├── developer_guide.md
│   └── architecture.md
├── tests
│   ├── unit
│   │   ├── test_agents.py
│   │   ├── test_mcp.py
│   │   └── test_workflows.py
│   ├── integration
│   │   ├── integration_tests.py
│   │   ├── performance_tests.py
│   │   └── load_tests.py
│   └── fixtures
│       ├── test_data.json
│       └── mock_responses.json
├── monitoring
│   ├── phoenix_monitoring.py
│   ├── health_check.py
│   ├── performance_optimizer.py
│   └── alerts_config.yaml
├── security
│   ├── security_audit.py
│   ├── encryption_utils.py
│   └── auth_config.yaml
├── backups
├── logs
├── financing
│   ├── cdti_neotec_2025.json
│   ├── enisa_emprendedoras_2025.json
│   └── business_plan_executive.md
└── demo
    ├── prepare_demo.py
    └── demo_scenarios.json
