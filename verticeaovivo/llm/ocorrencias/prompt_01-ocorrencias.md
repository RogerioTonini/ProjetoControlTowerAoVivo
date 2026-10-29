# Prompt 01 - Ocorrências da execução

Registro do que aconteceu ao executar o `llm/prompt_01.md` (arrumar o bundle, conferir a
bronze e montar a silver) no bundle `verticeaovivo`, em 28/10/2026, no workspace Free
Edition (`dbc-068fb8ed-9845`, perfil `DEFAULT`).

**Resultado final:** bundle arrumado, job `vertice_farol` com 4 tarefas, pipeline
`vertice_medalhao` com as 7 tabelas da silver e todos os números de teste do CLAUDE.md
batendo. No caminho, a conferência da bronze encontrou 2 planilhas faltando no data lake,
o que foi corrigido.

---

## 1. Linha do tempo

| # | Etapa | O que aconteceu |
|---|---|---|
| 1 | Planejamento | O prompt foi planejado em plan mode, com verificações só de leitura: bundle, job importado, jobs do workspace, warehouse e colunas da bronze. O plano foi aprovado. |
| 2 | Contexto | `llm/template/prd/CLAUDE.md` foi copiado para `CLAUDE.md` e `run_sql.py` para `scripts/`. No Windows, os comandos `cp`/`mkdir -p` foram trocados pelos equivalentes do PowerShell. |
| 3 | Bundle | `databricks.yml`, o job e o pipeline foram reescritos, e os notebooks foram movidos para `src/ingestao/`. |
| 4 | Conferência + silver | `src/conferencia/00-conferencia-bronze.sql` e os 5 arquivos de `src/silver/` foram criados. |
| 5 | `bundle validate` | OK. |
| 6 | `bundle deploy` | OK: `Deleted jobs.ingestão`, `Created pipelines.vertice_medalhao`, `Created jobs.vertice_farol` (job id 543315582517787). |
| 7 | Job antigo "Ingestão" | O job 423300096334656 não tem schedule nem trigger, então não havia o que pausar. Ele não foi apagado. |
| 8 | 1º run (`conferencia_bronze,medalhao`) | **FALHOU** em `conferencia_bronze` (~7 s). O `medalhao` foi SKIPPED. |
| 9 | Investigação | Faltavam 2 planilhas Excel no bucket do data lake (ver seção 3). |
| 10 | Correção | As 2 planilhas foram geradas de novo e subidas com o nome sem acento (feito pelo usuário com `!`). |
| 11 | 2º run (`ingestao_data_lake,conferencia_bronze`) | SUCCESS (~3 min): as 9 tabelas batem. |
| 12 | 3º run (`medalhao`) | SUCCESS (~1,5 min): 7 tabelas, com todos os EXPECTs passando. |

## 2. O que foi construído

### `databricks.yml`
- `bundle.name` ficou `verticeaovivo`. O prompt fala em "bundle vertice", mas renomear
  mudaria a pasta de deploy e deixaria o estado já implantado órfão.
- O `mode: development` saiu do target `dev` (ele prefixava os nomes com `[dev usuario]`), e
  entrou `presets: { trigger_pause_status: PAUSED }`.
- Variáveis: `catalog` (default `lakehouse_vertice`) e `warehouse_id` (default
  `facd6d5689d35a9a`, o Serverless Starter Warehouse, descoberto com
  `databricks warehouses list`). As variáveis `catalog`/`schema` do template saíram.
  `s3_access_key_id` e `s3_secret_access_key` vieram do job para cá, só com `description`.
  O valor continua no `variable-overrides.json`, que não foi tocado.
- O target `prod` perdeu os overrides `catalog: workspace` / `schema: prod`.
- `fixtures/`, `tests/` e o artifact `.whl` do template continuam onde estavam.

### `resources/vertice.job.yml`, o job `vertice_farol`
O arquivo `resources/ingestão.job.yml` foi removido (`git rm`).

| Tarefa | Tipo | Depende de |
|---|---|---|
| `ingestao_feriados` | notebook `src/ingestao/01_ingestao_api.py` | — |
| `ingestao_data_lake` | notebook `src/ingestao/02_ingestao_boto3_gabarito.py` (chaves em `${var.…}`) | — |
| `conferencia_bronze` | sql_task `src/conferencia/00-conferencia-bronze.sql`, warehouse `${var.warehouse_id}` | as duas ingestões |
| `medalhao` | pipeline_task `${resources.pipelines.vertice_medalhao.id}` | `conferencia_bronze` |

- **Desvio do prompt:** o prompt pede `schedule.pause_status: PAUSED`, mas o job importado
  **não tinha bloco `schedule`**. Nenhum foi criado agora, porque o prompt 4 é que acrescenta
  o agendamento de segunda. O preset `PAUSED` do target `dev` já vai cobrir esse caso.
- Os notebooks foram movidos com `git mv`.

### `resources/vertice_medalhao.pipeline.yml`
`name: vertice_medalhao`, `catalog: ${var.catalog}`, `schema: silver`, `serverless: true`,
`photon: true` e `libraries` com o glob `../src/silver/**`.

### `src/conferencia/00-conferencia-bronze.sql`
Um SELECT com uma linha por tabela (`tabela | esperado | obtido | resultado`). Quando uma
contagem diverge, a coluna `resultado` chama `raise_error()` com a tabela e a indicação
"Olhe a saída da tarefa ingestao_data_lake". `bronze.feriados` fica de fora.

### Silver (`src/silver/`), 7 materialized views
| Arquivo | Tabelas | Destaques |
|---|---|---|
| `01-projetos.sql` | `projetos` | data em 2 formatos (`coalesce` de `try_to_date`); ferramenta por `LIKE` + `ferramenta_como_veio`; código vazio → NULL; EXPECTs `data_inicio_valida` e `ferramenta_conhecida` |
| `02-tarefas.sql` | `tarefas` | 3 temp views com as mesmas 13 colunas + `UNION ALL`; Excel com fallback `regexp_extract(arquivo,'PRJ-[0-9]{3}',0)`, datas texto/série, `%` em 3 formatos, sem `TOTAL`; ClickUp com ms → date, `filter(custom_fields…)`, fallback pelo nome da lista, status → 3 valores; MS Project com a janela `last_value` num CTE **antes** do `Summary = 0`; EXPECTs `achou_o_projeto`, `pct_entre_0_e_100`, `horas_positivas` |
| `03-status-e-custos.sql` | `status_semanal`, `custos` | farol `lower(trim())` com EXPECT; flag `status_vazio`; valor com `replace(',','.')` antes do CAST; estorno mantido e sinalizado; `semana` = sexta |
| `04-pessoas.sql` | `colaboradores`, `apontamentos` | duplicados resolvidos com `row_number`, preferindo o papel em minúsculas; `semana = semana_inicio + 4` |
| `05-fornecedores.sql` | `entregas_fornecedor` | CodeForge normalizada + `fornecedor_como_veio`; prazos, atraso, `em_aberto`, `em_atraso` com `DATE'2026-10-16'` |

Ajustes feitos antes do deploy, por causa do modo ANSI do SQL: o teste do `%` usa `instr(x, '%') > 0` em vez de
`LIKE '%\%%'`, e os CASTs de texto que pode vir vazio passam por `nullif(trim(x), '')`.
Nenhum `current_date()`.

## 3. A ocorrência principal: `bronze.excel_tarefas` com 1.500 linhas

### Sintoma
```
[USER_RAISED_EXCEPTION] bronze.excel_tarefas: esperado 1663 linhas, obtido 1500.
Olhe a saída da tarefa ingestao_data_lake. SQLSTATE: P0001
```
As outras 8 tabelas batiam. A conferência fez o que devia: parou o job antes de a silver
rodar com dado incompleto.

### Investigação
1. A bronze tinha **18 arquivos distintos e 18 linhas TOTAL**, mas são 20 planilhas.
2. Faltavam `PRJ-020 - Core bancário - módulo de cr v5 FINAL.xlsx` e
   `PRJ-021 - Integração omnichannel - Sup v5 FINAL.xlsx`. Os dois também não estavam no
   volume `bronze.raw/excel`.
3. A saída da última execução da ingestão (run 221475076305943) mostrou que o **próprio
   bucket** listava só 18 arquivos em `excel/` (73 no total), e todos foram baixados. Logo,
   o notebook não perdeu nada: os arquivos não estavam na fonte.
4. O diff contra o gabarito do curso mostrou só o nome do bucket (`datalake_Vertice` contra
   `DataLakeVertice`), porque o bucket é do próprio aluno no Supabase.

### Causa
As duas planilhas que faltavam são **as únicas com acento no nome**. O Supabase Storage não
aceita chave de objeto com caractere não ASCII, e elas ficaram de fora no upload do data
lake. O próprio prompt já previa esse caso ("o arquivo chegou sem acento: 'Core bancario' ×
'Core bancário'"), e por isso a silver tem o fallback pelo `PRJ-xxx` do nome do arquivo.

### Correção
1. O gerador do curso (`material/gerar_dataset.py` + `xlsx_simples.py`, seed 42) foi
   baixado para uma pasta temporária, com um `pdf_simples.py` de mentira para pular os PDFs.
   O Claude Code não pôde executar o gerador (a permissão de código externo foi negada), então o
   **usuário rodou com `!`**.
   Os comandos executados foram:
   
   ```powershell
   .venv\Scripts\python.exe -I "C:\Users\rtoni\AppData\Local\Temp\claude\D--Git-Projetos-ProjetoControlTowerAoVivo-verticeaovivo\cada488b-d8f8-4a76-994d-7c61d8e8d5ce\scratchpad\gerador\gerar_dataset.py" --saida "C:\Users\rtoni\AppData\Local\Temp\claude\D--Git-Projetos-ProjetoControlTowerAoVivo-verticeaovivo\cada488b-d8f8-4a76-994d-7c61d8e8d5ce\scratchpad\dados" --seed 42
   ```
  
  **Resultado:**

  ```text
  Dataset da Vértice Tecnologia gerado em C:\Users\rtoni\AppData\Local\Temp\claude\D--Git-Projetos-ProjetoControlTowerAoVivo-verticeaovivo\cada488b-d8f8-4a76-994d-7c61d8e8d5ce\scratchpad\dados/ (seed 42, hoje = 2026-10-16)
  projetos                    60
  tarefas                  4.917
  status_semanal           3.911
  custos                  23.640
  colaboradores              523
  apontamentos            30.883
  entregas_fornecedor        640
  pdf_contratos                8
  arquivos_excel              20
  arquivos_clickup            25
  arquivos_msproject          15
  ```

  ```powershell
  .venv\Scripts\python.exe "C:\Users\rtoni\AppData\Local\Temp\claude\D--Git-Projetos-ProjetoControlTowerAoVivo-verticeaovivo\cada488b-d8f8-4a76-994d-7c61d8e8d5ce\scratchpad\subir_excel_faltantes.py" "C:\Users\rtoni\AppData\Local\Temp\claude\D--Git-Projetos-ProjetoControlTowerAoVivo-verticeaovivo\cada488b-d8f8-4a76-994d-7c61d8e8d5ce\scratchpad\dados"
  ```

  **Resultado:**

  ```text
enviado excel/PRJ-020 - Core bancario - modulo de cr v5 FINAL.xlsx  (78 linhas, com o TOTAL)
enviado excel/PRJ-021 - Integracao omnichannel - Sup v5 FINAL.xlsx  (85 linhas, com o TOTAL)
total: 163 linhas (esperado 163 = 1663 - 1500)
  ```

2. Foi criado um script de upload (`subir_excel_faltantes.py`, fora do repositório). Ele lê as
   chaves do `variable-overrides.json` **só para leitura**, troca o acento por ASCII
   (`unicodedata` NFKD) e grava em `datalake_Vertice/excel/`. Como manuseia as chaves,
   **o usuário rodou com `!`**.
3. A primeira tentativa do upload falhou com `ModuleNotFoundError: boto3`: a `.venv` foi
   criada pelo `uv` e não tem `pip`. O `boto3` foi instalado com
   `uv pip install --python .venv\Scripts\python.exe boto3` (1.43.120). Efeito colateral:
   o `uv` rebaixou o `python-dateutil` da `.venv` de 3.0.0 para 2.9.0.post0. O script
   também passou a ler o JSON com `utf-8-sig`, para aceitar um eventual BOM.
4. Rodaram de novo `ingestao_data_lake,conferencia_bronze`, e `bronze.excel_tarefas` ficou
   com **1.663 linhas, 20 arquivos e 20 TOTAIS**.

## 4. Outras ocorrências menores

- **`run_sql.py` e BOM:** um `.sql` gravado com `Out-File -Encoding utf8` (PowerShell 5.1) sai
  com BOM, e o warehouse responde `PARSE_SYNTAX_ERROR at or near 'ï»¿'`. Regravar o mesmo
  arquivo manteve o BOM; um arquivo novo resolveu. No Windows, grave os `.sql` sem BOM.
- **`run_sql.py` e acentos:** a saída no console do Windows precisa de
  `$env:PYTHONIOENCODING='utf-8'`.
- **Nome do bucket fixo no notebook:** `02_ingestao_boto3_gabarito.py` usa
  `S3_BUCKET = "datalake_Vertice"` e ignora o parâmetro `AWS_BUCKET` que o job passa. Não foi
  alterado (é um ajuste opcional).
- **Runs em sequência:** antes de cada run, `databricks jobs list-runs --active-only`
  confirmou que não havia outro ativo, por causa do limite serverless do Free Edition.

## 5. Números conferidos (seed 42)

| O que | Esperado (CLAUDE.md) | Obtido |
|---|---|---|
| Tarefas na silver | 4.917 | 4.917 |
| · Excel | 1.643 (20 projetos) | 1.643 (20) |
| · ClickUp | 2.119 (25) | 2.119 (25) |
| · MS Project | 1.155 (15) | 1.155 (15) |
| Custo real total | R$ 193,35 mi | R$ 193,35 mi (331 estornos mantidos) |
| Entregas em atraso | 5, todas da CodeForge | 5, `CodeForge Consultoria Ltda` |
| Colaboradores | 520 | 520 |

## 6. Tabela final dos runs

| Tarefa | Tempo | Resultado |
|---|---|---|
| `conferencia_bronze` (1º run) | ~7 s | FAILED: `excel_tarefas` 1.500 ≠ 1.663; `medalhao` SKIPPED |
| `ingestao_data_lake` + `conferencia_bronze` | ~3 min | SUCCESS: as 9 tabelas da bronze batem |
| `medalhao` (`vertice_medalhao`) | ~1,5 min | SUCCESS: 7 MVs, todos os EXPECTs passaram |

## 7. Pendências

- Nada foi commitado ainda (branch `gera_pipeline`).
- Os 2 `.xlsx` sem acento estão no bucket porque foram subidos à mão. Se o data lake for
  recriado com os nomes acentuados, o problema volta.
- Opcional: o notebook passar a ler `AWS_BUCKET` em vez de fixar o nome no código.
- Próximo: prompt 2 (gold + `testes_de_qualidade`).
