# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""I testi dell'interfaccia da tradurre, estratti dal codice: ogni stringa e ogni f-string mostrata all'utente, come
modello con {0}, {1}… al posto delle parti variabili. Non si estraggono docstring, messaggi del log, query SQL,
espressioni regolari e i prompt dell'AI (già in inglese).

    .venv/Scripts/python tools/i18n_catalog.py            elenca i testi senza traduzione in i18n_en.CATALOG
    .venv/Scripts/python tools/i18n_catalog.py --json F   scrive in F tutti i testi (per tradurli)

Un test controlla che ogni testo abbia la sua traduzione inglese."""

import ast
import json
import re
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent / "myeasymp3toiphone"
SKIPPED_FILES = {"i18n.py", "i18n_en.py", "vscode_deploy.py"}
SKIPPED_NAMES = re.compile(r"(_SYSTEM|_SCHEMA|_QUERY|_PATTERN|_RE|SPLIT|MARKER|PREFIX|SUFFIX|NUMBERED_COPY|TITLE_EXTRA|"
                           r"_WORDS|STYLE_SHEET|USER_AGENT|HOST_REQUEST|_FORMAT|_FILE|_FOLDER|_NAME|_PATH|_ENV_VAR)$")
SKIPPED_CALLS = {"debug", "info", "warning", "error", "exception", "critical", "compile", "sub", "search", "match",
                 "fullmatch", "split", "findall", "finditer", "execute", "executescript", "setStyleSheet", "getLogger",
                 "strftime", "strptime", "get", "setdefault", "pop", "environ", "getenv", "join", "startswith",
                 "endswith", "replace", "setProperty", "setObjectName", "connect", "post", "send_plist", "Path",
                 "with_name", "with_suffix", "joinpath", "add_argument", "Formatter", "basicConfig", "addItem_data"}
TECHNICAL = re.compile(r"^\s*(SELECT|CREATE|INSERT|UPDATE|DELETE|PRAGMA|WITH)\b|^%\(|^\w+://|^[\s\W\d]*$")
WORD = re.compile(r"[A-Za-zÀ-ÿ'’]{3,}[.:…?!]*")
LETTER = re.compile(r"[A-Za-zÀ-ÿ]")


def _template(node) -> str:
    """Il modello di una stringa o f-string: le parti variabili diventano {0}, {1}…; le graffe vere si raddoppiano."""
    if isinstance(node, ast.Constant):
        result = node.value.replace("{", "{{").replace("}", "}}")
    else:
        result = ""
        number = 0
        for part in node.values:
            if isinstance(part, ast.Constant):
                result += part.value.replace("{", "{{").replace("}", "}}")
            else:
                result += "{" + str(number) + "}"
                number += 1
    return result


def _literal_text(node) -> str:
    if isinstance(node, ast.Constant):
        result = node.value
    else:
        result = ""
        for part in node.values:
            if isinstance(part, ast.Constant):
                result += part.value
    return result


class _Collector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.found = []
        self._skip = set()

    def _skip_subtree(self, node) -> None:
        for sub in ast.walk(node):
            self._skip.add(id(sub))

    def visit_Module(self, node) -> None:
        self._docstring(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node) -> None:
        self._docstring(node)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node) -> None:
        self._docstring(node)
        self.generic_visit(node)

    def _docstring(self, node) -> None:
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
            self._skip_subtree(node.body[0])

    def visit_Assign(self, node) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name) and SKIPPED_NAMES.search(target.id):
                self._skip_subtree(node.value)
        self.generic_visit(node)

    def visit_Call(self, node) -> None:
        name = ""
        if isinstance(node.func, ast.Attribute):
            name = node.func.attr
        elif isinstance(node.func, ast.Name):
            name = node.func.id
        if name in SKIPPED_CALLS:
            self._skip_subtree(node)
        self.generic_visit(node)

    def visit_Subscript(self, node) -> None:
        self._skip_subtree(node.slice)
        self.generic_visit(node)

    def visit_Compare(self, node) -> None:
        self._skip_subtree(node)
        self.generic_visit(node)

    def visit_Dict(self, node) -> None:
        for key in node.keys:
            if key is not None:
                self._skip_subtree(key)
        self.generic_visit(node)

    def visit_JoinedStr(self, node) -> None:
        if id(node) not in self._skip:
            self._add(node)
            self._skip_subtree(node)
        self.generic_visit(node)

    def visit_Constant(self, node) -> None:
        if id(node) not in self._skip and isinstance(node.value, str):
            self._add(node)

    def _add(self, node) -> None:
        text = _literal_text(node)
        token = text.strip()
        if LETTER.search(text) and not TECHNICAL.search(text) and (" " in token or WORD.fullmatch(token)):
            self.found.append(_template(node))


def templates() -> list:
    """Tutti i testi da tradurre, senza doppioni, nell'ordine in cui compaiono."""
    seen = []
    for path in sorted(PACKAGE.rglob("*.py")):
        if path.name not in SKIPPED_FILES:
            collector = _Collector()
            collector.visit(ast.parse(path.read_text(encoding="utf-8")))
            for text in collector.found:
                if text not in seen:
                    seen.append(text)
    return seen


def missing() -> list:
    sys.path.insert(0, str(PACKAGE.parent))
    from myeasymp3toiphone.i18n_en import CATALOG
    result = []
    for text in templates():
        if text not in CATALOG:
            result.append(text)
    return result


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--json":
        Path(sys.argv[2]).write_text(json.dumps(templates(), ensure_ascii=False, indent=0), encoding="utf-8")
        print(f"{len(templates())} testi")
    else:
        for item in missing():
            print(repr(item))
