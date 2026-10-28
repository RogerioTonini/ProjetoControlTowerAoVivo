-- silver.projetos: o cadastro do PMO. É o de-para da integração: diz em que ferramenta
-- cada projeto é controlado e com que código (nome do arquivo ou id da lista do ClickUp).
CREATE OR REFRESH MATERIALIZED VIEW projetos (
  CONSTRAINT data_inicio_valida EXPECT (data_inicio IS NOT NULL) ON VIOLATION FAIL UPDATE,
  CONSTRAINT ferramenta_conhecida EXPECT (ferramenta IN ('excel', 'clickup', 'msproject')) ON VIOLATION FAIL UPDATE
)
COMMENT 'Cadastro dos 60 projetos da Vértice (um por linha): cliente, segmento, contrato, orçamento, datas e a ferramenta onde o gerente controla o projeto (excel, clickup ou msproject) com o código nela. É o de-para que integra as três ferramentas em silver.tarefas.'
AS SELECT
  projeto_id,
  nome_projeto,
  cliente,
  segmento,
  tipo_projeto,
  -- sujeira 2: a ferramenta vem escrita de 8 jeitos (Excel, Planilha, Clickup, MS Project, Project...)
  CASE
    WHEN lower(ferramenta) LIKE '%excel%' OR lower(ferramenta) LIKE '%planilha%' THEN 'excel'
    WHEN lower(ferramenta) LIKE '%clickup%' THEN 'clickup'
    WHEN lower(ferramenta) LIKE '%project%' THEN 'msproject'
  END AS ferramenta,
  ferramenta AS ferramenta_como_veio,
  -- sujeira 3: código vazio vira NULL (a silver.tarefas tem um plano B para esses)
  nullif(trim(codigo_ferramenta), '') AS codigo_ferramenta,
  CAST(valor_contrato AS DECIMAL(18, 2)) AS valor_contrato,
  CAST(orcamento_custo AS DECIMAL(18, 2)) AS orcamento_custo,
  -- sujeira 1: data em yyyy-MM-dd ou dd/MM/yyyy
  coalesce(try_to_date(data_inicio, 'yyyy-MM-dd'), try_to_date(data_inicio, 'dd/MM/yyyy')) AS data_inicio,
  coalesce(try_to_date(data_fim_baseline, 'yyyy-MM-dd'), try_to_date(data_fim_baseline, 'dd/MM/yyyy')) AS data_fim_baseline,
  status,
  gerente_projeto
FROM lakehouse_vertice.bronze.projetos;
