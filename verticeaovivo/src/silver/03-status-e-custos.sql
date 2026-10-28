-- silver.status_semanal: o status que o gerente escreve toda sexta. É o histórico do avanço.
CREATE OR REFRESH MATERIALIZED VIEW status_semanal (
  CONSTRAINT farol_valido EXPECT (farol IN ('verde', 'amarelo', 'vermelho')) ON VIOLATION FAIL UPDATE
)
COMMENT 'Status semanal de cada projeto (uma linha por projeto e sexta-feira): % concluído informado, farol do gerente (verde, amarelo, vermelho) e o texto livre com bloqueios. status_vazio marca o texto em branco, N/A ou "ver ata da reunião" (a linha é mantida).'
AS SELECT
  projeto_id,
  to_date(data_status) AS data_status,
  gerente,
  -- sujeira 17: 'Verde', 'VERDE'
  lower(trim(farol)) AS farol,
  CAST(pct_concluido AS INT) AS pct_concluido,
  texto_status,
  -- sujeira 18: status vazio NÃO é descartado, só sinalizado
  coalesce(trim(texto_status), '') IN ('', 'N/A', 'ver ata da reunião') AS status_vazio
FROM lakehouse_vertice.bronze.status_semanal;

-- silver.custos: os lançamentos de custo real.
CREATE OR REFRESH MATERIALIZED VIEW custos
COMMENT 'Lançamentos de custo real dos projetos (pessoal, consultoria, cloud, licenças, despesas), um por linha, em reais. Estornos ficam como valor negativo (o custo é líquido) e marcados em estorno. semana é a sexta-feira da semana do lançamento.'
AS
WITH tipado AS (
  SELECT
    lancamento_id,
    projeto_id,
    to_date(data) AS data,
    categoria,
    descricao,
    -- sujeira 13: vírgula decimal. replace ANTES do CAST; try_cast jogaria R$ 5,4 mi fora em silêncio
    CAST(replace(valor, ',', '.') AS DECIMAL(18, 2)) AS valor,
    centro_custo
  FROM lakehouse_vertice.bronze.custos
)
SELECT
  lancamento_id,
  projeto_id,
  data,
  date_add(CAST(date_trunc('WEEK', data) AS DATE), 4) AS semana,
  categoria,
  descricao,
  valor,
  -- sujeira 14: estorno fica, sinalizado
  valor < 0 AS estorno,
  centro_custo
FROM tipado;
