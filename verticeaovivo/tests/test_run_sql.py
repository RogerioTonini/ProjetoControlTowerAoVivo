import json
import subprocess

import pytest

from tests.apoio import carregar_script

run_sql = carregar_script("run_sql")


# ---------- dividir ----------


@pytest.mark.parametrize(
    ("sql", "esperado"),
    [
        pytest.param("SELECT 1; SELECT 2;", ["SELECT 1", "SELECT 2"], id="ponto-e-virgula"),
        pytest.param("SELECT 1;\nSELECT 2", ["SELECT 1", "SELECT 2"], id="ultima-sem-ponto-e-virgula"),
        pytest.param("SELECT 'a;b'; SELECT 2", ["SELECT 'a;b'", "SELECT 2"], id="string"),
        pytest.param("SELECT 'it''s; ok'; SELECT 2", ["SELECT 'it''s; ok'", "SELECT 2"], id="aspas-escapadas"),
        pytest.param(
            "-- comentário; com ponto e vírgula\nSELECT 1; SELECT 2",
            ["-- comentário; com ponto e vírgula\nSELECT 1", "SELECT 2"],
            id="comentario",
        ),
        pytest.param("-- don't\nSELECT 1; SELECT 2", ["-- don't\nSELECT 1", "SELECT 2"], id="aspas-em-comentario"),
        pytest.param(
            "CREATE VIEW v WITH METRICS LANGUAGE YAML AS $$\nversion: 0.1\nsource: a;b\n$$; SELECT 2",
            ["CREATE VIEW v WITH METRICS LANGUAGE YAML AS $$\nversion: 0.1\nsource: a;b\n$$", "SELECT 2"],
            id="bloco-dolar",
        ),
        pytest.param(
            "CREATE VIEW v AS $$\nmeasures:\n  - name: total\n    expr: SUM(x)\n$$",
            ["CREATE VIEW v AS $$\nmeasures:\n  - name: total\n    expr: SUM(x)\n$$"],
            id="indentacao-no-bloco-dolar",
        ),
        pytest.param("SELECT 1;;\n  ;\n-- só comentário\n;", ["SELECT 1"], id="vazias-ou-so-comentario"),
        pytest.param("", [], id="arquivo-vazio"),
    ],
)
def test_dividir(sql, esperado):
    """dividir: separa o .sql em statements"""
    assert run_sql.dividir(sql) == esperado


# ---------- cli ----------


def processo(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


def test_cli_monta_comando_e_le_json(monkeypatch):
    """cli: chama o databricks com --profile e -o json e lê o JSON"""
    chamadas = []

    def fake_run(cmd, **kwargs):
        chamadas.append(cmd)
        return processo(stdout='{"ok": true}')

    monkeypatch.setattr(run_sql.subprocess, "run", fake_run)

    assert run_sql.cli(["warehouses", "list"], "DEFAULT") == {"ok": True}
    assert chamadas == [["databricks", "warehouses", "list", "--profile", "DEFAULT", "-o", "json"]]


def test_cli_saida_vazia_vira_dict_vazio(monkeypatch):
    """cli: saída vazia vira {}"""
    monkeypatch.setattr(run_sql.subprocess, "run", lambda cmd, **kw: processo(stdout=""))
    assert run_sql.cli(["x"], "DEFAULT") == {}


@pytest.mark.parametrize(
    ("stdout", "stderr", "mensagem"),
    [
        pytest.param("", "  auth falhou \n", "^auth falhou$", id="usa-stderr"),
        pytest.param("erro no stdout", "", "erro no stdout", id="sem-stderr-usa-stdout"),
    ],
)
def test_cli_erro_levanta_runtimeerror(monkeypatch, stdout, stderr, mensagem):
    """cli: erro do databricks levanta RuntimeError com a mensagem"""
    monkeypatch.setattr(run_sql.subprocess, "run", lambda cmd, **kw: processo(1, stdout, stderr))
    with pytest.raises(RuntimeError, match=mensagem):
        run_sql.cli(["x"], "DEFAULT")


# ---------- warehouse_padrao ----------


@pytest.mark.parametrize(
    "resposta",
    [
        pytest.param([{"id": "wh1"}, {"id": "wh2"}], id="lista"),
        pytest.param({"warehouses": [{"id": "wh1"}]}, id="objeto"),
    ],
)
def test_warehouse_padrao_pega_o_primeiro(monkeypatch, resposta):
    """warehouse_padrao: pega o primeiro warehouse da lista"""
    monkeypatch.setattr(run_sql, "cli", lambda args, profile: resposta)
    assert run_sql.warehouse_padrao("DEFAULT") == "wh1"


@pytest.mark.parametrize(
    "resposta",
    [
        pytest.param([], id="lista-vazia"),
        pytest.param({}, id="objeto-vazio"),
        pytest.param({"warehouses": []}, id="warehouses-vazio"),
    ],
)
def test_warehouse_padrao_sem_warehouse_encerra(monkeypatch, resposta):
    """warehouse_padrao: sem warehouse encerra com mensagem"""
    monkeypatch.setattr(run_sql, "cli", lambda args, profile: resposta)
    with pytest.raises(SystemExit, match="nenhum SQL warehouse"):
        run_sql.warehouse_padrao("DEFAULT")


# ---------- executar ----------


def test_executar_envia_statement_e_espera_terminar(monkeypatch):
    """executar: envia a statement e consulta até sair de PENDING/RUNNING"""
    respostas = iter(
        [
            {"statement_id": "s1", "status": {"state": "PENDING"}},
            {"statement_id": "s1", "status": {"state": "RUNNING"}},
            {"statement_id": "s1", "status": {"state": "SUCCEEDED"}},
        ]
    )
    chamadas = []

    def fake_cli(args, profile):
        chamadas.append(args)
        return next(respostas)

    monkeypatch.setattr(run_sql, "cli", fake_cli)
    monkeypatch.setattr(run_sql.time, "sleep", lambda s: None)

    r = run_sql.executar("SELECT 1", "wh1", "DEFAULT")

    assert r["status"]["state"] == "SUCCEEDED"
    assert chamadas[0][:3] == ["api", "post", "/api/2.0/sql/statements"]
    assert json.loads(chamadas[0][4]) == {
        "warehouse_id": "wh1",
        "statement": "SELECT 1",
        "wait_timeout": "50s",
        "on_wait_timeout": "CONTINUE",
    }
    assert chamadas[1:] == [["api", "get", "/api/2.0/sql/statements/s1"]] * 2


def test_executar_sem_espera_quando_ja_terminou(monkeypatch):
    """executar: não espera quando a statement já terminou"""
    monkeypatch.setattr(run_sql, "cli", lambda args, profile: {"statement_id": "s1", "status": {"state": "FAILED"}})
    monkeypatch.setattr(run_sql.time, "sleep", lambda s: pytest.fail("não deveria esperar"))
    assert run_sql.executar("SELECT 1", "wh1", "DEFAULT")["status"]["state"] == "FAILED"


# ---------- imprimir ----------


def resultado(colunas, linhas):
    return {"manifest": {"schema": {"columns": [{"name": c} for c in colunas]}}, "result": {"data_array": linhas}}


def test_imprimir_cabecalho_e_linhas_com_null(capsys):
    """imprimir: mostra cabeçalho e linhas, NULL em branco"""
    run_sql.imprimir(resultado(["a", "b"], [["1", None], ["2", "x"]]))
    assert capsys.readouterr().out == "  a | b\n  1 | \n  2 | x\n"


def test_imprimir_corta_no_limite(capsys):
    """imprimir: corta no limite e mostra o total de linhas"""
    run_sql.imprimir(resultado(["n"], [[str(i)] for i in range(5)]), limite=2)
    assert capsys.readouterr().out == "  n\n  0\n  1\n  ... (5 linhas)\n"


@pytest.mark.parametrize(
    "r",
    [
        pytest.param({}, id="sem-manifest"),
        pytest.param(resultado([], [["1"]]), id="sem-colunas"),
        pytest.param(resultado(["a"], []), id="sem-linhas"),
        pytest.param(resultado(["a"], None), id="data-array-nulo"),
    ],
)
def test_imprimir_sem_colunas_ou_linhas_nao_imprime(capsys, r):
    """imprimir: sem colunas ou sem linhas não imprime nada"""
    run_sql.imprimir(r)
    assert capsys.readouterr().out == ""


# ---------- main ----------


@pytest.fixture
def arquivo_sql(tmp_path):
    arquivo = tmp_path / "teste.sql"
    arquivo.write_text("-- cabeçalho\nSELECT 1;\nSELECT 2;\nSELECT 3;", encoding="utf-8")
    return arquivo


@pytest.fixture
def rodar(monkeypatch, arquivo_sql):
    """Roda main() com um executar falso que devolve os estados na ordem; retorna (código, statements executadas)."""

    def _rodar(estados, *flags):
        executadas = []
        estados = iter(estados)

        def fake_executar(stmt, wh, profile):
            executadas.append((stmt, wh, profile))
            estado = next(estados)
            if isinstance(estado, Exception):
                raise estado
            r = {"status": {"state": estado}}
            if estado != "SUCCEEDED":
                r["status"]["error"] = {"message": "deu ruim"}
            return r

        monkeypatch.setattr(run_sql, "executar", fake_executar)
        monkeypatch.setattr("sys.argv", ["run_sql.py", str(arquivo_sql), "--profile", "DEFAULT", *flags])
        return run_sql.main(), executadas

    monkeypatch.setattr(run_sql, "warehouse_padrao", lambda profile: "wh-padrao")
    return _rodar


def test_main_tudo_ok(rodar, capsys):
    """main: executa todas as statements no warehouse padrão e sai com 0"""
    codigo, executadas = rodar(["SUCCEEDED"] * 3)

    assert codigo == 0
    assert [s for s, _, _ in executadas] == ["-- cabeçalho\nSELECT 1", "SELECT 2", "SELECT 3"]
    assert all(wh == "wh-padrao" and profile == "DEFAULT" for _, wh, profile in executadas)
    saida = capsys.readouterr().out
    assert "3 statement(s) · warehouse wh-padrao" in saida
    assert "[1/3] SELECT 1" in saida  # o título pula o comentário


def test_main_usa_warehouse_informado(rodar, monkeypatch):
    """main: com --warehouse usa o informado e não lista os warehouses"""
    monkeypatch.setattr(run_sql, "warehouse_padrao", lambda profile: pytest.fail("não deveria listar"))
    _, executadas = rodar(["SUCCEEDED"] * 3, "--warehouse", "wh-x")
    assert {wh for _, wh, _ in executadas} == {"wh-x"}


def test_main_para_na_primeira_falha(rodar, capsys):
    """main: para na primeira statement que falha e sai com 1"""
    codigo, executadas = rodar(["SUCCEEDED", "FAILED", "SUCCEEDED"])

    assert codigo == 1
    assert len(executadas) == 2
    assert "FALHOU: deu ruim" in capsys.readouterr().out


def test_main_continuar_segue_depois_da_falha(rodar):
    """main: com --continuar executa tudo mesmo com falha e sai com 0"""
    codigo, executadas = rodar(["FAILED", "SUCCEEDED", "SUCCEEDED"], "--continuar")

    assert len(executadas) == 3
    assert codigo == 0


def test_main_erro_do_cli_vira_falha(rodar, capsys):
    """main: erro do databricks (RuntimeError) conta como falha"""
    codigo, executadas = rodar([RuntimeError("sem permissão")])

    assert codigo == 1
    assert len(executadas) == 1
    assert "FALHOU: sem permissão" in capsys.readouterr().out


def test_main_quiet_nao_imprime_resultado(rodar, monkeypatch):
    """main: com --quiet não imprime o resultado das queries"""
    monkeypatch.setattr(run_sql, "imprimir", lambda r: pytest.fail("não deveria imprimir"))
    codigo, _ = rodar(["SUCCEEDED"] * 3, "--quiet")
    assert codigo == 0


def test_main_profile_obrigatorio(monkeypatch, arquivo_sql):
    """main: sem --profile encerra"""
    monkeypatch.setattr("sys.argv", ["run_sql.py", str(arquivo_sql)])
    with pytest.raises(SystemExit):
        run_sql.main()
