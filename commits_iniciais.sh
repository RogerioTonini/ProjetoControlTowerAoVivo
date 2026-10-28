#!/usr/bin/env bash
# Commits iniciais do projeto (Conventional Commits) e push para o GitHub.
# Uso: bash commits_iniciais.sh  (na raiz do repositório)
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
P=verticeaovivo

# Adiciona apenas os caminhos que existem e commita somente se houver algo no stage.
commit() {
    local paths=() msg=()
    while [[ $# -gt 0 && $1 != "--" ]]; do paths+=("$1"); shift; done
    shift
    msg=("$@")

    local existentes=()
    for p in "${paths[@]}"; do
        if [[ -e $p ]]; then existentes+=("$p"); else echo "  (ignorado: $p não existe)"; fi
    done
    [[ ${#existentes[@]} -gt 0 ]] && git add -- "${existentes[@]}"

    if git diff --cached --quiet; then
        echo ">> Nada para commitar: ${msg[0]}"
        return
    fi
    local args=()
    for m in "${msg[@]}"; do args+=(-m "$m"); done
    git commit "${args[@]}"
}

# Segurança: não versionar credenciais em texto puro.
if grep -rqE 'AWS_SECRET_ACCESS_KEY:[[:space:]]*["'\'']?[^"'\''${[:space:]]' "$P/resources" 2>/dev/null; then
    echo "ERRO: credenciais AWS em texto puro em $P/resources/." >&2
    echo "Mova-as para um secret scope do Databricks antes de commitar." >&2
    exit 1
fi

commit "$P/.gitignore" "$P/.gitattributes" "$P/.githooks-scripts" "commits_iniciais.sh" -- \
    "chore(git): adicionar configurações do Git" \
    "- Adicionar .gitignore
- Adicionar .gitattributes para normalização de arquivos e tratamento de binários
- Adicionar script de commits iniciais"

commit "$P/.python-version" "$P/pyproject.toml" "$P/uv.lock" "$P/databricks.yml" -- \
    "build: configurar ambiente Python e Databricks" \
    "- Definir a versão do Python utilizada no projeto
- Configurar o uv e as dependências do projeto (pyproject.toml e uv.lock)
- Configurar o bundle da plataforma Databricks (databricks.yml)"

commit "$P/extrair_chaves_s3.py" -- \
    "chore(security): adicionar script para extrair as chaves do S3 do YAML do job" \
    "- Substituir as chaves do data lake por variáveis do bundle
- Gravar os valores em variable-overrides.json, fora do Git"

commit "$P/.vscode" -- \
    "chore(vscode): adicionar configurações do editor"

commit "$P/.claude" "$P/AGENTS.md" -- \
    "build: adicionar skills para o Claude e AGENTS.md"

commit "$P/app" "$P/resources" "$P/src" -- \
    "feat(app): adicionar estrutura base da aplicação"

commit "$P/tests" "$P/fixtures" -- \
    "test: adicionar estrutura de testes"

commit "README.md" "$P/docs" -- \
    "docs: adicionar README e documentação das aulas"

echo
git log --oneline

echo
git push -uf origin main
