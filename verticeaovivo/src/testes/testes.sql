-- Testes de qualidade da silver e da gold (sql_task, depois do medalhão).
-- Cada linha é um teste. Se o obtido não bate com o esperado, raise_error derruba a tarefa
-- com a mensagem do teste que falhou.
WITH testes AS (

  SELECT 1 AS n, 'os 60 projetos têm cronograma na silver.tarefas' AS teste,
         '60' AS esperado,
         CAST(count(DISTINCT t.projeto_id) AS STRING) AS obtido
  FROM lakehouse_vertice.silver.tarefas t
  JOIN lakehouse_vertice.silver.projetos p ON p.projeto_id = t.projeto_id

  UNION ALL
  SELECT 2, 'cada projeto veio de UMA ferramenta, a do cadastro do PMO',
         '0 projetos fora da regra',
         concat(CAST(count(*) AS STRING), ' projetos fora da regra')
  FROM (
    SELECT t.projeto_id
    FROM lakehouse_vertice.silver.tarefas t
    JOIN lakehouse_vertice.silver.projetos p ON p.projeto_id = t.projeto_id
    GROUP BY t.projeto_id
    HAVING count(DISTINCT t.ferramenta) > 1 OR max(t.ferramenta) <> max(p.ferramenta)
  )

  UNION ALL
  SELECT 3, 'as horas do Excel na silver = a soma das linhas de TOTAL das planilhas',
         CAST(round((SELECT sum(CAST(replace(horas_previstas, 'h', '') AS DOUBLE))
                     FROM lakehouse_vertice.bronze.excel_tarefas
                     WHERE tarefa = 'TOTAL'), 1) AS STRING),
         CAST(round(sum(horas), 1) AS STRING)
  FROM lakehouse_vertice.silver.tarefas
  WHERE ferramenta = 'excel'

  UNION ALL
  SELECT 4, 'uma linha por pessoa na silver.colaboradores',
         CAST(count(DISTINCT colaborador_id) AS STRING),
         CAST(count(*) AS STRING)
  FROM lakehouse_vertice.silver.colaboradores

  UNION ALL
  SELECT 5, 'a CodeForge virou um fornecedor só',
         '1',
         CAST(count(DISTINCT fornecedor) AS STRING)
  FROM lakehouse_vertice.silver.entregas_fornecedor
  WHERE lower(replace(fornecedor_como_veio, ' ', '')) LIKE '%codeforge%'

  UNION ALL
  SELECT 6, 'a limpeza não mudou o custo total (bronze com replace = silver)',
         CAST((SELECT sum(CAST(replace(valor, ',', '.') AS DECIMAL(18,2)))
               FROM lakehouse_vertice.bronze.custos) AS STRING),
         CAST(sum(valor) AS STRING)
  FROM lakehouse_vertice.silver.custos

  UNION ALL
  SELECT 7, 'os 60 projetos têm fotografia de hoje',
         '60',
         CAST(count(*) AS STRING)
  FROM lakehouse_vertice.gold.projeto_situacao_atual

  UNION ALL
  SELECT 8, 'todo projeto em andamento tem SPI e CPI',
         '0 sem SPI ou CPI',
         concat(CAST(count(*) AS STRING), ' sem SPI ou CPI')
  FROM lakehouse_vertice.gold.projeto_situacao_atual
  WHERE status = 'em_andamento' AND (spi IS NULL OR cpi IS NULL)

  UNION ALL
  -- o EV de hoje calculado pelo status semanal e pelas tarefas das ferramentas
  SELECT 9, 'o EV de hoje do status semanal bate com o das ferramentas (diferença < 1%)',
         'diferença < 1%',
         CASE WHEN abs(ev_status - ev_ferramentas) / ev_ferramentas < 0.01
              THEN 'diferença < 1%'
              ELSE concat('diferença de ', CAST(round(100 * abs(ev_status - ev_ferramentas) / ev_ferramentas, 2) AS STRING), '%')
         END
  FROM (
    SELECT
      (SELECT sum(ev) FROM lakehouse_vertice.gold.fato_projeto_semana WHERE semana = DATE'2026-10-16') AS ev_status,
      (SELECT sum(ev) FROM lakehouse_vertice.gold.projeto_situacao_atual) AS ev_ferramentas
  )

  UNION ALL
  SELECT 10, 'AC de hoje no fato = soma dos lançamentos até hoje',
         CAST(round((SELECT sum(CAST(valor AS DOUBLE))
                     FROM lakehouse_vertice.silver.custos
                     WHERE data <= DATE'2026-10-16'), 0) AS STRING),
         CAST(round(sum(ac), 0) AS STRING)
  FROM lakehouse_vertice.gold.fato_projeto_semana
  WHERE semana = DATE'2026-10-16'
)
SELECT
  n,
  teste,
  esperado,
  obtido,
  CASE
    WHEN obtido IS NULL OR obtido <> esperado
      THEN raise_error(concat('Teste ', n, ' falhou: ', teste, '. Esperado ', esperado, ', obtido ', coalesce(obtido, 'nulo')))
    ELSE 'ok'
  END AS resultado
FROM testes
ORDER BY n
