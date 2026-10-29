# verticeaovivo

O projeto **verticeaovivo** foi gerado utilizando o template **default-python**.

- `src/`: Python source code for this project.
  - `src/verticeaovivo/`: Shared Python code that can be used by jobs and pipelines.
- `resources/`: Resource configurations (jobs, pipelines, etc.)
- `tests/`: Unit tests for the shared Python code.
- `fixtures/`: Fixtures for data sets (primarily used for testing).

## Sequencia de comandos para criação, configuração e inicialização do projeto

**1.** Realizar o login
`$ databricks auth login --profile DEFAULT`

**2.** Listar todas as tabelas do catálogo
`$ databricks experimental aitools tools query "SHOW TABLES IN lakehouse_vertice.bronze" --profile DEFAULT`

**3.** Listar os dados do profile
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

**4.** Inicializar o DATABRICKS no repositório (com padrão python)
`$ databricks bundle init default-python`

**Importante:**

    a. Apagar o conteúdo das pastas: resources/, src/ e tests/
    b. Alterar o nome da pasta my_project para o nome real do projeto nos arquivos: databricks.yml e pyproject.toml

**5.** Listar todos os JOBs do catalogo
`$ databricks jobs list --profile DEFAULT`

**Resposta:**
`<id_job>  Ingestão`

**6.** Com o código(s) do(s) JOB(s), gerar uma cópia os arquivos contidos no catalogo do projeto para a pasta src/ e na pasta recources/
`$ databricks bundle generate job --existing-job-id <id_job> --profile DEFAULT`

**7.** Instalar as skills do DATABRICKS
`$ databricks aitools install --agents claude-code --scope project --skills-only --experimental`

**8.** Seleciona a versão do python para criação do ambiente virtual
`$ uv python pin 3.12.10`

**Importante:** Somente a versão 3.12 aceita

**9.** Cria o ambiente virtual
`$ uv venv [--seed]`

**Importante:** O parâmetro [--seed] instala o pip no ambiente virtual

**10.** Instala todas as bibliotecas básicas para o projeto
`$ uv sync`

**11.** Rodar o script python para esconder dados sensíveis (senhas, parâmetros e etc)
`$ python extrair_chaves_s3.py`

**12.** Validação e deploy
`$ databricks bundle validate --profile DEFAULT`

**Resposta:**
Name: **verticeaovivo**
Target: **dev**
Workspace:
Host: **https://dbc-068fb8ed-9845.cloud.databricks.com**
User: **rt.data.eng.analytics@gmail.com**
Path: **/Workspace/Users/rt.data.eng.analytics@gmail.com/.bundle/verticeaovivo/dev**

`$ databricks bundle deploy   --profile DEFAULT`

## Árvore do ProjetoControlTowerAoVivo / verticeaovivo

```
├── 📁 .claude
├── 📁 .databricks
├── 📁 .git
│   └── 📁 hooks
│       └── 📄 commit-msg                                       # padrão dos commits
├── 📁 docs
│   ├── 📁 aula-01-ingestao-manual                              # aula 01 - Ingestão manual no Databricks
│   ├── 📁 aula-02-python-engenheiro                            # aula 02 - Ingestão de dados utilizando interface web DATABRICKS 
│   ├── 📁 aula-03-modelagem-claude-code                        # aula 03 - ingestão de dados utilizando Claude Code
│   ├── 📁 aula-04-produtos-de-dados-ia                         # aual 04 - Analisando os dados com IA
├── 📁 img                                                      # imagens dos recursos/produto final
├── 📁 verticeaovivo
│   ├── 📁 .claude
│   ├── 📁 .databricks
│   ├── 📁 .pytest_cache
│   ├── 📁 .ruff_cache
│   ├── 📁 .venv
│   ├── 📁 .vscode
│   ├── 📁 dist
│   ├── 📁 fixtures                                             # dados de entrada
│   ├── 📁 llm
│   │   ├── 📁 ocorrencias
│   │   │   └── 📝 prompt_01-ocorrencias.md
│   │   ├── 📁 prd
│   │   │   └── 📝 bundle-na-mao.md
│   │   ├── 📁 template
│   │   │   └── 📁 prd
│   │   │       └── 📝 CLAUDE.md
│   │   ├── 📝 prompt_01.md
│   │   ├── 📝 prompt_02.md
│   │   ├── 📝 prompt_03.md
│   │   └── 📝 prompt_04.md
│   ├── 📁 log
│   ├── 📁 resources
│   │   ├── ⚙️ dashboard-portfolio.lvdash.json
│   │   ├── ⚙️ dashboard.dashboard.yml
│   │   ├── ⚙️ vertice.job.yml
│   │   └── ⚙️ vertice_medalhao.pipeline.yml
│   ├── 📁 scripts
│   │   ├── 🐍 extrair_chaves_s3.py
│   │   ├── 🐍 gerar_dashboard.py
│   │   └── 🐍 run_sql.py
│   ├── 📁 src
│   │   ├── 📁 conferencia
│   │   │   └── 📄 00-conferencia-bronze.sql
│   │   ├── 📁 gold
│   │   │   ├── 📄 01-fato-projeto-semana.sql
│   │   │   └── 📄 02-situacao-e-pessoas.sql
│   │   ├── 📁 ia
│   │   │   └── 📄 status_estruturado.sql
│   │   ├── 📁 ingestao
│   │   │   ├── 🐍 01_ingestao_api.py
│   │   │   └── 🐍 02_ingestao_boto3_gabarito.py
│   │   ├── 📁 silver
│   │   │   ├── 📄 01-projetos.sql
│   │   │   ├── 📄 02-tarefas.sql
│   │   │   ├── 📄 03-status-e-custos.sql
│   │   │   ├── 📄 04-pessoas.sql
│   │   │   └── 📄 05-fornecedores.sql
│   │   ├── 📁 testes
│   │   │   └── 📄 testes.sql
│   │   └── 📁 verticeaovivo
│   │       ├── 🐍 __init__.py
│   │       └── 🐍 main.py
│   ├── 📁 tests
│   │   ├── 📁 log
│   │   ├── 🐍 __init__.py
│   │   ├── 🐍 apoio.py
│   │   ├── 🐍 conftest.py
│   │   ├── 🐍 test_extrair_chaves_s3.py
│   │   └── 🐍 test_run_sql.py
│   ├── 📁 tests
│   ├── 📝 AGENTS.md
│   ├── 📝 CLAUDE.md
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

---

## 5. Testes unitários

Os testes ficam em `verticeaovivo/tests/` e cobrem os scripts de apoio em
`verticeaovivo/src/verticeaovivo/main/scripts/`. Nenhum teste acessa o Databricks:
as chamadas ao `databricks` CLI, as esperas e as execuções de SQL são substituídas
por versões falsas (`monkeypatch`), e os arquivos são criados em pastas temporárias
(`tmp_path`), sem tocar no bundle real.

### Estrutura

```
verticeaovivo/tests/
├── __init__.py                  # torna tests um pacote (permite `from tests.apoio import ...`)
├── apoio.py                     # carregar_script(): carrega um script pelo caminho do arquivo
├── conftest.py                  # hooks do pytest que gravam os arquivos de log
├── test_extrair_chaves_s3.py    # testes de extrair_chaves_s3.py
├── test_run_sql.py              # testes de run_sql.py
└── log/                         # logs gerados a cada execução (fora do Git)
```

Os scripts são carregados pelo caminho do arquivo (`apoio.carregar_script`) porque
`src/verticeaovivo/main.py` tem o mesmo nome da pasta `src/verticeaovivo/main/`,
o que impede `import verticeaovivo.main.scripts`.

### O que é testado

| Arquivo a ser testado  | Testes                      | Cobertura                                                                                                                                                                                                                                                                                                                  |
| ---------------------- | --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `extrair_chaves_s3.py` | `test_extrair_chaves_s3.py` | troca das chaves por `${var.…}` no YAML do job; gravação do `variable-overrides.json` preservando variáveis existentes; erro claro quando falta a chave, quando falta o job e quando o script roda duas vezes (sem perder as chaves)                                                                                       |
| `run_sql.py`           | `test_run_sql.py`           | divisão do `.sql` em statements (`;` em string, comentário e bloco `$$`); chamada ao `databricks` CLI e tratamento de erro; escolha do warehouse padrão; envio e espera da statement; impressão do resultado; fluxo do `main` (`--warehouse`, `--quiet`, `--continuar`, parada na primeira falha, `--profile` obrigatório) |

### Como executar

Na pasta do bundle (`verticeaovivo`), com o `uv` usando o `.venv` do projeto
(o `pytest` está no grupo `dev` do `pyproject.toml`):

```powershell
cd verticeaovivo
uv run pytest tests                                      # todos os testes
uv run pytest tests -v                                   # lista cada teste pelo nome
uv run pytest tests/test_run_sql.py                      # um arquivo
uv run pytest tests/test_run_sql.py::test_main_tudo_ok   # um teste
uv run pytest tests -k dividir                           # testes com "dividir" no nome
uv run pytest tests -x                                   # para na primeira falha
```

Se aparecer o aviso de que `VIRTUAL_ENV` não corresponde ao `.venv` do projeto, há
outro ambiente virtual ativo no terminal: rode `deactivate` antes. No VS Code, os
testes também rodam pelo painel **Testing**, com o interpretador `verticeaovivo\.venv`.

### Arquivos de log

A cada execução, o `tests/conftest.py` grava **um arquivo de log por arquivo de teste**
em `tests/log/<arquivo de teste>.log` (por exemplo, `tests/log/test_run_sql.log`).
O arquivo é recriado a cada execução: guarda apenas o resultado da última.

Layout:

- **Primeira linha** (cabeçalho, obrigatória):
  `dd/mm/yyyy hh:mm:ss.ssss | Projeto: <nome do projeto> - Hostname: <nome do host>`
  O nome do projeto vem de `[project].name` do `pyproject.toml`, e o hostname do
  `socket.gethostname()`.
- **Demais linhas**, uma por teste:
  `dd/mm/yyyy hh:mm:ss.ssss | <o que foi executado> | SUCESSO ou ERRO`

O campo _o que foi executado_ é a primeira linha da docstring do teste (ou o nome da
função, se não houver docstring). Em testes parametrizados, o id do caso vem entre
colchetes, como `[bloco-dolar]`. Se uma fixture quebrar antes ou depois do teste, a
linha recebe `(setup)` ou `(teardown)` e o resultado `ERRO`.

Exemplo (`tests/log/test_extrair_chaves_s3.log`):

```
[28/10/2026 09:51:33.7121] | Projeto: verticeaovivo - Hostname: RT-WIN-SVR
[28/10/2026 09:51:33.7131] | extrair_chaves: troca as chaves do YAML por ${var.…} e devolve os valores | SUCESSO
[28/10/2026 09:51:33.7141] | extrair_chaves: YAML sem a chave gera ValueError dizendo qual faltou | SUCESSO
[28/10/2026 09:51:33.7161] | extrair_chaves: YAML já com ${var.…} é recusado | SUCESSO
```

Os logs ficam fora do Git (regras `*.log` e `[Ll]og/` do `.gitignore`).

Para incluir um teste novo no log, basta criar a função `test_...` em `tests/` com uma
docstring de uma linha descrevendo o que ela verifica: o hook grava a linha
automaticamente.


---

## 6. Configurar DBeaver (acesso remoto ao DATABRICKS)

Se for necessário acessar os dados que não seja pelo ambiente do DATABRICKS ou Claude, existe a possibilidade de configurar um CLI.
Um deles pode ser o **DBeaver**.

**Requisitos:** 
  **a-)** Você precisará do **ID Serverless Starter Warehouse**.
  **b-)** Geração do token.

**1.** Abra o DATABRICKS na web.

**2.** No menu lateral a esquerda clique em **Home**. 
Copie o endereço da URL até **.cloud.databricks.com/** para um bloco de notas.
**Exemplo:** https://<**abc-123de4fg-5678**>.cloud.databricks.com/,chamarei de **SEU_ID**

**3.** No menu lateral a esquerda clique em **SQL DataWarehoses**

![imagem-01](/img/manual/databricks-01.png)

**4.** Selecione a aba **SQL DataWarehoses** e clique em **Serverless Starter Warehouse**

![imagem-02](/img/manual/databricks-02.png)

**5.** Copie a informação do **ID Serverless Starter Warehouse** em um bloco de notas. Ele é composto de letras, números e o caractere hífen.
**Exemplo:** abc9d9999e99j9K

![imagem-03](/img/manual/databricks-03.png)

**6.** Para a geração do **token**, clique na sua foto/avatar (canto superior direito) → Settings

**7.** Vá em Developer → Access Tokens

**8.** Clique em **Generate New Token**

**9.** Dê um nome (ex.: DBeaver) e defina o prazo de validade (ou deixe sem expiração)
Clique Generate e copie o token imediatamente para o bloco de notas — ***ele é exibido só uma vez***
Ele será utilizado no endereço URL de conexão do Dbeaver.

**10.** No DBeaver, crie uma nova conexão (atalho: **Ctrl + Shift + N**) e selecione o DATABRICKS e clique em **Avançar**. 

![imagem-04](/img/manual/dbeaver-01.png)

Após a instalação automática do driver, será aberta a janela:

![imagem-05](/img/manual/dbeaver-02.png)

**11.** Configurações a serem realizadas:

**a-)** Conectar usando - **URL**
**b-)** URL JDBC - Eis a URL completa de conexão. Substitua os IDs.

`jdbc:databricks://<SEU_ID>.cloud.databricks.com:443/default;httpPath=/sql/1.0/warehouses/<ID_Serverless_Starter_Warehouse>;AuthMech=3;UID=token;PWD=<ID_TOKEN>`

**c-)** Nome de usuário - seu -mail de conexão com o DATABRICKS
**d-)** Senha
**e-)** clique em **Concluir**

**12.** Não ocorrendo nenhum erro de conexão será criada uma conexão ao lado esquerdo da tela. Clique no símbolo **>** ao lado esquerdo
da conexão e será listado todos os objetos que o banco de dados possui.

![imagem-06](/img/manual/dbeaver-03.png)