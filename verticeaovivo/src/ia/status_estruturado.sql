-- gold.status_estruturado: o texto livre do status semanal vira coluna.
-- A tabela ACUMULA: cada execução só classifica os status que ainda não estão nela
-- (a IA leva uns 5 s por texto e não pode ser refeita a cada segunda-feira).
-- Três métodos, do mais barato ao mais caro:
--   regra         status vazio ou "sem bloqueio" escrito no texto
--   ia            status com bloqueio dos últimos 90 dias (ai_classify + ai_extract)
--   palavra_chave status com bloqueio mais antigos (RLIKE)
-- Atenção: a sql_task corta o arquivo em cada ponto e vírgula, então não use esse caractere dentro de textos.

CREATE TABLE IF NOT EXISTS lakehouse_vertice.gold.status_estruturado (
  projeto_id       STRING    COMMENT 'Código do projeto (PRJ-xxx)',
  data_status      DATE      COMMENT 'Sexta-feira do status semanal',
  farol            STRING    COMMENT 'Farol informado pelo gerente: verde, amarelo ou vermelho',
  causa_bloqueio   STRING    COMMENT 'Causa do bloqueio: change_freeze, falta_sre, dependencia_fornecedor, rotatividade, mudanca_escopo, bug_retrabalho, aprovacao_cliente, sem_bloqueio, nao_reportado ou outro',
  bloqueio         STRING    COMMENT 'O que está travando o projeto, em poucas palavras (só no método ia)',
  quem_destrava    STRING    COMMENT 'Pessoa, área ou empresa que resolve o bloqueio (só no método ia)',
  dias_impacto     DOUBLE    COMMENT 'Dias de impacto no cronograma declarados no status (1 semana = 7)',
  metodo           STRING    COMMENT 'Como o status foi classificado: regra, ia ou palavra_chave',
  texto_status     STRING    COMMENT 'Texto original do status semanal',
  _classificado_em TIMESTAMP COMMENT 'Quando a linha foi classificada (auditoria da carga)'
)
COMMENT 'Status semanal estruturado: causa do bloqueio, o que trava, quem destrava e dias de impacto declarados, por projeto e sexta-feira. Classificado por regra (sem bloqueio), por IA (últimos 90 dias com bloqueio) ou por palavra-chave (histórico). Tabela incremental: nada é reclassificado.';

MERGE INTO lakehouse_vertice.gold.status_estruturado AS alvo
USING (
  WITH pendentes AS (
    -- só os status que ainda não foram classificados
    SELECT
      s.projeto_id,
      s.data_status,
      s.farol,
      s.texto_status,
      s.status_vazio,
      lower(coalesce(s.texto_status, '')) AS t
    FROM lakehouse_vertice.silver.status_semanal s
    LEFT ANTI JOIN lakehouse_vertice.gold.status_estruturado e
      ON e.projeto_id = s.projeto_id AND e.data_status = s.data_status
  ),
  com_metodo AS (
    SELECT
      *,
      CASE
        WHEN status_vazio
          OR t LIKE '%bloqueios: nenhum%'
          OR t LIKE '%sem bloqueios%'
          OR t LIKE '%nada relevante%' THEN 'regra'
        WHEN data_status >= DATE'2026-07-18' THEN 'ia'
        ELSE 'palavra_chave'
      END AS metodo
    FROM pendentes
  ),
  com_ia AS (
    -- a IA só é chamada nas linhas do método ia (uma chamada de cada função por linha)
    SELECT
      *,
      CASE WHEN metodo = 'ia' THEN ai_classify(
        texto_status,
        '["change_freeze","falta_sre","dependencia_fornecedor","rotatividade","mudanca_escopo","bug_retrabalho","aprovacao_cliente","sem_bloqueio"]',
        map('version', '2.0')
      ) END AS ia_causa,
      CASE WHEN metodo = 'ia' THEN ai_extract(
        texto_status,
        '{"bloqueio":{"type":"string","description":"o que está travando o projeto, em poucas palavras"},"quem_destrava":{"type":"string","description":"pessoa, área ou empresa que resolve o bloqueio"},"dias_impacto":{"type":"number","description":"dias de impacto no cronograma. 1 semana = 7. 0 se não houver impacto"}}',
        map('version', '2.0')
      ) END AS ia_campos
    FROM com_metodo
  )
  SELECT
    projeto_id,
    data_status,
    farol,
    CASE
      WHEN status_vazio THEN 'nao_reportado'
      WHEN metodo = 'regra' THEN 'sem_bloqueio'
      WHEN metodo = 'ia' THEN ia_causa:response[0]::STRING
      WHEN t RLIKE 'freeze|congelamento|janela de deploy' THEN 'change_freeze'
      WHEN t RLIKE 'sre|infraestrutura|ambiente de homologação' THEN 'falta_sre'
      WHEN t RLIKE 'forge|consultoria|fornecedor' THEN 'dependencia_fornecedor'
      WHEN t RLIKE 'saída de|rotatividade|onboarding' THEN 'rotatividade'
      WHEN t RLIKE 'escopo|change request|regra de negócio' THEN 'mudanca_escopo'
      WHEN t RLIKE 'bugs|regressão|refazendo' THEN 'bug_retrabalho'
      WHEN t RLIKE 'aprovação do cliente|homologação do cliente' THEN 'aprovacao_cliente'
      ELSE 'outro'
    END AS causa_bloqueio,
    CASE WHEN metodo = 'ia' THEN ia_campos:response:bloqueio::STRING END AS bloqueio,
    CASE WHEN metodo = 'ia' THEN ia_campos:response:quem_destrava::STRING END AS quem_destrava,
    CASE
      WHEN metodo = 'ia' THEN ia_campos:response:dias_impacto::DOUBLE
      WHEN t LIKE '%impacto estimado: 1 semana%' THEN 7.0
      ELSE CAST(nullif(regexp_extract(t, 'impacto estimado de ([0-9]+) dias', 1), '') AS DOUBLE)
    END AS dias_impacto,
    metodo,
    texto_status,
    current_timestamp() AS _classificado_em
  FROM com_ia
) AS novo
ON alvo.projeto_id = novo.projeto_id AND alvo.data_status = novo.data_status
WHEN NOT MATCHED THEN INSERT *;

-- leitura: quantos status por método e causa
SELECT metodo, causa_bloqueio, count(*) AS status
FROM lakehouse_vertice.gold.status_estruturado
GROUP BY metodo, causa_bloqueio
ORDER BY metodo, status DESC
