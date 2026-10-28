-- silver.tarefas: AS TRÊS FERRAMENTAS VIRAM UMA.
-- Cada ferramenta ganha uma visão temporária com as MESMAS 13 colunas, e a tabela final é o UNION ALL.
-- projeto_id, ferramenta, id_na_ferramenta, fase, tarefa, responsavel,
-- inicio_baseline, fim_baseline, inicio_real, fim_real, pct_como_veio, horas, status_na_ferramenta

-- Excel: 20 planilhas, tudo texto.
CREATE TEMPORARY VIEW tarefas_excel AS
SELECT
  -- de-para pelo nome do arquivo; se não casar (código vazio ou arquivo sem acento), o PRJ-xxx do nome
  coalesce(p.projeto_id, regexp_extract(e.arquivo, 'PRJ-[0-9]{3}', 0)) AS projeto_id,
  'excel' AS ferramenta,
  CAST(e.id AS STRING) AS id_na_ferramenta,
  e.fase,
  e.tarefa,
  e.responsavel,
  -- sujeira 4: data com '/' é dd/MM/yyyy; sem '/' é número de série do Excel
  CASE WHEN e.inicio_previsto LIKE '%/%' THEN to_date(e.inicio_previsto, 'dd/MM/yyyy')
       ELSE date_add(DATE'1899-12-30', CAST(nullif(trim(e.inicio_previsto), '') AS INT)) END AS inicio_baseline,
  CASE WHEN e.termino_previsto LIKE '%/%' THEN to_date(e.termino_previsto, 'dd/MM/yyyy')
       ELSE date_add(DATE'1899-12-30', CAST(nullif(trim(e.termino_previsto), '') AS INT)) END AS fim_baseline,
  CASE WHEN e.inicio_real LIKE '%/%' THEN to_date(e.inicio_real, 'dd/MM/yyyy')
       ELSE date_add(DATE'1899-12-30', CAST(nullif(trim(e.inicio_real), '') AS INT)) END AS inicio_real,
  CASE WHEN e.termino_real LIKE '%/%' THEN to_date(e.termino_real, 'dd/MM/yyyy')
       ELSE date_add(DATE'1899-12-30', CAST(nullif(trim(e.termino_real), '') AS INT)) END AS fim_real,
  -- sujeira 5: '45%' e '10,5%' (tira o % e troca a vírgula) ou fração 0.45 (× 100)
  CASE WHEN instr(e.pct_concluido, '%') > 0 THEN CAST(replace(replace(e.pct_concluido, '%', ''), ',', '.') AS DOUBLE)
       ELSE CAST(nullif(trim(e.pct_concluido), '') AS DOUBLE) * 100 END AS pct_como_veio,
  -- sujeira 7: horas '40h'
  CAST(replace(e.horas_previstas, 'h', '') AS DOUBLE) AS horas,
  CAST(NULL AS STRING) AS status_na_ferramenta
FROM lakehouse_vertice.bronze.excel_tarefas e
LEFT JOIN projetos p
  ON p.ferramenta = 'excel' AND p.codigo_ferramenta = e.arquivo
-- sujeira 6: a linha de TOTAL do fim da planilha não é tarefa
WHERE e.tarefa <> 'TOTAL';

-- ClickUp: 25 listas; datas em milissegundos, % e baseline dentro de custom_fields.
CREATE TEMPORARY VIEW tarefas_clickup AS
SELECT
  -- de-para pelo list_id; se o código faltar, pelo nome da lista
  coalesce(p_id.projeto_id, p_nome.projeto_id) AS projeto_id,
  'clickup' AS ferramenta,
  c.id AS id_na_ferramenta,
  filter(c.custom_fields, f -> f.name = 'Fase')[0].value AS fase,
  c.name AS tarefa,
  c.assignees[0].username AS responsavel,
  -- sujeira 8: datas em ms
  to_date(timestamp_millis(CAST(filter(c.custom_fields, f -> f.name = 'Início baseline')[0].value AS BIGINT))) AS inicio_baseline,
  to_date(timestamp_millis(CAST(filter(c.custom_fields, f -> f.name = 'Fim baseline')[0].value AS BIGINT))) AS fim_baseline,
  to_date(timestamp_millis(CAST(nullif(c.start_date, '') AS BIGINT))) AS inicio_real,
  to_date(timestamp_millis(CAST(nullif(c.date_done, '') AS BIGINT))) AS fim_real,
  CAST(filter(c.custom_fields, f -> f.name = 'Progresso (%)')[0].value AS DOUBLE) AS pct_como_veio,
  c.time_estimate / 3600000 AS horas,
  -- sujeira 9: status de 12 jeitos
  CASE
    WHEN lower(c.status.status) IN ('done', 'concluído', 'closed') THEN 'concluida'
    WHEN lower(c.status.status) IN ('to do', 'backlog', 'a fazer') THEN 'a_fazer'
    ELSE 'em_andamento'  -- in progress, em andamento, review, doing
  END AS status_na_ferramenta
FROM lakehouse_vertice.bronze.clickup_tarefas c
LEFT JOIN projetos p_id
  ON p_id.ferramenta = 'clickup' AND p_id.codigo_ferramenta = c.list_id
LEFT JOIN projetos p_nome
  ON p_nome.ferramenta = 'clickup' AND p_nome.codigo_ferramenta IS NULL AND p_nome.nome_projeto = c.list_name;

-- MS Project: 15 XML. A fase é a tarefa-resumo de nível 1 acima da tarefa.
CREATE TEMPORARY VIEW tarefas_msproject AS
WITH com_fase AS (
  -- sujeira 11: a janela roda em TODAS as linhas (inclusive as resumo) e só depois filtramos
  SELECT
    m.*,
    last_value(CASE WHEN m.OutlineLevel = 1 THEN m.Name END, true)
      OVER (PARTITION BY m.arquivo ORDER BY m.UID) AS fase
  FROM lakehouse_vertice.bronze.msproject_tarefas m
)
SELECT
  p.projeto_id,
  'msproject' AS ferramenta,
  CAST(t.UID AS STRING) AS id_na_ferramenta,
  t.fase,
  t.Name AS tarefa,
  CAST(NULL AS STRING) AS responsavel,
  to_date(t.Baseline.Start) AS inicio_baseline,
  to_date(t.Baseline.Finish) AS fim_baseline,
  to_date(t.ActualStart) AS inicio_real,
  to_date(t.ActualFinish) AS fim_real,
  CAST(t.PercentComplete AS DOUBLE) AS pct_como_veio,
  -- sujeira 12: horas em 'PT40H0M0S'
  CAST(regexp_extract(t.Work, 'PT([0-9]+)H', 1) AS DOUBLE) AS horas,
  CAST(NULL AS STRING) AS status_na_ferramenta
FROM com_fase t
LEFT JOIN projetos p
  ON p.ferramenta = 'msproject' AND p.codigo_ferramenta = t.arquivo
-- sujeira 10: as tarefas-resumo somam as de baixo; contariam as horas duas vezes
WHERE t.Summary = 0;

CREATE OR REFRESH MATERIALIZED VIEW tarefas (
  CONSTRAINT achou_o_projeto EXPECT (projeto_id IS NOT NULL) ON VIOLATION FAIL UPDATE,
  CONSTRAINT pct_entre_0_e_100 EXPECT (pct_concluido BETWEEN 0 AND 100) ON VIOLATION FAIL UPDATE,
  CONSTRAINT horas_positivas EXPECT (horas > 0) ON VIOLATION FAIL UPDATE
)
COMMENT 'Todas as tarefas dos 60 projetos num modelo só, vindas das três ferramentas (Excel, ClickUp e MS Project). Uma linha por tarefa (tarefa_id = projeto-ferramenta-id), com datas baseline e reais, % concluído (limitado a 100, com flag quando veio acima) e horas previstas. É a fotografia de hoje do avanço.'
AS
WITH todas AS (
  SELECT * FROM tarefas_excel
  UNION ALL SELECT * FROM tarefas_clickup
  UNION ALL SELECT * FROM tarefas_msproject
)
SELECT
  concat_ws('-', projeto_id, ferramenta, id_na_ferramenta) AS tarefa_id,
  projeto_id,
  ferramenta,
  id_na_ferramenta,
  fase,
  tarefa,
  responsavel,
  inicio_baseline,
  fim_baseline,
  inicio_real,
  fim_real,
  pct_como_veio,
  least(pct_como_veio, 100) AS pct_concluido,
  pct_como_veio > 100 AS pct_veio_acima_de_100,
  horas,
  status_na_ferramenta
FROM todas;
