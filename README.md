# verticeaovivo

O projeto **verticeaovivo** foi gerado utilizando o template **default-python**.

- `src/`: Python source code for this project.
  - `src/verticeaovivo/`: Shared Python code that can be used by jobs and pipelines.
- `resources/`: Resource configurations (jobs, pipelines, etc.)
- `tests/`: Unit tests for the shared Python code.
- `fixtures/`: Fixtures for data sets (primarily used for testing).

## Sequencia de comandos para criação, configuração e inicialização do projeto

1. Realizar o login
   `$ databricks auth login --profile DEFAULT`

2. Listar todas as tabelas do catálogo
   `$ databricks experimental aitools tools query "SHOW TABLES IN lakehouse_vertice.bronze" --profile DEFAULT`

3. Listar os dados do profile
   `$ databricks auth describe --profile DEFAULT`

   Host: https://dbc-068fb8ed-9845.cloud.databricks.com

   User: rt.data.eng.analytics@gmail.com

   Authenticated with: databricks-cli

   Token storage: secure, OS keyring (service: databricks-cli) (from auth_storage in [__settings__] section of C:/Users/<user>/.databrickscfg)

---

**Current configuration:**

**✓ host:** https://dbc-068fb8ed-9845.cloud.databricks.com (from C:\Users\<user>/.databrickscfg config file)
**✓ account_id:** f06cd2b8-6224-4fe8-b608-367d9ebecb06 (from C:\Users\<user>/.databrickscfg config file)
**✓ workspace_id:** 7474645395795496 (from C:\Users\<user>/.databrickscfg config file)
**✓ profile:** DEFAULT (from --profile flag)
**✓ databricks_cli_path:** C:\Users\<user>\AppData\Local\Microsoft\WinGet\Packages\Databricks.DatabricksCLI_Microsoft.Winget.Source_8wekyb3d8bbwe\databricks.exe
**✓ auth_type:** databricks-cli (from C:\Users\<user>/.databrickscfg config file)
**✓ cloud:** AWS
**✓ audience:** https://dbc-068fb8ed-9845.cloud.databricks.com/oidc/v1/token
**✓ discovery_url:** https://dbc-068fb8ed-9845.cloud.databricks.com/oidc/.well-known/oauth-authorization-server

4. Inicializar o DATABRICKS no repositório (com padrão python)
   `$ databricks bundle init default-python`

**Importante:**

    a. Apagar o conteúdo das pastas: resources/, src/ e tests/
    b. Alterar o nome da pasta my_project para o nome real do projeto nos arquivos: databricks.yml e pyproject.toml

5. Listar todos os JOBs do catalogo
   `$ databricks jobs list --profile DEFAULT`

**Resposta:**
`<id_job>  Ingestão`

6. Com o código(s) do(s) JOB(s), gerar uma cópia os arquivos contidos no catalogo do projeto para a pasta src/ e na pasta recources/
   `$ databricks bundle generate job --existing-job-id <id_job> --profile DEFAULT`

7. Instalar as skills do DATABRICKS
   `$ databricks aitools install --agents claude-code --scope project --skills-only --experimental`

8. Seleciona a versão do python para criação do ambiente virtual
   `$ uv python pin 3.12.10`

**Importante:** Somente a versão 3.12 aceita

9. Cria o ambiente virtual
   `$ uv venv [--seed]`

**Importante:** O parâmetro [--seed] instala o pip no ambiente virtual

10. Instala todas as bibliotecas básicas para o projeto
    `$ uv sync`

11. Rodar o script python para esconder dados sensíveis (senhas, parâmetros e etc)
    `$ python extrair_chaves_s3.py`

## Árvore do ProjetoControlTowerAoVivo / verticeaovivo

```
├── 📁 .claude
├── 📁 docs
│   ├── 📁 aula-01-ingestao-manual
│   │   ├── 📁 json
│   │   │   ├── ⚙️ dashboard-bronze.lvdash.json
│   │   │   └── ⚙️ genie-bronze.json
│   │   ├── 📁 notebooks
│   │   │   ├── 📁 em-branco
│   │   │   │   ├── 📄 exemplo-00-time-travel.sql
│   │   │   │   ├── 📄 exemplo-01-a-05-sql-na-bronze.sql
│   │   │   │   ├── 📄 exemplo-06-quanto-custa-o-atraso.sql
│   │   │   │   └── 📄 exemplo-07-ler-pdf.sql
│   │   │   └── 📁 resolvidos
│   │   │       ├── 📄 exemplo-00-time-travel.sql
│   │   │       ├── 📄 exemplo-01-a-05-sql-na-bronze.sql
│   │   │       ├── 📄 exemplo-06-quanto-custa-o-atraso.sql
│   │   │       └── 📄 exemplo-07-ler-pdf.sql
│   │   ├── 📁 python
│   │   │   ├── 🐍 00-carregar-dados.py
│   │   │   └── 🐍 gerar_dashboard.py
│   │   ├── 📁 sql
│   │   │   ├── 📄 00-setup-catalogo.sql
│   │   │   ├── 📄 01-ingestao-bronze.sql
│   │   │   ├── 📄 99-verificacao.sql
│   │   │   ├── 📄 dashboard-dataset-custos.sql
│   │   │   ├── 📄 dashboard-dataset-projetos.sql
│   │   │   ├── 📄 exemplo-00-time-travel.sql
│   │   │   ├── 📄 exemplo-01-a-05-sql-na-bronze.sql
│   │   │   ├── 📄 exemplo-06-quanto-custa-o-atraso.sql
│   │   │   ├── 📄 exemplo-07-ler-pdf.sql
│   │   │   └── 📝 roteiro-execucao-scripts-sql.md
│   │   ├── 📁 validacao-execucao
│   │   │   └── 🖼️ resultados.png
│   │   ├── 📝 README.md
│   │   ├── 📝 passo-a-passo-dashboard-e-genie.md
│   │   └── 📝 roteiro-genie-e-dashboard.md
│   ├── 📁 aula-02-python-engenheiro
│   │   ├── 🐍 00_aquecimento_python.py
│   │   ├── 🐍 00_aquecimento_python_gabarito.py
│   │   ├── 🐍 01_ingestao_api.py
│   │   ├── 🐍 01_ingestao_api_gabarito.py
│   │   ├── 🐍 02_ingestao_boto3.py
│   │   ├── 🐍 02_ingestao_boto3_gabarito.py
│   │   └── 📝 README.md
│   ├── 📁 aula-03-modelagem-claude-code
│   │   ├── 📁 claude-code
│   │   │   ├── 📁 meu-vertice
│   │   │   │   └── 📝 README.md
│   │   │   ├── 📁 prd
│   │   │   │   ├── 📄 00-reset.sh
│   │   │   │   ├── 📄 99-verificacao.sql
│   │   │   │   ├── 📝 CLAUDE.md
│   │   │   │   ├── 📝 bundle-na-mao.md
│   │   │   │   ├── 📝 prompt-01-silver.md
│   │   │   │   ├── 📝 prompt-02-gold.md
│   │   │   │   ├── 📝 prompt-03-job-completo.md
│   │   │   │   └── 📝 prompt-04-dashboard.md
│   │   │   ├── 📁 vertice
│   │   │   │   ├── 📁 resources
│   │   │   │   │   ├── ⚙️ dashboard-portfolio.lvdash.json
│   │   │   │   │   ├── ⚙️ dashboard.dashboard.yml
│   │   │   │   │   ├── ⚙️ farol.geniespace.json
│   │   │   │   │   ├── ⚙️ genie.genie_space.yml
│   │   │   │   │   ├── ⚙️ vertice.job.yml
│   │   │   │   │   └── ⚙️ vertice_medalhao.pipeline.yml
│   │   │   │   ├── 📁 src
│   │   │   │   │   ├── 📁 conferencia
│   │   │   │   │   │   └── 📄 00-conferencia-bronze.sql
│   │   │   │   │   ├── 📁 gold
│   │   │   │   │   │   ├── 📄 01-fato-projeto-semana.sql
│   │   │   │   │   │   └── 📄 02-situacao-e-pessoas.sql
│   │   │   │   │   ├── 📁 ia
│   │   │   │   │   │   └── 📄 status_estruturado.sql
│   │   │   │   │   ├── 📁 ingestao
│   │   │   │   │   │   ├── 🐍 01_ingestao_api.py
│   │   │   │   │   │   └── 🐍 02_ingestao_boto3.py
│   │   │   │   │   ├── 📁 metricas
│   │   │   │   │   │   └── 📄 metricas.sql
│   │   │   │   │   ├── 📁 ml
│   │   │   │   │   │   ├── 📄 01-features.sql
│   │   │   │   │   │   ├── 🐍 02-modelo.py
│   │   │   │   │   │   └── 🐍 03-score.py
│   │   │   │   │   ├── 📁 silver
│   │   │   │   │   │   ├── 📄 01-projetos.sql
│   │   │   │   │   │   ├── 📄 02-tarefas.sql
│   │   │   │   │   │   ├── 📄 03-status-e-custos.sql
│   │   │   │   │   │   ├── 📄 04-pessoas.sql
│   │   │   │   │   │   └── 📄 05-fornecedores.sql
│   │   │   │   │   └── 📁 testes
│   │   │   │   │       └── 📄 testes.sql
│   │   │   │   └── ⚙️ databricks.yml
│   │   │   ├── 📝 APRENDIZADOS.md
│   │   │   └── 📝 README.md
│   │   └── 📝 README.md
│   ├── 📁 aula-04-produtos-de-dados-ia
│   │   ├── 📁 bonus
│   │   │   ├── 📁 agente
│   │   │   │   ├── 📄 01-contratos.sql
│   │   │   │   ├── ⚙️ contratos.job.yml
│   │   │   │   ├── ⚙️ diretoria-contratos-genie.json
│   │   │   │   └── 🐍 gerar_genie.py
│   │   │   ├── 📁 meu-agente
│   │   │   │   └── 📝 README.md
│   │   │   ├── 📄 99-verificacao-contratos.sql
│   │   │   ├── 📝 CLAUDE.md
│   │   │   ├── 📝 README.md
│   │   │   ├── ⚙️ genie-benchmark-contratos.json
│   │   │   └── 📝 prompt-agente-de-contratos.md
│   │   ├── 📁 minha-torre
│   │   │   └── 📝 README.md
│   │   ├── 📁 notebooks
│   │   │   ├── 📄 01-o-que-o-modelo-vale.sql
│   │   │   └── 🐍 02-o-vazamento-de-dado.py
│   │   ├── 📁 prd
│   │   │   ├── 📄 99-limpar-aula-04.sh
│   │   │   ├── 📄 99-limpar-modelo.sh
│   │   │   ├── 📝 CLAUDE.md
│   │   │   ├── ⚙️ genie-benchmark-diretoria.json
│   │   │   ├── 📝 prompt-01-modelo.md
│   │   │   ├── 📝 prompt-02-genie.md
│   │   │   ├── 📝 prompt-03-app.md
│   │   │   └── 📝 prompt-04-aprovacao-lakebase.md
│   │   ├── 📁 torre-app
│   │   │   ├── 📁 client
│   │   │   │   ├── 📁 public
│   │   │   │   │   ├── 🖼️ apple-touch-icon.png
│   │   │   │   │   ├── 🖼️ favicon-16x16.png
│   │   │   │   │   ├── 🖼️ favicon-192x192.png
│   │   │   │   │   ├── 🖼️ favicon-32x32.png
│   │   │   │   │   ├── 🖼️ favicon-48x48.png
│   │   │   │   │   ├── 🖼️ favicon-512x512.png
│   │   │   │   │   ├── 🖼️ favicon.svg
│   │   │   │   │   └── 📄 site.webmanifest
│   │   │   │   ├── 📁 src
│   │   │   │   │   ├── 📁 pages
│   │   │   │   │   │   ├── 📁 decisoes
│   │   │   │   │   │   │   └── 📄 DecisoesPage.tsx
│   │   │   │   │   │   ├── 📁 genie
│   │   │   │   │   │   │   └── 📄 GeniePage.tsx
│   │   │   │   │   │   ├── 📁 projetos
│   │   │   │   │   │   │   └── 📄 ProjetosPage.tsx
│   │   │   │   │   │   └── 📁 simulador
│   │   │   │   │   │       └── 📄 SimuladorPage.tsx
│   │   │   │   │   ├── 📄 App.tsx
│   │   │   │   │   ├── 📄 ErrorBoundary.tsx
│   │   │   │   │   ├── 🎨 index.css
│   │   │   │   │   ├── 📄 main.tsx
│   │   │   │   │   └── 📄 vite-env.d.ts
│   │   │   │   ├── ⚙️ components.json
│   │   │   │   ├── 🌐 index.html
│   │   │   │   ├── 📄 postcss.config.js
│   │   │   │   ├── 📄 tailwind.config.ts
│   │   │   │   └── 📄 vite.config.ts
│   │   │   ├── 📁 config
│   │   │   │   ├── 📁 metric-views
│   │   │   │   │   ├── ⚙️ definitions.json
│   │   │   │   │   └── ⚙️ metadata.generated.json
│   │   │   │   └── 📁 queries
│   │   │   │       ├── 📄 kpis.sql
│   │   │   │       ├── 📄 pessoas_ociosas.sql
│   │   │   │       └── 📄 projetos_risco.sql
│   │   │   ├── 📁 server
│   │   │   │   ├── 📁 routes
│   │   │   │   │   ├── 📄 decisoes.ts
│   │   │   │   │   └── 📄 score.ts
│   │   │   │   ├── 📄 decisoes.test.ts
│   │   │   │   └── 📄 server.ts
│   │   │   ├── 📁 shared
│   │   │   │   └── 📁 appkit-types
│   │   │   │       ├── 📄 analytics.d.ts
│   │   │   │       ├── 📄 database.d.ts
│   │   │   │       └── 📄 metric-views.d.ts
│   │   │   ├── ⚙️ .gitignore
│   │   │   ├── ⚙️ .prettierignore
│   │   │   ├── ⚙️ .prettierrc.json
│   │   │   ├── 📝 CLAUDE.md
│   │   │   ├── 📝 README.md
│   │   │   ├── ⚙️ app.yaml
│   │   │   ├── ⚙️ appkit.plugins.json
│   │   │   ├── ⚙️ databricks.yml
│   │   │   ├── 📄 eslint.config.js
│   │   │   ├── ⚙️ package-lock.json
│   │   │   ├── ⚙️ package.json
│   │   │   ├── ⚙️ tsconfig.client.json
│   │   │   ├── ⚙️ tsconfig.json
│   │   │   ├── ⚙️ tsconfig.server.json
│   │   │   ├── ⚙️ tsconfig.shared.json
│   │   │   ├── 📄 tsdown.server.config.ts
│   │   │   └── 📄 vitest.config.ts
│   │   ├── 📄 99-verificacao.sql
│   │   ├── 📝 APRENDIZADOS.md
│   │   ├── 📝 README.md
│   │   └── 📝 pitch.md
│   └── 📁 interacoes-gemini
│       ├── 📝 2026-10-23-sessao-databricks-cli.md
│       └── 📝 2026-10-27-sessao-erro-databricks-bundle.md
├── 📁 img
│   ├── 📁 logos
│   │   ├── 🖼️ clickup.svg
│   │   ├── 🖼️ excel.svg
│   │   └── 🖼️ msproject.svg
│   ├── 📝 PRINTS.md
│   ├── 🖼️ agora-gold.jpg
│   ├── 🖼️ agora-silver-tarefas.jpg
│   ├── 🖼️ capa-thumb-youtube.png
│   ├── 🖼️ erros-databricks-bash.png
│   ├── 🖼️ logo-jornada-horizontal-branco.png
│   ├── 🖼️ noite1-catalogo-bronze.jpg
│   ├── 🖼️ noite1-dashboard-graficos.jpg
│   ├── 🖼️ noite1-dashboard.jpg
│   ├── 🖼️ noite1-genie-erra.jpg
│   ├── 🖼️ noite1-volume-excel.jpg
│   ├── 🖼️ noite2-bloqueios-ia.jpg
│   ├── 🖼️ noite2-capacidade.jpg
│   ├── 🖼️ noite2-dashboard-graficos.jpg
│   ├── 🖼️ noite2-dashboard.jpg
│   ├── 🖼️ noite2-fornecedores.jpg
│   ├── 🖼️ noite2-genie-recomendacao.jpg
│   ├── 🖼️ noite2-genie.jpg
│   ├── 🖼️ noite2-gold-v2.jpg
│   ├── 🖼️ noite2-job-v2.jpg
│   ├── 🖼️ noite2-job.jpg
│   ├── 🖼️ noite2-metric-view.jpg
│   ├── 🖼️ noite2-pessoas.jpg
│   ├── 🖼️ noite2-pipeline-v2.jpg
│   ├── 🖼️ noite2-pipeline.jpg
│   ├── 🖼️ noite3-dashboard-graficos.jpg
│   ├── 🖼️ noite3-dashboard.jpg
│   ├── 🖼️ noite3-job-completo.jpg
│   ├── 🖼️ noite3-job-passo1.jpg
│   ├── 🖼️ noite3-job-timeline.jpg
│   ├── 🖼️ noite3-mlflow.jpg
│   ├── 🖼️ noite3-modelo-ml.jpg
│   ├── 🖼️ noite3-modelo.jpg
│   ├── 🖼️ noite3-pipeline-tabelas.jpg
│   ├── 🖼️ noite3-score-v2.jpg
│   ├── 🖼️ noite3-score.jpg
│   ├── 🖼️ noite4-app-decisoes.jpg
│   ├── 🖼️ noite4-app-perguntar.jpg
│   ├── 🖼️ noite4-app-projetos.jpg
│   ├── 🖼️ noite4-app-simulador.jpg
│   ├── 🖼️ noite4-contratos-tipado.jpg
│   ├── 🖼️ noite4-contratos.jpg
│   ├── 🖼️ noite4-genie-contratos.jpg
│   ├── 🖼️ ontem-clickup-json.jpg
│   ├── 🖼️ ontem-excel-sujo.jpg
│   ├── 🖼️ ontem-msproject-xml.jpg
│   ├── 🖼️ recurso-app-authorize.jpg
│   ├── 🖼️ recurso-catalogo.jpg
│   ├── 🖼️ recurso-compute-lakebase.jpg
│   ├── 🖼️ recurso-genie-instrucoes.jpg
│   ├── 🖼️ recurso-genie-perguntas.jpg
│   ├── 🖼️ recurso-ingestao-conectores.jpg
│   ├── 🖼️ recurso-jobs-pipelines.jpg
│   ├── 🖼️ recurso-lakebase-projeto.jpg
│   ├── 🖼️ recurso-lakebase-tabela.jpg
│   ├── 🖼️ recurso-lineage-grafo.jpg
│   ├── 🖼️ recurso-lineage-lista.jpg
│   ├── 🖼️ recurso-metric-view.jpg
│   ├── 🖼️ recurso-notebook.jpg
│   ├── 🖼️ recurso-query-history.jpg
│   ├── 🖼️ recurso-serverless.jpg
│   ├── 🖼️ recurso-sql-editor.jpg
│   ├── 🖼️ recurso-sql-warehouse.jpg
│   ├── 🖼️ recurso-workspace-bundle.jpg
│   ├── 🖼️ slide-n3-dag.jpg
│   ├── 🖼️ slide-n3-dashboard.jpg
│   ├── 🖼️ slide-n3-gold.jpg
│   ├── 🖼️ slide-n3-passo1.jpg
│   ├── 🖼️ slide-n3-silver.jpg
│   └── 🖼️ slide-n3-timeline.jpg
├── 📁 verticeaovivo
│   ├── 📁 .claude
│   ├── 📁 fixtures
│   ├── 📁 resources
│   │   └── ⚙️ ingestão.job.yml
│   ├── 📁 src
│   │   ├── 📁 verticeaovivo
│   │   │   ├── 🐍 __init__.py
│   │   │   └── 🐍 main.py
│   │   ├── 🐍 01_ingestao_api.py
│   │   └── 🐍 02_ingestao_boto3_gabarito.py
│   ├── 📁 tests
│   ├── 📝 AGENTS.md
│   ├── ⚙️ databricks.yml
│   ├── 🐍 extrair_chaves_s3.py
│   ├── ⚙️ pyproject.toml
│   └── 📄 uv.lock
├── ⚙️ .gitattributes
├── ⚙️ .gitignore
├── 📝 README.md
└── 📄 commits_iniciais.sh
```

## Getting started

Choose how you want to work on this project:

(a) Directly in your Databricks workspace, see
https://docs.databricks.com/dev-tools/bundles/workspace.

(b) Locally with an IDE like Cursor or VS Code, see
https://docs.databricks.com/dev-tools/vscode-ext.html.

(c) With command line tools, see https://docs.databricks.com/dev-tools/cli/databricks-cli.html

If you're developing with an IDE, dependencies for this project should be installed using uv:

- Make sure you have the UV package manager installed.
  It's an alternative to tools like pip: https://docs.astral.sh/uv/getting-started/installation/.
- Run `uv sync --dev` to install the project's dependencies.

# Using this project using the CLI

The Databricks workspace and IDE extensions provide a graphical interface for working
with this project. It's also possible to interact with it directly using the CLI:

1. Authenticate to your Databricks workspace, if you have not done so already:

```

$ databricks configure

```

2. To deploy a development copy of this project, type:

```

$ databricks bundle deploy --target dev

```

(Note that "dev" is the default target, so the `--target` parameter
is optional here.)

This deploys everything that's defined for this project.
For example, the default template would deploy a pipeline called
`[dev yourname] verticeaovivo_etl` to your workspace.
You can find that resource by opening your workpace and clicking on **Jobs & Pipelines**.

3. Similarly, to deploy a production copy, type:

```

$ databricks bundle deploy --target prod

```

Note the default template has a includes a job that runs the pipeline every day
(defined in resources/sample_job.job.yml). The schedule
is paused when deploying in development mode (see
https://docs.databricks.com/dev-tools/bundles/deployment-modes.html).

4. To run a job or pipeline, use the "run" command:

```

$ databricks bundle run

```

5. Finally, to run tests locally, use `pytest`:

```

$ uv run pytest

```

```

```
