#!/usr/bin/env python3
"""Renomeia com segurança a chave de um projeto no ~/.claude.json.

Uso: rename_claude_json_key.py <caminho-antigo> <caminho-novo>

Nunca use sed no ~/.claude.json — este script renomeia SÓ a chave em
projects{} e grava atomicamente (tmp + os.replace).
"""
import json
import os
import sys


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    old, new = sys.argv[1], sys.argv[2]
    path = os.path.expanduser("~/.claude.json")

    with open(path) as f:
        data = json.load(f)

    projects = data.get("projects", {})
    if old not in projects:
        print(f"OK (nada a fazer): chave não existe: {old}")
        return 0
    if new in projects:
        print(f"ERRO: a chave nova já existe, resolva manualmente: {new}")
        return 1

    projects[new] = projects.pop(old)

    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)

    # relê pra confirmar que o arquivo continua JSON válido
    with open(path) as f:
        check = json.load(f)
    assert new in check["projects"] and old not in check["projects"]
    print(f"OK: {old} -> {new}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
