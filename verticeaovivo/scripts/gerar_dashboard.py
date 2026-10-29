#!/usr/bin/env python3
"""Gera o dashboard AI/BI do Projeto Farol (resources/dashboard-portfolio.lvdash.json).

Três páginas, cada uma respondendo a uma pergunta do dono:
  Portfólio     quais projetos estão atrasados e quanto isso vai custar
  Pessoas       tenho gente parada enquanto outro projeto pede gente
  Fornecedores  quem está atrasando as entregas

As queries da gold usam o nome PURO da tabela: o catálogo e o schema vêm do
recurso do bundle (dataset_catalog / dataset_schema). A silver.entregas_fornecedor
vai com o nome completo, porque o schema padrão do dashboard é a gold.

Uso:
  python3 scripts/gerar_dashboard.py [--conferir <arquivo.sql>]

--conferir grava também um .sql com as mesmas queries, com lakehouse_vertice.gold.
prefixado, para rodar antes do deploy:
  python3 scripts/run_sql.py <arquivo.sql> --profile <perfil>
"""
import argparse, json, re
from pathlib import Path

SAIDA = Path(__file__).resolve().parent.parent / "resources" / "dashboard-portfolio.lvdash.json"
TABELAS_GOLD = (
    "projeto_situacao_atual",
    "fato_projeto_semana",
    "utilizacao_pessoa_semana",
    "status_estruturado",
)

# cores da Jornada e as da situação do projeto
AZUL, CIANO, FUNDO_ESCURO = "#0059DB", "#22C2F4", "#14141A"
CRITICO, ATENCAO, OK = "#FF5F46", "#F6C344", CIANO
CORES_SITUACAO = [
    {"value": "crítico", "color": CRITICO},
    {"value": "atenção", "color": ATENCAO},
    {"value": "ok", "color": OK},
]

# ---------------------------------------------------------------------------
# Datasets: toda a regra de negócio fica no SQL. Razão é SUM/SUM, nunca AVG de razão.
# "Hoje" é 16/10/2026: as datas são fixas, nunca current_date().
# ---------------------------------------------------------------------------
DATASETS = {
    "ds_kpis": ("KPIs da carteira em andamento", """
SELECT
  sum(valor_contrato) AS carteira,
  sum(ev) / sum(pv) AS spi,
  sum(ev) / sum(ac) AS cpi,
  sum(estouro_previsto) AS estouro_previsto,
  count_if(situacao IN ('atenção', 'crítico')) AS em_risco,
  count_if(situacao = 'crítico') AS criticos,
  count_if(melancia) AS melancias
FROM projeto_situacao_atual
WHERE status = 'em_andamento'
"""),
    "ds_projetos": ("Projetos em andamento", """
SELECT
  projeto_id,
  projeto,
  cliente,
  gerente_projeto,
  situacao,
  spi,
  cpi,
  estouro_previsto,
  margem_projetada,
  atraso_projetado_dias,
  farol_do_gerente,
  farol_calculado,
  CASE WHEN melancia THEN 'sim' ELSE '' END AS melancia
FROM projeto_situacao_atual
WHERE status = 'em_andamento'
ORDER BY estouro_previsto DESC
"""),
    "ds_carteira_semana": ("SPI e CPI semanais da carteira", """
SELECT
  semana,
  sum(ev) / sum(pv) AS spi,
  sum(ev) / sum(ac) AS cpi
FROM fato_projeto_semana
WHERE semana >= DATE'2025-03-07'
GROUP BY semana
ORDER BY semana
"""),
    "ds_top_parados": ("Top 15 pessoas por custo da hora parada", """
SELECT
  concat(colaborador_id, ' · ', nome) AS pessoa,
  papel,
  sum(horas_ociosas) AS horas_ociosas,
  sum(custo_ocioso) AS custo_ocioso,
  try_divide(sum(horas_apontadas), sum(horas_disponiveis)) AS utilizacao
FROM utilizacao_pessoa_semana
WHERE semana > DATE'2026-07-24'
GROUP BY colaborador_id, nome, papel
ORDER BY custo_ocioso DESC
LIMIT 15
"""),
    "ds_pessoas": ("Utilização por pessoa e projeto (12 semanas)", """
SELECT
  colaborador_id,
  nome,
  papel,
  senioridade,
  projeto_id,
  sum(horas_disponiveis) AS horas_disponiveis,
  sum(horas_apontadas) AS horas_apontadas,
  try_divide(sum(horas_apontadas), sum(horas_disponiveis)) AS utilizacao,
  sum(custo_ocioso) AS custo_ocioso
FROM utilizacao_pessoa_semana
WHERE semana > DATE'2026-07-24'
GROUP BY colaborador_id, nome, papel, senioridade, projeto_id
ORDER BY utilizacao ASC
"""),
    "ds_causas": ("Causas de bloqueio por projeto (90 dias)", """
SELECT
  projeto_id,
  causa_bloqueio,
  count(*) AS status
FROM status_estruturado
WHERE data_status >= DATE'2026-07-18'
  AND causa_bloqueio NOT IN ('sem_bloqueio', 'nao_reportado')
GROUP BY projeto_id, causa_bloqueio
ORDER BY projeto_id
"""),
    "ds_fornecedores": ("Entregas por fornecedor", """
SELECT
  fornecedor,
  count(DISTINCT fornecedor_como_veio) AS grafias,
  array_join(array_sort(collect_set(fornecedor_como_veio)), ' | ') AS como_aparece,
  count(*) AS entregas,
  try_divide(
    sum(CASE WHEN data_entrega IS NOT NULL THEN prazo_real_dias END),
    sum(CASE WHEN data_entrega IS NOT NULL THEN prazo_prometido_dias END)
  ) AS prazo_real_sobre_prometido,
  try_divide(count_if(data_entrega <= data_prometida), count_if(data_entrega IS NOT NULL)) AS pct_no_prazo,
  count_if(em_atraso) AS em_atraso_hoje
FROM lakehouse_vertice.silver.entregas_fornecedor
GROUP BY fornecedor
ORDER BY prazo_real_sobre_prometido DESC
"""),
    "ds_entregas_atrasadas": ("Entregas em atraso hoje", """
SELECT
  entrega_id,
  projeto_id,
  fornecedor,
  fornecedor_como_veio,
  item,
  valor,
  data_pedido,
  data_prometida,
  datediff(DATE'2026-10-16', data_prometida) AS dias_em_atraso
FROM lakehouse_vertice.silver.entregas_fornecedor
WHERE em_atraso
ORDER BY dias_em_atraso DESC
"""),
}

# ---------------------------------------------------------------------------
# Formatos
# ---------------------------------------------------------------------------
REAIS = {
    "type": "number-currency",
    "currencyCode": "BRL",
    "abbreviation": "compact",
    "decimalPlaces": {"type": "max", "places": 2},
}
PERCENTUAL = {"type": "number-percent", "decimalPlaces": {"type": "max", "places": 1}}
INDICE = {"type": "number", "decimalPlaces": {"type": "exact", "places": 2}}


# ---------------------------------------------------------------------------
# Widgets: cada função devolve o item do layout (widget + posição)
# ---------------------------------------------------------------------------
def posicao(x, y, w, h):
    return {"x": x, "y": y, "width": w, "height": h}


def campo(nome):
    return {"name": nome, "expression": f"`{nome}`"}


def consulta(dataset, campos, filtros=None):
    q = {"datasetName": dataset, "fields": campos, "disaggregated": True}
    if filtros:
        q["filters"] = [{"expression": f} for f in filtros]
    return [{"name": "main_query", "query": q}]


def texto(nome, titulo, subtitulo, pos):
    return {
        "widget": {
            "name": nome,
            "multilineTextboxSpec": {"lines": [f"## {titulo}\n", "\n", subtitulo]},
        },
        "position": pos,
    }


def contador(nome, dataset, coluna, titulo, formato, pos):
    valor = {"fieldName": coluna, "displayName": titulo}
    if formato:
        valor["format"] = formato
    return {
        "widget": {
            "name": nome,
            "queries": consulta(dataset, [campo(coluna)]),
            "spec": {
                "version": 2,
                "widgetType": "counter",
                "encodings": {"value": valor},
                "frame": {"showTitle": True, "title": titulo},
            },
        },
        "position": pos,
    }


def tabela(nome, dataset, colunas, titulo, pos, descricao=None):
    """colunas: lista de (campo, rótulo, formato ou None)."""
    encod = []
    for c, rotulo, formato in colunas:
        col = {"fieldName": c, "displayName": rotulo}
        if formato:
            col["format"] = formato
        encod.append(col)
    frame = {"showTitle": True, "title": titulo}
    if descricao:
        frame.update(description=descricao, showDescription=True)
    return {
        "widget": {
            "name": nome,
            "queries": consulta(dataset, [campo(c) for c, _, _ in colunas]),
            "spec": {
                "version": 2,
                "widgetType": "table",
                "encodings": {"columns": encod},
                "frame": frame,
            },
        },
        "position": pos,
    }


def linha_de_corte(eixo, valor, rotulo):
    """Linha de referência (0,9 = atenção) num gráfico."""
    return {
        "type": "horizontal-line" if eixo == "y" else "vertical-line",
        "encodings": {
            eixo: {"dataValue": str(valor), "dataType": "DOUBLE"},
            "label": {"value": rotulo},
            "color": {"value": ATENCAO},
        },
    }


# ---------------------------------------------------------------------------
# Página 1 · Portfólio
# ---------------------------------------------------------------------------
def pagina_portfolio():
    kpis = [
        ("kpi-carteira", "carteira", "Carteira em andamento", REAIS),
        ("kpi-spi", "spi", "SPI da carteira", INDICE),
        ("kpi-cpi", "cpi", "CPI da carteira", INDICE),
        ("kpi-estouro", "estouro_previsto", "Estouro previsto", REAIS),
        ("kpi-em-risco", "em_risco", "Projetos em risco", None),
        ("kpi-criticos", "criticos", "Críticos", None),
        ("kpi-melancias", "melancias", "Melancias", None),
    ]
    layout = [
        texto(
            "titulo-portfolio",
            "Quais projetos estão atrasados, de quais clientes, e quanto isso vai custar?",
            "Carteira em andamento na fotografia de 16/10/2026. SPI ou CPI abaixo de 0,9 = atenção, abaixo de 0,8 = crítico.",
            posicao(0, 0, 12, 2),
        )
    ]
    # 4 contadores na primeira linha (w3) e 3 na segunda (w4)
    for i, (nome, coluna, titulo, formato) in enumerate(kpis):
        pos = posicao(i * 3, 2, 3, 3) if i < 4 else posicao((i - 4) * 4, 5, 4, 3)
        layout.append(contador(nome, "ds_kpis", coluna, titulo, formato, pos))

    barra_estouro = {
        "widget": {
            "name": "barra-estouro",
            "queries": consulta(
                "ds_projetos",
                [campo("projeto_id"), campo("estouro_previsto"), campo("situacao")],
                filtros=["`estouro_previsto` > 0"],
            ),
            "spec": {
                "version": 3,
                "widgetType": "bar",
                "encodings": {
                    "x": {
                        "fieldName": "projeto_id",
                        "scale": {"type": "categorical", "sort": {"by": "y-reversed"}},
                        "displayName": "Projeto",
                    },
                    "y": {
                        "fieldName": "estouro_previsto",
                        "scale": {"type": "quantitative"},
                        "displayName": "Estouro previsto",
                        "format": REAIS,
                    },
                    "color": {
                        "fieldName": "situacao",
                        "scale": {"type": "categorical", "mappings": CORES_SITUACAO},
                        "displayName": "Situação",
                    },
                },
                "frame": {
                    "showTitle": True,
                    "title": "Estouro previsto por projeto",
                    "description": "EAC − orçamento, só os projetos que vão estourar",
                    "showDescription": True,
                },
            },
        },
        "position": posicao(0, 8, 6, 6),
    }
    dispersao = {
        "widget": {
            "name": "dispersao-spi-cpi",
            "queries": consulta(
                "ds_projetos",
                [campo("cpi"), campo("spi"), campo("situacao"), campo("projeto")],
            ),
            "spec": {
                "version": 3,
                "widgetType": "scatter",
                "encodings": {
                    "x": {"fieldName": "cpi", "scale": {"type": "quantitative"}, "displayName": "CPI"},
                    "y": {"fieldName": "spi", "scale": {"type": "quantitative"}, "displayName": "SPI"},
                    "color": {
                        "fieldName": "situacao",
                        "scale": {"type": "categorical", "mappings": CORES_SITUACAO},
                        "displayName": "Situação",
                    },
                    "extra": [{"fieldName": "projeto", "displayName": "Projeto"}],
                },
                "annotations": [
                    linha_de_corte("y", 0.9, "SPI 0,9"),
                    linha_de_corte("x", 0.9, "CPI 0,9"),
                ],
                "frame": {
                    "showTitle": True,
                    "title": "SPI × CPI por projeto",
                    "description": "Embaixo e à esquerda: atrasado e estourando",
                    "showDescription": True,
                },
            },
        },
        "position": posicao(6, 8, 6, 6),
    }
    linha_semanal = {
        "widget": {
            "name": "linha-spi-cpi-semanal",
            "queries": consulta("ds_carteira_semana", [campo("semana"), campo("spi"), campo("cpi")]),
            "spec": {
                "version": 3,
                "widgetType": "line",
                "encodings": {
                    "x": {"fieldName": "semana", "scale": {"type": "temporal"}, "displayName": "Semana"},
                    "y": {
                        "scale": {"type": "quantitative"},
                        "fields": [
                            {"fieldName": "spi", "displayName": "SPI"},
                            {"fieldName": "cpi", "displayName": "CPI"},
                        ],
                    },
                },
                "annotations": [linha_de_corte("y", 0.9, "atenção")],
                "frame": {
                    "showTitle": True,
                    "title": "SPI e CPI da carteira, semana a semana",
                    "description": "Σ EV ÷ Σ PV e Σ EV ÷ Σ AC de toda sexta, com o % do status semanal",
                    "showDescription": True,
                },
            },
        },
        "position": posicao(0, 14, 12, 5),
    }
    tabela_projetos = tabela(
        "tabela-projetos",
        "ds_projetos",
        [
            ("projeto", "Projeto", None),
            ("cliente", "Cliente", None),
            ("gerente_projeto", "Gerente", None),
            ("situacao", "Situação", None),
            ("farol_do_gerente", "Farol do gerente", None),
            ("farol_calculado", "Farol pelo número", None),
            ("melancia", "Melancia", None),
            ("spi", "SPI", INDICE),
            ("cpi", "CPI", INDICE),
            ("estouro_previsto", "Estouro previsto", REAIS),
            ("margem_projetada", "Margem projetada", PERCENTUAL),
            ("atraso_projetado_dias", "Atraso projetado (dias)", None),
        ],
        "Projetos em andamento",
        posicao(0, 19, 12, 8),
        descricao="Melancia: verde por fora (farol do gerente), vermelho por dentro (SPI < 0,9)",
    )
    layout += [barra_estouro, dispersao, linha_semanal, tabela_projetos]
    return {
        "name": "portfolio",
        "displayName": "Portfólio",
        "pageType": "PAGE_TYPE_CANVAS",
        "layoutVersion": "GRID_V1",
        "layout": layout,
    }


# ---------------------------------------------------------------------------
# Página 2 · Pessoas
# ---------------------------------------------------------------------------
def pagina_pessoas():
    top_parados = {
        "widget": {
            "name": "barra-top-parados",
            "queries": consulta("ds_top_parados", [campo("pessoa"), campo("custo_ocioso")]),
            "spec": {
                "version": 3,
                "widgetType": "bar",
                "encodings": {
                    "x": {
                        "fieldName": "custo_ocioso",
                        "scale": {"type": "quantitative"},
                        "displayName": "Custo da hora parada",
                        "format": REAIS,
                    },
                    "y": {
                        "fieldName": "pessoa",
                        "scale": {"type": "categorical", "sort": {"by": "x-reversed"}},
                        "displayName": "Pessoa",
                    },
                },
                "frame": {
                    "showTitle": True,
                    "title": "Top 15 pessoas por custo da hora parada",
                    "description": "Horas disponíveis não apontadas × custo/hora, últimas 12 semanas",
                    "showDescription": True,
                },
            },
        },
        "position": posicao(0, 2, 6, 8),
    }
    causas = {
        "widget": {
            "name": "barra-causas",
            "queries": consulta("ds_causas", [campo("projeto_id"), campo("status"), campo("causa_bloqueio")]),
            "spec": {
                "version": 3,
                "widgetType": "bar",
                "encodings": {
                    "x": {"fieldName": "projeto_id", "scale": {"type": "categorical"}, "displayName": "Projeto"},
                    "y": {"fieldName": "status", "scale": {"type": "quantitative"}, "displayName": "Status com bloqueio"},
                    "color": {"fieldName": "causa_bloqueio", "scale": {"type": "categorical"}, "displayName": "Causa"},
                },
                "frame": {
                    "showTitle": True,
                    "title": "Causas de bloqueio por projeto",
                    "description": "Status semanais dos últimos 90 dias, classificados pela IA",
                    "showDescription": True,
                },
            },
        },
        "position": posicao(6, 2, 6, 8),
    }
    tabela_utilizacao = tabela(
        "tabela-utilizacao",
        "ds_pessoas",
        [
            ("colaborador_id", "Pessoa", None),
            ("nome", "Nome", None),
            ("papel", "Papel", None),
            ("senioridade", "Senioridade", None),
            ("projeto_id", "Projeto", None),
            ("horas_disponiveis", "Horas disponíveis", None),
            ("horas_apontadas", "Horas apontadas", None),
            ("utilizacao", "Utilização", PERCENTUAL),
            ("custo_ocioso", "Custo da hora parada", REAIS),
        ],
        "Utilização por pessoa e projeto",
        posicao(0, 10, 12, 8),
        descricao="Últimas 12 semanas, da mais parada à mais ocupada (acima de 100% é hora extra)",
    )
    return {
        "name": "pessoas",
        "displayName": "Pessoas",
        "pageType": "PAGE_TYPE_CANVAS",
        "layoutVersion": "GRID_V1",
        "layout": [
            texto(
                "titulo-pessoas",
                "Tenho gente parada enquanto outro projeto pede gente?",
                "Timesheet das últimas 12 semanas (até 16/10/2026) e a causa que o gerente escreve no status.",
                posicao(0, 0, 12, 2),
            ),
            top_parados,
            causas,
            tabela_utilizacao,
        ],
    }


# ---------------------------------------------------------------------------
# Página 3 · Fornecedores
# ---------------------------------------------------------------------------
def pagina_fornecedores():
    return {
        "name": "fornecedores",
        "displayName": "Fornecedores",
        "pageType": "PAGE_TYPE_CANVAS",
        "layoutVersion": "GRID_V1",
        "layout": [
            texto(
                "titulo-fornecedores",
                "O que vai dar errado no próximo mês?",
                "As entregas das consultorias: o que foi prometido × o que chegou, e o que está atrasado hoje (16/10/2026).",
                posicao(0, 0, 12, 2),
            ),
            tabela(
                "tabela-fornecedores",
                "ds_fornecedores",
                [
                    ("fornecedor", "Fornecedor", None),
                    ("grafias", "Grafias no cadastro", None),
                    ("como_aparece", "Como aparece", None),
                    ("entregas", "Entregas", None),
                    ("prazo_real_sobre_prometido", "Prazo real ÷ prometido", INDICE),
                    ("pct_no_prazo", "% no prazo", PERCENTUAL),
                    ("em_atraso_hoje", "Em atraso hoje", None),
                ],
                "Entregas por fornecedor",
                posicao(0, 2, 12, 4),
            ),
            tabela(
                "tabela-entregas-atrasadas",
                "ds_entregas_atrasadas",
                [
                    ("entrega_id", "Entrega", None),
                    ("projeto_id", "Projeto", None),
                    ("fornecedor", "Fornecedor", None),
                    ("fornecedor_como_veio", "Como veio no cadastro", None),
                    ("item", "Item", None),
                    ("valor", "Valor", REAIS),
                    ("data_pedido", "Pedido", None),
                    ("data_prometida", "Prometida para", None),
                    ("dias_em_atraso", "Dias em atraso", None),
                ],
                "Entregas em atraso hoje",
                posicao(0, 6, 12, 6),
            ),
        ],
    }


# ---------------------------------------------------------------------------
# Montagem
# ---------------------------------------------------------------------------
def linhas_da_query(sql: str) -> list[str]:
    """queryLines: cada linha termina em \\n, porque o dashboard concatena sem separador."""
    return [l + "\n" for l in sql.strip().splitlines()]


def dashboard() -> dict:
    return {
        "datasets": [
            {"name": nome, "displayName": titulo, "queryLines": linhas_da_query(sql)}
            for nome, (titulo, sql) in DATASETS.items()
        ],
        "pages": [pagina_portfolio(), pagina_pessoas(), pagina_fornecedores()],
        "uiSettings": {
            "theme": {
                "canvasBackgroundColor": {"light": "#F5F7FA", "dark": FUNDO_ESCURO},
                "widgetBackgroundColor": {"light": "#FFFFFF", "dark": "#1C1C24"},
                "widgetBorderColor": {"light": "#FFFFFF", "dark": "#1C1C24"},
                "fontColor": {"light": FUNDO_ESCURO, "dark": "#E8ECF0"},
                "selectionColor": {"light": AZUL, "dark": CIANO},
                "visualizationColors": [
                    AZUL, CIANO, "#7B61FF", ATENCAO, CRITICO, "#2EC4A6", "#C77DFF", "#9AA5B1",
                ],
                "widgetHeaderAlignment": "LEFT",
            }
        },
    }


def com_prefixo(sql: str) -> str:
    """Para rodar fora do dashboard: tabela da gold ganha lakehouse_vertice.gold."""
    nomes = "|".join(TABELAS_GOLD)
    return re.sub(rf"\b(FROM|JOIN)\s+({nomes})\b", r"\1 lakehouse_vertice.gold.\2", sql)


def conferencia(arquivo: Path) -> None:
    """Um .sql com a contagem de linhas de cada dataset e, depois, cada query inteira."""
    contagens = "\nUNION ALL\n".join(
        f"SELECT '{nome}' AS dataset, count(*) AS linhas FROM (\n{com_prefixo(sql).strip()}\n)"
        for nome, (_, sql) in DATASETS.items()
    )
    partes = [contagens] + [
        f"-- {nome}\n{com_prefixo(sql).strip()}" for nome, (_, sql) in DATASETS.items()
    ]
    arquivo.write_text(";\n\n".join(partes) + "\n", encoding="utf-8")
    print(f"conferência gravada em {arquivo}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--conferir", help="grava também um .sql com as queries prefixadas")
    args = ap.parse_args()

    d = dashboard()
    SAIDA.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    widgets = sum(len(p["layout"]) for p in d["pages"])
    print(f"{SAIDA.name}: {len(d['datasets'])} datasets, {len(d['pages'])} páginas, {widgets} widgets")
    if args.conferir:
        conferencia(Path(args.conferir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
