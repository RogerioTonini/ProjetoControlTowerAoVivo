-- gold.projeto_situacao_atual: a fotografia de hoje (16/10/2026), um projeto por linha.
-- O avanço de hoje vem das tarefas das três ferramentas (silver.tarefas), não do status.
CREATE OR REFRESH MATERIALIZED VIEW lakehouse_vertice.gold.projeto_situacao_atual
COMMENT 'Fotografia de 16/10/2026 dos 60 projetos (um por linha): o cadastro (cliente, segmento, tipo, ferramenta, gerente, contrato, orçamento, prazo) e os KPIs calculados sobre as tarefas das ferramentas: PV, EV, AC, SPI, CPI, EAC, estouro previsto, margem projetada, atraso e término projetados. situacao: concluído, crítico (SPI ou CPI < 0,8), atenção (< 0,9) ou ok. melancia = em andamento, farol do gerente verde e SPI < 0,9.'
AS
WITH avanco_tarefas AS (
  -- EV e PV em horas: Σ horas × % concluído e Σ horas × % do prazo baseline decorrido
  SELECT
    projeto_id,
    sum(horas) AS horas_totais,
    sum(horas * pct_concluido / 100) AS horas_agregadas,
    sum(horas * CASE
      WHEN datediff(fim_baseline, inicio_baseline) <= 0
        THEN CASE WHEN DATE'2026-10-16' >= fim_baseline THEN 1.0 ELSE 0.0 END
      ELSE greatest(0.0, least(1.0,
        datediff(DATE'2026-10-16', inicio_baseline) / datediff(fim_baseline, inicio_baseline)))
    END) AS horas_planejadas
  FROM tarefas
  GROUP BY projeto_id
),
custo_ate_hoje AS (
  SELECT projeto_id, sum(CAST(valor AS DOUBLE)) AS ac
  FROM custos
  WHERE data <= DATE'2026-10-16'
  GROUP BY projeto_id
),
ultimo_status AS (
  -- o farol do status mais recente (projeto concluído: o último que publicou)
  SELECT projeto_id, max_by(farol, data_status) AS farol_do_gerente
  FROM status_semanal
  WHERE data_status <= DATE'2026-10-16'
  GROUP BY projeto_id
),
kpis AS (
  SELECT
    p.*,
    CAST(p.orcamento_custo AS DOUBLE) AS orcamento,
    datediff(p.data_fim_baseline, p.data_inicio) AS duracao_baseline_dias,
    round(CAST(p.orcamento_custo AS DOUBLE) * a.horas_planejadas / a.horas_totais, 2) AS pv,
    round(CAST(p.orcamento_custo AS DOUBLE) * a.horas_agregadas / a.horas_totais, 2) AS ev,
    round(c.ac, 2) AS ac,
    try_divide(a.horas_agregadas, a.horas_planejadas) AS spi_bruto,
    try_divide(CAST(p.orcamento_custo AS DOUBLE) * a.horas_agregadas / a.horas_totais, c.ac) AS cpi_bruto,
    u.farol_do_gerente
  FROM projetos p
  LEFT JOIN avanco_tarefas a ON a.projeto_id = p.projeto_id
  LEFT JOIN custo_ate_hoje c ON c.projeto_id = p.projeto_id
  LEFT JOIN ultimo_status u ON u.projeto_id = p.projeto_id
)
SELECT
  projeto_id,
  concat(projeto_id, ' · ', nome_projeto) AS projeto,
  nome_projeto,
  cliente,
  segmento,
  tipo_projeto,
  ferramenta,
  gerente_projeto,
  CAST(valor_contrato AS DOUBLE) AS valor_contrato,
  orcamento,
  data_inicio,
  data_fim_baseline,
  duracao_baseline_dias,
  status,
  pv,
  ev,
  ac,
  round(spi_bruto, 4) AS spi,
  round(cpi_bruto, 4) AS cpi,
  round(try_divide(orcamento, cpi_bruto), 2) AS eac,
  round(greatest(try_divide(orcamento, cpi_bruto) - orcamento, 0), 2) AS estouro_previsto,
  round((CAST(valor_contrato AS DOUBLE) - try_divide(orcamento, cpi_bruto)) / CAST(valor_contrato AS DOUBLE), 4) AS margem_projetada,
  round(try_divide(duracao_baseline_dias, spi_bruto) - duracao_baseline_dias, 0) AS atraso_projetado_dias,
  date_add(data_inicio, CAST(round(try_divide(duracao_baseline_dias, spi_bruto), 0) AS INT)) AS termino_projetado,
  CASE
    WHEN status <> 'em_andamento' THEN 'concluído'
    WHEN spi_bruto < 0.8 OR cpi_bruto < 0.8 THEN 'crítico'
    WHEN spi_bruto < 0.9 OR cpi_bruto < 0.9 THEN 'atenção'
    ELSE 'ok'
  END AS situacao,
  farol_do_gerente,
  -- regra do manual da Vértice: o farol segue o número, não a percepção do gerente
  CASE
    WHEN spi_bruto >= 0.95 THEN 'verde'
    WHEN spi_bruto >= 0.90 THEN 'amarelo'
    ELSE 'vermelho'
  END AS farol_calculado,
  coalesce(status = 'em_andamento' AND farol_do_gerente = 'verde' AND spi_bruto < 0.9, false) AS melancia
FROM kpis;

-- gold.utilizacao_pessoa_semana: quem está parado, onde e quanto isso custa.
CREATE OR REFRESH MATERIALIZED VIEW lakehouse_vertice.gold.utilizacao_pessoa_semana
COMMENT 'Uso do timesheet por pessoa, projeto e semana (sexta-feira): nome, papel e senioridade, horas disponíveis, apontadas e ociosas, utilizacao (apontadas ÷ disponíveis, acima de 1 é hora extra), custo_ocioso (horas ociosas × custo/hora) e o SPI do projeto naquela semana.'
AS SELECT
  a.colaborador_id,
  c.nome,
  c.papel,
  c.senioridade,
  a.projeto_id,
  a.semana,
  a.horas_disponiveis,
  a.horas_apontadas,
  greatest(a.horas_disponiveis - a.horas_apontadas, 0) AS horas_ociosas,
  round(try_divide(a.horas_apontadas, a.horas_disponiveis), 4) AS utilizacao,
  round(greatest(a.horas_disponiveis - a.horas_apontadas, 0) * CAST(c.custo_hora AS DOUBLE), 2) AS custo_ocioso,
  f.spi AS spi_do_projeto
FROM apontamentos a
LEFT JOIN colaboradores c ON c.colaborador_id = a.colaborador_id
LEFT JOIN lakehouse_vertice.gold.fato_projeto_semana f
  ON f.projeto_id = a.projeto_id AND f.semana = a.semana;
