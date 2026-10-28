-- gold.fato_projeto_semana: a evolução de cada projeto, semana a semana.
-- O % de cada sexta vem do status semanal (as ferramentas só guardam o % de hoje).
-- As funções de janela ficam em CTEs próprios; a agregação vem no CTE seguinte.
CREATE OR REFRESH MATERIALIZED VIEW lakehouse_vertice.gold.fato_projeto_semana (
  CONSTRAINT pv_nao_negativo EXPECT (pv >= 0) ON VIOLATION FAIL UPDATE,
  CONSTRAINT ev_ate_o_orcamento EXPECT (ev <= orcamento) ON VIOLATION FAIL UPDATE
)
COMMENT 'Uma linha por projeto e semana (sexta-feira), da semana do início até 16/10/2026. Valor planejado (pv), valor agregado (ev, do % do status semanal) e custo real acumulado (ac), com SPI, CPI e EAC da semana, o último farol publicado pelo gerente e as horas disponíveis, apontadas e ociosas do timesheet.'
AS
WITH semanas AS (
  -- uma linha por sexta-feira, da semana do início até hoje
  SELECT
    projeto_id,
    CAST(orcamento_custo AS DOUBLE) AS orcamento,
    explode(sequence(
      date_add(CAST(date_trunc('WEEK', data_inicio) AS DATE), 4),
      DATE'2026-10-16',
      INTERVAL 1 WEEK
    )) AS semana
  FROM projetos
  WHERE data_inicio <= DATE'2026-10-16'
),
fracao_tarefa AS (
  -- quanto do prazo baseline de cada tarefa já tinha passado naquela sexta (de 0 a 1)
  SELECT
    s.projeto_id,
    s.semana,
    t.horas,
    CASE
      WHEN datediff(t.fim_baseline, t.inicio_baseline) <= 0
        THEN CASE WHEN s.semana >= t.fim_baseline THEN 1.0 ELSE 0.0 END
      ELSE greatest(0.0, least(1.0,
        datediff(s.semana, t.inicio_baseline) / datediff(t.fim_baseline, t.inicio_baseline)))
    END AS fracao_baseline
  FROM semanas s
  JOIN tarefas t ON t.projeto_id = s.projeto_id
),
planejado AS (
  SELECT
    projeto_id,
    semana,
    sum(horas * fracao_baseline) / sum(horas) AS fracao_planejada
  FROM fracao_tarefa
  GROUP BY projeto_id, semana
),
status_da_semana AS (
  -- projeto concluído não publica mais status: fica valendo o último % e o último farol
  SELECT
    s.projeto_id,
    s.semana,
    last_value(st.pct_concluido, true) OVER janela AS pct_concluido,
    last_value(st.farol, true) OVER janela AS farol_do_gerente
  FROM semanas s
  LEFT JOIN status_semanal st
    ON st.projeto_id = s.projeto_id AND st.data_status = s.semana
  WINDOW janela AS (PARTITION BY s.projeto_id ORDER BY s.semana ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
),
custo_da_semana AS (
  SELECT projeto_id, semana, sum(CAST(valor AS DOUBLE)) AS custo
  FROM custos
  GROUP BY projeto_id, semana
),
custo_acumulado AS (
  SELECT
    s.projeto_id,
    s.semana,
    sum(coalesce(c.custo, 0)) OVER (
      PARTITION BY s.projeto_id ORDER BY s.semana ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS ac
  FROM semanas s
  LEFT JOIN custo_da_semana c ON c.projeto_id = s.projeto_id AND c.semana = s.semana
),
horas_da_semana AS (
  SELECT
    projeto_id,
    semana,
    sum(horas_disponiveis) AS horas_disponiveis,
    sum(horas_apontadas) AS horas_apontadas,
    -- hora extra (apontada > disponível) não compensa a ociosidade de outra pessoa
    sum(greatest(horas_disponiveis - horas_apontadas, 0)) AS horas_ociosas
  FROM apontamentos
  GROUP BY projeto_id, semana
),
valores AS (
  SELECT
    s.projeto_id,
    s.semana,
    s.orcamento,
    round(s.orcamento * coalesce(p.fracao_planejada, 0), 2) AS pv,
    round(s.orcamento * (coalesce(CAST(st.pct_concluido AS DOUBLE), 0) / 100), 2) AS ev,
    round(a.ac, 2) AS ac,
    st.pct_concluido,
    st.farol_do_gerente,
    coalesce(h.horas_disponiveis, 0) AS horas_disponiveis,
    coalesce(h.horas_apontadas, 0) AS horas_apontadas,
    coalesce(h.horas_ociosas, 0) AS horas_ociosas
  FROM semanas s
  LEFT JOIN planejado p ON p.projeto_id = s.projeto_id AND p.semana = s.semana
  LEFT JOIN status_da_semana st ON st.projeto_id = s.projeto_id AND st.semana = s.semana
  LEFT JOIN custo_acumulado a ON a.projeto_id = s.projeto_id AND a.semana = s.semana
  LEFT JOIN horas_da_semana h ON h.projeto_id = s.projeto_id AND h.semana = s.semana
)
SELECT
  projeto_id,
  semana,
  orcamento,
  pct_concluido,
  pv,
  ev,
  ac,
  round(try_divide(ev, pv), 4) AS spi,
  round(try_divide(ev, ac), 4) AS cpi,
  round(try_divide(orcamento, try_divide(ev, ac)), 2) AS eac,
  farol_do_gerente,
  horas_disponiveis,
  horas_apontadas,
  horas_ociosas
FROM valores;
