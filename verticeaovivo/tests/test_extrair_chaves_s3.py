import json

import pytest

from tests.apoio import carregar_script

extrair_chaves_s3 = carregar_script("extrair_chaves_s3")

JOB_YML = """resources:
  jobs:
    ingestão:
      name: Ingestão
      tasks:
        - task_key: ingestao_data_lake
          notebook_task:
            base_parameters:
              AWS_ACCESS_KEY_ID: "AKIAFAKE123"
              AWS_SECRET_ACCESS_KEY: 'segredo/com+simbolos'
"""


def ler_json(caminho):
    return json.loads(caminho.read_text(encoding="utf-8"))


@pytest.fixture
def bundle(tmp_path):
    (tmp_path / "resources").mkdir()
    (tmp_path / extrair_chaves_s3.JOB).write_text(JOB_YML, encoding="utf-8")
    return tmp_path


def test_extrair_chaves_troca_valores_por_variaveis():
    """extrair_chaves: troca as chaves do YAML por ${var.…} e devolve os valores"""
    yml, valores = extrair_chaves_s3.extrair_chaves(JOB_YML)

    assert valores == {"s3_access_key_id": "AKIAFAKE123", "s3_secret_access_key": "segredo/com+simbolos"}
    assert "AWS_ACCESS_KEY_ID: ${var.s3_access_key_id}" in yml
    assert "AWS_SECRET_ACCESS_KEY: ${var.s3_secret_access_key}" in yml
    assert "AKIAFAKE123" not in yml and "segredo" not in yml
    assert yml.startswith("variables:\n  s3_access_key_id:\n")
    assert "  s3_secret_access_key:\n" in yml


def test_extrair_chaves_sem_chave_no_yaml():
    """extrair_chaves: YAML sem a chave gera ValueError dizendo qual faltou"""
    with pytest.raises(ValueError, match="AWS_ACCESS_KEY_ID"):
        extrair_chaves_s3.extrair_chaves("resources: {}\n")


def test_extrair_chaves_ja_extraidas():
    """extrair_chaves: YAML já com ${var.…} é recusado"""
    yml, _ = extrair_chaves_s3.extrair_chaves(JOB_YML)
    with pytest.raises(ValueError, match="já foram extraídas"):
        extrair_chaves_s3.extrair_chaves(yml)


def test_main_grava_overrides_e_reescreve_job(bundle):
    """main: grava variable-overrides.json e tira as chaves do job"""
    overrides = extrair_chaves_s3.main(bundle)

    assert ler_json(overrides) == {"s3_access_key_id": "AKIAFAKE123", "s3_secret_access_key": "segredo/com+simbolos"}
    job = (bundle / extrair_chaves_s3.JOB).read_text(encoding="utf-8")
    assert "AKIAFAKE123" not in job
    assert "${var.s3_access_key_id}" in job


def test_main_preserva_outros_overrides(bundle):
    """main: mantém as outras variáveis que já estavam no variable-overrides.json"""
    overrides = bundle / extrair_chaves_s3.OVERRIDES
    overrides.parent.mkdir(parents=True)
    overrides.write_text(json.dumps({"catalog": "lakehouse_vertice"}), encoding="utf-8")

    extrair_chaves_s3.main(bundle)

    assert ler_json(overrides)["catalog"] == "lakehouse_vertice"


def test_main_rodar_duas_vezes_nao_perde_as_chaves(bundle):
    """main: rodar duas vezes para com erro e não perde as chaves nem mexe no job"""
    extrair_chaves_s3.main(bundle)
    job_depois_da_primeira = (bundle / extrair_chaves_s3.JOB).read_text(encoding="utf-8")

    with pytest.raises(SystemExit, match="já foram extraídas"):
        extrair_chaves_s3.main(bundle)

    assert ler_json(bundle / extrair_chaves_s3.OVERRIDES)["s3_access_key_id"] == "AKIAFAKE123"
    assert (bundle / extrair_chaves_s3.JOB).read_text(encoding="utf-8") == job_depois_da_primeira


def test_main_sem_job(tmp_path):
    """main: sem resources/ingestão.job.yml encerra dizendo o que faltou"""
    with pytest.raises(SystemExit, match="não achei"):
        extrair_chaves_s3.main(tmp_path)
