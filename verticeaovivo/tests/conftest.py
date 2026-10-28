"""Grava um log por arquivo de teste em tests/log/<arquivo>.log, recriado a cada execução.

Primeira linha: [dd/mm/yyyy hh:mm:ss.ssss] | Projeto: <projeto> - Hostname: <host>
Demais linhas:  [dd/mm/yyyy hh:mm:ss.ssss] | <o que foi executado> | SUCESSO ou ERRO
"""

import datetime
import pathlib
import socket
import tomllib

import pytest

PASTA_LOG = pathlib.Path(__file__).parent / "log"
PROJETO = tomllib.loads(
    (pathlib.Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8")
)["project"]["name"]

_iniciados: set[pathlib.Path] = set()
_descricoes: dict[str, str] = {}


def agora() -> str:
    """Data e hora no formato dd/mm/yyyy hh:mm:ss.ssss."""
    return datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S.%f")[:-2]


def gravar(arquivo: pathlib.Path, texto: str) -> None:
    if arquivo not in _iniciados:
        PASTA_LOG.mkdir(exist_ok=True)
        arquivo.write_text(
            f"[{agora()}] | Projeto: {PROJETO} - Hostname: {socket.gethostname()}\n",
            encoding="utf-8",
        )
        _iniciados.add(arquivo)
    with arquivo.open("a", encoding="utf-8") as f:
        f.write(f"{agora()} | {texto}\n")


def pytest_collection_modifyitems(items):
    """Guarda a descrição de cada teste: a 1ª linha da docstring (ou o nome) + o parâmetro, se houver."""
    for item in items:
        doc = (getattr(item, "obj", None) and item.obj.__doc__) or ""
        descricao = doc.strip().splitlines()[0] if doc.strip() else item.originalname
        if hasattr(item, "callspec"):
            descricao += f" [{item.callspec.id}]"
        _descricoes[item.nodeid] = descricao


@pytest.hookimpl
def pytest_runtest_logreport(report):
    # uma linha por teste: o resultado da execução, ou o erro de setup/teardown (fixture que quebrou)
    if report.when == "call" or (report.failed and report.when != "call"):
        resultado = "SUCESSO" if report.passed else "ERRO"
        descricao = _descricoes.get(report.nodeid, report.nodeid)
        if report.when != "call":
            descricao += f" ({report.when})"
        gravar(
            PASTA_LOG / f"{pathlib.Path(report.fspath).stem}.log",
            f"{descricao} | {resultado}",
        )
