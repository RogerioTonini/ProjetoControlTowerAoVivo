-- silver.colaboradores: as 520 pessoas, sem as duplicadas.
CREATE OR REFRESH MATERIALIZED VIEW colaboradores
COMMENT 'Cadastro das 520 pessoas da Vértice (uma por colaborador_id): nome, papel, senioridade, custo por hora, admissão e desligamento.'
AS
WITH numerado AS (
  SELECT
    *,
    -- sujeira 16: COL0102, COL0257 e COL0433 aparecem duas vezes; fica o cadastro com papel em minúsculas
    row_number() OVER (
      PARTITION BY colaborador_id
      ORDER BY CASE WHEN papel = lower(papel) THEN 0 ELSE 1 END
    ) AS n
  FROM lakehouse_vertice.bronze.colaboradores
)
SELECT
  colaborador_id,
  nome,
  papel,
  senioridade,
  CAST(custo_hora AS DECIMAL(10, 2)) AS custo_hora,
  to_date(data_admissao) AS data_admissao,
  to_date(nullif(trim(data_desligamento), '')) AS data_desligamento
FROM numerado
WHERE n = 1;

-- silver.apontamentos: o timesheet semanal.
CREATE OR REFRESH MATERIALIZED VIEW apontamentos
COMMENT 'Timesheet semanal (uma linha por pessoa, projeto e semana): horas disponíveis e horas apontadas. semana é a sexta-feira (semana_inicio + 4), a mesma data do status semanal.'
AS SELECT
  colaborador_id,
  projeto_id,
  to_date(semana_inicio) AS semana_inicio,
  date_add(to_date(semana_inicio), 4) AS semana,
  CAST(horas_disponiveis AS DOUBLE) AS horas_disponiveis,
  CAST(horas_apontadas AS DOUBLE) AS horas_apontadas
FROM lakehouse_vertice.bronze.apontamentos;
