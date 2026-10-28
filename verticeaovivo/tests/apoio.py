"""Apoio aos testes: carrega os scripts de src/verticeaovivo/main/scripts pelo caminho do arquivo.

verticeaovivo/main.py esconde a pasta verticeaovivo/main/, então `import verticeaovivo.main.scripts` não funciona.
"""
import importlib.util
import pathlib
from types import ModuleType

SCRIPTS = pathlib.Path(__file__).parents[1] / "src/verticeaovivo/main/scripts"


def carregar_script(nome: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(nome, SCRIPTS / f"{nome}.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo
