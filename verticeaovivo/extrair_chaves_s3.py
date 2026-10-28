"""Tira as chaves do data lake do YAML do job e grava em variable-overrides.json (fora do Git).

Rode na pasta do bundle (cd ~/projetos/vertice), depois do generate:
    python3 extrair_chaves_s3.py
"""
import json
import pathlib
import re

arquivo = pathlib.Path("resources/ingestão.job.yml")
assert arquivo.exists(), "não achei resources/ingestão.job.yml: rode na pasta do bundle (cd ~/projetos/vertice) e depois do generate"
yml = arquivo.read_text(encoding="utf-8")
chaves = {"s3_access_key_id": "AWS_ACCESS_KEY_ID", "s3_secret_access_key": "AWS_SECRET_ACCESS_KEY"}
valores = {}
for var, param in chaves.items():
    valores[var] = re.search(rf"{param}: (.+)", yml).group(1).strip().strip("\"'")
    yml = re.sub(rf"{param}: .+", f"{param}: ${{var.{var}}}", yml)
yml = "variables:\n" + "".join(f"  {v}:\n    description: chave do data lake (o valor fica fora do Git)\n" for v in chaves) + "\n" + yml
arquivo.write_text(yml, encoding="utf-8")
pasta = pathlib.Path(".databricks/bundle/dev")
pasta.mkdir(parents=True, exist_ok=True)
(pasta / "variable-overrides.json").write_text(json.dumps(valores), encoding="utf-8")
print("ok: as chaves saíram do YAML e foram para", pasta / "variable-overrides.json")
