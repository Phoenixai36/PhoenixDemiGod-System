<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# Árbol de Directorios Propuesto

### Phoenix DemiGod v8.7 (arquitectura “no-transformer”) + Integraciones AutoGen \& Rasa

```
phoenix/
├── docker/
│   ├── compose.yml                 # Orquestación servicios (FastAPI, n8n, Windmill, DuckDB, …
│   └── env/                        # Variables por entorno (dev, stage, prod)
├── infra/
│   ├── terraform/                  # IaC para cloud híbrido
│   ├── ansible/                    # Playbooks provisión on-prem
│   └── kubernetes/                 # Helm charts (fase 3)
├── apps/
│   ├── api/                        # FastAPI monorrepo (router multimodel)
│   │   ├── main.py
│   │   ├── settings.py             # Pydantic-BaseSettings
│   │   ├── deps/                   # Depends comunes
│   │   ├── routes/
│   │   │   ├── health.py
│   │   │   ├── inference.py
│   │   │   └── admin.py
│   │   └── models/                 # Pydantic I/O schemas
│   ├── autogen/                    # Agentes AutoGen
│   │   ├── core/
│   │   │   ├── architect.py        # Agent(role="Architect")
│   │   │   ├── reviewer.py
│   │   │   ├── tester.py
│   │   │   └── doc_writer.py
│   │   ├── teams/
│   │   │   ├── dev_team.json       # Declarativo (GroupChat v0.4)
│   │   │   └── qa_team.json
│   │   └── tools/                  # Herramientas auxiliares (Git, HTTP, Shell)
│   ├── rasa/                       # Rasa project (on-prem NLU)
│   │   ├── data/
│   │   │   ├── nlu.yml
│   │   │   ├── rules.yml
│   │   │   └── stories.yml
│   │   ├── domain/
│   │   │   ├── base.yml
│   │   │   └── phoenix_slots.yml
│   │   ├── actions/                # Custom actions (Python SDK)
│   │   └── config.yml              # Pipelines con spaCy + DIET
│   ├── n8n/                        # Workflows low-code
│   │   └── projects/
│   │       ├── deploy_monitor.json
│   │       └── backup_stack.json
│   └── windmill/                   # Scripts TypeScript / Python
│       └── jobs/
│           ├── validate_hardware.wmill
│           └── nightly_backup.wmill
├── libs/
│   ├── common/                     # Utilidades compartidas (logging, tracing, auth)
│   ├── embeddings/                 # Módulo Keras -> vectores
│   └── cli/                        # Scripts gestión (Typer)
├── resources/
│   ├── prompts/                    # Plantillas LLM
│   └── diagrams/                   # Draw.io arquitectura
├── tests/
│   ├── unit/
│   └── integration/
├── scripts/
│   ├── deploymentquicktest.sh
│   └── PhoenixDemigodSystem.sh
├── docs/
│   ├── ADR/                        # Architectural Decision Records
│   └── roadmap.md
├── .env.example
├── pyproject.toml                  # Poetry monorepo (plugins)
├── Makefile                        # Comandos DX (“make dev”, “make qa”)
└── README.md
```


## Claves de la Estructura

| Carpeta | Propósito | Tools/Lógica ideal |
| :-- | :-- | :-- |
| **docker/** | Unifica despliegue local y CI (compose) | Compose v3, redes internas, volúmenes declarados |
| **infra/** | Evolución IaC -> multicloud | Terraform + Helm para fase 3 |
| **apps/api/** | Núcleo FastAPI multimodel | Router condicional, Pydantic v2, Uvicorn workers |
| **apps/autogen/** | Equipos multi-agente | Declaración JSON (AutoGen v0.4), roles, termination rules |
| **apps/rasa/** | NLU especializado Phoenix | Slots dominio-propio, reglas onboarding, fallback local |
| **apps/n8n/** | Orquestación visual | Workflows exportados JSON, nodos custom |
| **apps/windmill/** | Jobs programados | Scripts backup, validación hardware |
| **libs/** | Código común reutilizable | Namespace `phoenix_*`, publicado en Artifactory privado |
| **resources/prompts/** | Prompt-engineering versionado | Plantillas Jinja2, estrategia “few-shot” |
| **scripts/** | Utilidades bash | Validación, setup one-liner |

## Ciclo de Vida Propuesto

1. **Desarrollo local**
    - `make dev` levanta compose con hot-reload FastAPI y Rasa.
    - Agentes AutoGen usan llaves `.env` locales.
2. **CI** (GitHub Actions)
    - Workflows lint, pytest, build imágenes.
    - Publica containers en GHCR, paquetes Python en PyPI privado.
3. **CD**
    - `infra/terraform` aplica en cluster Proxmox + optional AWS.
    - Helm despliega servicios stateful (DuckDB, MinIO) y stateless.
4. **Fase 1-2 (0-5 meses)**
    - Mantener stack base, añadir AutoGen QA-team y Rasa DevOps assistant.
    - Métricas vía Prometheus exporter integrado.
5. **Fase 3-4 (5-12 meses)**
    - Escalar a micro-VMs Firecracker, implementar Knative autoscaling.
    - Dashboard Inversores (Superset) conectado a logs Phoenix.

## Buenas Prácticas Adoptadas

- **Monorepo Poetry**: versiones coherentes y `workspace.dependencies` simplificado.
- **Namespace único** (`phoenix_*`) evita colisiones y facilita importaciones [^1][^2].
- **Volúmenes “local-files”** para n8n / Windmill según patrón oficial [^3][^4].
- **Declaración autogen teams** → facilita pruebas en AutoGen Studio [^5][^6].
- **ADR en docs/**: decisiones rastreables (ej. “usar Rasa vs LLM router”).
- **Git hooks pre-commit**: Black, Ruff, detect-secrets.


## Próximos Pasos

1. Completar **rasa training data** para onboarding técnico (30 intents).
2. Integrar **Gemini CLI** como wrapper opcional en `libs/cli`.
3. Solicitar **CDTI Misiones IA 2025** (enero 2025) con dossier docs/roadmap.md.
4. Migrar **docker compose → Kubernetes** fase 3 (Helm charts ya esqueleto).

### Resumen No Técnico

El árbol anterior muestra **dónde vive cada pieza** del sistema: la API principal, los agentes AutoGen, el asistente conversacional Rasa y los flujos visuales n8n/Windmill. Todo convive en un único repositorio para facilitar cambios rápidos y asegurar que cada módulo comparte utilidades y despliegue. Los inversores verán un stack listo para escalar, con pruebas automatizadas, infra declarativa y una ruta de evolución clara hasta el mes 12.

<div style="text-align: center">⁂</div>

[^1]: https://github.com/zhanymkanov/fastapi-best-practices

[^2]: https://hexdocs.pm/phoenix/directory_structure.html

[^3]: https://innovationyourself.com/run-multiple-services-with-docker-compose/

[^4]: https://docs.n8n.io/hosting/installation/server-setups/docker-compose/

[^5]: https://microsoft.github.io/autogen/dev/user-guide/autogenstudio-user-guide/index.html

[^6]: https://www.youtube.com/watch?v=oum6EI7wohM

[^7]: https://www.semanticscholar.org/paper/a41e45c8efef4840d8844f50bacda1e8f027d195

[^8]: https://pubs.aip.org/aip/acp/article/808363

[^9]: https://www.semanticscholar.org/paper/ac54cbd18369be9b43a99c5054889fe5d5a2b475

[^10]: https://link.springer.com/10.1007/s41686-023-00077-5

[^11]: https://revistas.uminho.pt/index.php/ijispm/article/view/5932

[^12]: https://www.semanticscholar.org/paper/4eae6c75d62529588bc540dcf716c53d8c6cdb5f

[^13]: https://dx.plos.org/10.1371/journal.pone.0302988

[^14]: https://revistas.uminho.pt/index.php/ijispm/article/view/6449

[^15]: https://dev.to/pedromtavares/blazing-with-phoenix-project-structure-463l

[^16]: https://github.com/microsoft/autogen

[^17]: https://hexdocs.pm/ash/project-structure.html

[^18]: https://dev.to/mohammad222pr/structuring-a-fastapi-project-best-practices-53l6

[^19]: https://www.gettingstarted.ai/autogen-multi-agent-workflow-tutorial/

[^20]: https://www.linkedin.com/pulse/fastapi-project-structure-best-practices-manikandan-parasuraman-fx4pc

[^21]: https://browsee.io/blog/autogen-ai-agents-framework/

[^22]: https://dev.to/rushikeshpandit/mastering-phoenix-framework-part-2-5hkb

[^23]: https://www.youtube.com/watch?v=YpChDNB1R60

[^24]: https://newsletter.victordibia.com/p/a-friendly-introduction-to-the-autogen

[^25]: https://forum.devtalk.com/t/directory-structure-with-elixir-phoenix/145554

[^26]: https://stackoverflow.com/questions/70725345/python-directory-structure-for-a-package-featuring-a-fastapi

[^27]: https://microsoft.github.io/autogen/stable/index.html

[^28]: https://www.youtube.com/watch?v=pXHfhXmqr78

[^29]: https://www.nature.com/articles/s41597-022-01805-5

[^30]: https://ieeexplore.ieee.org/document/9308147/

[^31]: https://www.semanticscholar.org/paper/0e96cee237afe4f1df1c17154b2e32f7ee5134a1

[^32]: https://peerj.com/preprints/2791v1

[^33]: https://www.semanticscholar.org/paper/0af2b8335eb5c792c801142087cfdf04473fa989

[^34]: https://www.mdpi.com/2072-6694/15/8/2360

[^35]: https://www.semanticscholar.org/paper/900706b995f69cb71af6673cfca0beaf5199f14d

[^36]: http://www.airccse.org/journal/ijaia/papers/4413ijaia05.pdf

[^37]: https://www.youtube.com/watch?v=_ILisPyUEiQ

[^38]: https://n8n.io/workflows/2334-organise-your-local-file-directories-with-ai/

[^39]: https://open-windmill.org/en/

[^40]: https://forum.rasa.com/t/making-directory-a-valid-rasa-project/10169

[^41]: https://community.n8n.io/t/organize-workflows-using-folders-got-created/49089

[^42]: https://www.africawindmill.org/who-we-work-with

[^43]: https://rasa.com/docs/reference/api/command-line-interface/

[^44]: https://community.n8n.io/t/creating-a-folder-structure-for-workflows-got-created/46495

[^45]: https://movingwindmills.org

[^46]: https://github.com/RasaHQ/rasa/issues/10878

[^47]: https://docs.n8n.io/integrations/creating-nodes/build/reference/node-file-structure/

[^48]: https://www.globalwindsafety.org

[^49]: https://rasa.com/docs/reference/primitives/training-data-format

[^50]: https://www.reddit.com/r/n8n/comments/1il3odz/folder_view_for_n8n_sidebar_organize_your/

[^51]: https://www.windaid.org

[^52]: https://rasa.com/docs/reference/api/analytics-data-structure-reference/

[^53]: https://ieeexplore.ieee.org/document/10824424/

[^54]: https://link.springer.com/10.1007/s10664-024-10462-8

[^55]: https://bmcpregnancychildbirth.biomedcentral.com/articles/10.1186/s12884-020-03109-1

[^56]: https://www.iadisportal.org/digital-library/citizen-science-as-a-service-a-review-of-multi-project-citizen-science-platforms

[^57]: https://publications.ipma.world/conference/11th-ipma-research-conference-research-resonating-with-project-practices/articles/11rc202316/

[^58]: https://www.mdpi.com/1660-4601/16/18/3299

[^59]: https://www.mdpi.com/1660-4601/16/10/1767

[^60]: https://dl.acm.org/doi/10.1145/3696500.3696533

[^61]: https://dev.to/mukhilpadmanabhan/a-simple-guide-to-docker-compose-multi-container-applications-5e0g

[^62]: https://code.visualstudio.com/api/get-started/extension-anatomy

[^63]: https://www.educative.io/answers/how-to-efficiently-build-a-polyglot-development-team

[^64]: https://betterprogramming.pub/dockerizing-multiple-services-inside-a-single-container-96cdff286cef

[^65]: https://snyk.io/blog/modern-vs-code-extension-development-tutorial/

[^66]: https://30dayscoding.com/blog/designing-polyglot-persistence-architectures

[^67]: https://learn.microsoft.com/en-us/dotnet/architecture/microservices/multi-container-microservice-net-applications/multi-container-applications-docker-compose

[^68]: https://code.visualstudio.com/api/get-started/your-first-extension

[^69]: https://www.nan-labs.com/v4/blog/polyglot-database-architecture/

[^70]: https://docs.docker.com/build/building/multi-stage/

[^71]: https://code.visualstudio.com/api/extension-capabilities/overview

[^72]: https://developer.confluent.io/courses/microservices/polyglot-architecture/

[^73]: https://docs.docker.com/engine/containers/multi-service_container/

[^74]: https://snyk.io/blog/modern-vs-code-extension-development-basics/

[^75]: https://softwareengineering.stackexchange.com/questions/276655/how-to-organize-large-polyglot-projects

[^76]: https://stackoverflow.com/questions/68463928/what-is-the-best-way-to-structure-two-docker-containers-that-depend-on-common-co

[^77]: http://link.springer.com/10.1007/978-981-13-1867-2

[^78]: https://arxiv.org/abs/2402.16936

[^79]: https://arxiv.org/abs/2406.07209

[^80]: http://www.proceedings.com/065147-0070.html

[^81]: https://link.springer.com/10.1007/978-3-642-54230-5_6

[^82]: https://arxiv.org/abs/2407.01976

[^83]: https://www.semanticscholar.org/paper/fa2baf9f208fb07b83e6102e3483927c7e6423c8

[^84]: https://ieeexplore.ieee.org/document/10656400/

[^85]: https://ieeexplore.ieee.org/document/10940967/

[^86]: https://proceeding.researchsynergypress.com/index.php/icmrsi/article/view/818

[^87]: https://arxiv.org/html/2408.15247v1

[^88]: https://arxiv.org/html/2405.08037

[^89]: https://discuss.python.org/t/multiple-related-programs-one-pyproject-toml-or-multiple-projects/17427

[^90]: https://nx.dev/concepts/decisions/folder-structure

[^91]: https://www.projectpro.io/article/autogen-projects-and-examples/1129

[^92]: https://softwareengineering.stackexchange.com/questions/377695/what-is-a-proper-way-to-structure-a-python-project-consisting-of-smaller-package

[^93]: https://blog.kodezi.com/how-to-set-up-a-mono-repo-structure-a-step-by-step-guide/

[^94]: https://forum.rasa.com/t/how-to-work-on-multiple-rasa-and-rasa-x-projects-in-docker-container/41466

[^95]: https://www.reddit.com/r/learnpython/comments/15ht129/python_project_structure_modules_projects/

[^96]: https://www.reddit.com/r/expo/comments/1jn7ce0/whats_the_ideal_directory_structure_for_a/

[^97]: https://dev.to/jonathanpwheat/using-docker-with-rasa-for-development-1c3h

[^98]: https://dev.to/hubschrauber/developing-custom-nodes-for-n8n-with-docker-3poj

[^99]: https://www.projectpro.io/article/autogen/1139

[^100]: https://tweag.io/blog/2023-04-04-python-monorepo-1/

[^101]: https://turborepo.com/docs/crafting-your-repository/structuring-a-repository

[^102]: https://forum.rasa.com/t/running-rasa-with-docker-compose/50113

[^103]: https://thewebsiteengineer.com/blog/how-to-run-n8n-with-docker-compose-to-use-custom-npm-modules/

[^104]: https://revistas.uminho.pt/index.php/ijispm/article/view/3546

[^105]: https://link.springer.com/10.1007/s12652-021-03610-1

[^106]: https://pmc.ncbi.nlm.nih.gov/articles/PMC10195660/

[^107]: https://dl.acm.org/doi/pdf/10.1145/3589335.3651935

[^108]: https://downloads.hindawi.com/journals/mpe/2014/307498.pdf

[^109]: https://annals-csis.org/proceedings/2022/drp/pdf/163.pdf

[^110]: https://clinmedjournals.org/articles/jmdt/journal-of-musculoskeletal-disorders-and-treatment-jmdt-2-023.php?jid=jmdt

[^111]: https://arxiv.org/html/2407.07337v1

[^112]: https://arxiv.org/abs/2101.00328

[^113]: https://arxiv.org/ftp/arxiv/papers/1003/1003.4077.pdf

[^114]: https://arxiv.org/pdf/0906.1346.pdf

[^115]: https://fastapi.tiangolo.com/tutorial/bigger-applications/

[^116]: https://microsoft.github.io/autogen/0.2/docs/Getting-Started/

[^117]: https://www.reddit.com/r/elixir/comments/1gt43ba/getting_started_with_phoenix_framework_but_how/

[^118]: https://www.reddit.com/r/FastAPI/comments/11nu9sw/how_to_build_a_scalable_project_file_structure/

[^119]: http://portal.acm.org/citation.cfm?doid=38713.38743

[^120]: https://www.rfc-editor.org/info/rfc0775

[^121]: https://community.n8n.io/t/ability-to-create-folders-in-the-workflow-menu-merged/22419

[^122]: https://www.windmill.dev

[^123]: https://rasa.com/docs/studio/tutorial/

[^124]: https://community.n8n.io/t/arranging-workflows-in-folders-got-created/2197

[^125]: https://windmill-itn.eu

[^126]: https://www.semanticscholar.org/paper/674a09fb2bd0766154e3d6ca573d24db650106dd

[^127]: https://bmchealthservres.biomedcentral.com/articles/10.1186/s12913-021-06563-5

[^128]: https://ijai.iaescore.com/index.php/IJAI/article/download/22652/13799

[^129]: https://jurnal.narotama.ac.id/index.php/ijeeit/article/download/1208/843

[^130]: https://arxiv.org/pdf/1711.01758.pdf

[^131]: https://www.mdpi.com/2076-3417/12/13/6737/pdf?version=1656832602

[^132]: https://arxiv.org/html/2404.12074v1

[^133]: https://www.mdpi.com/2076-3417/12/12/5793/pdf?version=1654762735

[^134]: https://downloads.hindawi.com/journals/cin/2022/5325694.pdf

[^135]: https://arxiv.org/pdf/1911.02275.pdf

[^136]: http://arxiv.org/pdf/1805.08598.pdf

[^137]: https://arxiv.org/pdf/2111.01972.pdf

[^138]: https://dev.to/dusan100janovic/create-a-visual-studio-code-extension-1i7c

[^139]: https://github.com/kubernetes-sigs/kubebuilder/issues/2475

[^140]: https://docs.docker.com/build/building/multi-platform/

[^141]: https://www.youtube.com/watch?v=lxRAj1Gijic

[^142]: https://www.mdpi.com/2079-9292/12/4/1047/pdf?version=1676880017

[^143]: https://arxiv.org/pdf/2308.08155.pdf

[^144]: http://arxiv.org/pdf/2412.00431.pdf

[^145]: https://arxiv.org/abs/2406.01388

[^146]: https://arxiv.org/html/2503.22231v2

[^147]: https://arxiv.org/pdf/2111.06016.pdf

[^148]: https://arxiv.org/pdf/2211.08387.pdf

[^149]: https://arxiv.org/pdf/2405.03807.pdf

