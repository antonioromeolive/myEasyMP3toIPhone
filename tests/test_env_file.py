# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Il file delle variabili (parte 1 di "config and build specs.md"): nomi e valori inventati."""

import os

from myeasymp3toiphone import env_file


def _load(tmp_path, text: str, encoding: str = "utf-8") -> list:
    path = tmp_path / "test.env"
    path.write_text(text, encoding=encoding)
    result = env_file.load(path)
    return result


def test_file_value_beats_system(tmp_path, monkeypatch):
    monkeypatch.setenv("MY_TEST_A", "dal-sistema")
    warnings = _load(tmp_path, "MY_TEST_A=dal-file\n")
    assert os.environ["MY_TEST_A"] == "dal-file"
    assert env_file.source("MY_TEST_A") == "file"
    assert warnings == []


def test_empty_line_and_self_reference_leave_system(tmp_path, monkeypatch):
    monkeypatch.setenv("MY_TEST_A", "sistema-a")
    monkeypatch.setenv("MY_TEST_B", "sistema-b")
    warnings = _load(tmp_path, "MY_TEST_A=\nMY_TEST_B=$MY_TEST_B\n")
    assert os.environ["MY_TEST_A"] == "sistema-a"
    assert os.environ["MY_TEST_B"] == "sistema-b"
    assert env_file.source("MY_TEST_A") == "sistema"
    assert warnings == []


def test_reference_prefers_file_in_any_order_and_through_a_chain(tmp_path, monkeypatch):
    monkeypatch.setenv("MY_TEST_C", "sistema-c")
    warnings = _load(tmp_path, "MY_TEST_A=$MY_TEST_B\nMY_TEST_B=$MY_TEST_C\nMY_TEST_C=file-c\n")
    assert os.environ["MY_TEST_A"] == "file-c"
    assert os.environ["MY_TEST_B"] == "file-c"
    assert warnings == []


def test_reference_to_variable_left_to_system(tmp_path, monkeypatch):
    monkeypatch.setenv("MY_TEST_B", "sistema-b")
    _load(tmp_path, "MY_TEST_A=$MY_TEST_B\nMY_TEST_B=$MY_TEST_B\n")
    assert os.environ["MY_TEST_A"] == "sistema-b"


def test_double_dollar_is_literal_and_system_values_are_not_references(tmp_path, monkeypatch):
    monkeypatch.setenv("MY_TEST_B", "$MY_TEST_C")
    monkeypatch.setenv("MY_TEST_C", "non-usato")
    _load(tmp_path, "MY_TEST_A=$$testo\nMY_TEST_D=$MY_TEST_B\n")
    assert os.environ["MY_TEST_A"] == "$testo"
    assert os.environ["MY_TEST_D"] == "$MY_TEST_C"


def test_dollar_inside_a_value_is_ordinary(tmp_path):
    _load(tmp_path, "MY_TEST_A=ab$cd\n")
    assert os.environ["MY_TEST_A"] == "ab$cd"


def test_loop_and_dead_reference_warn_without_value(tmp_path, monkeypatch):
    monkeypatch.setenv("MY_TEST_A", "resta")
    warnings = _load(tmp_path, "MY_TEST_A=$MY_TEST_B\nMY_TEST_B=$MY_TEST_A\nMY_TEST_D=$MY_TEST_NESSUNA\n")
    assert os.environ["MY_TEST_A"] == "resta"
    assert "MY_TEST_D" not in os.environ
    text = " ".join(warnings)
    assert "MY_TEST_A" in text and "MY_TEST_D" in text and "ciclo" in text
    assert "MY_TEST_NESSUNA" not in text


def test_malformed_line_warns_with_number_not_text(tmp_path):
    warnings = _load(tmp_path, "# commento\nexport MY_TEST_A=segreto123\nMY_TEST_B=ok\n")
    assert os.environ["MY_TEST_B"] == "ok"
    assert any("2" in warning for warning in warnings)
    assert not any("segreto123" in warning for warning in warnings)


def test_home_variable_is_ignored(tmp_path, monkeypatch):
    before = os.environ["MYEASYMP3TOIPHONE_HOME"]
    warnings = _load(tmp_path, "MYEASYMP3TOIPHONE_HOME=C:\\altrove\n")
    assert os.environ["MYEASYMP3TOIPHONE_HOME"] == before
    assert any("MYEASYMP3TOIPHONE_HOME" in warning for warning in warnings)


def test_bom_quotes_last_wins_and_unreadable_file(tmp_path):
    warnings = _load(tmp_path, "MY_TEST_A = \"uno\"\nMY_TEST_A='due'\n", encoding="utf-8-sig")
    assert os.environ["MY_TEST_A"] == "due"
    assert warnings == []
    folder = tmp_path / "cartella.env"
    folder.mkdir()
    assert env_file.load(folder)  # una cartella non si legge: avviso, nessuna eccezione


def test_update_keeps_lines_adds_names_once_and_never_values(tmp_path, monkeypatch):
    monkeypatch.setenv("MY_TEST_USATA", "valore-di-sistema")
    template = tmp_path / "modello.env"
    template.write_text("# modello\nMY_TEST_UNO=\nMY_TEST_DUE=\n", encoding="utf-8")
    target = tmp_path / "home.env"
    target.write_text("MY_TEST_UNO=mio\n# MY_TEST_DUE=commentata\nALTRA=x\n", encoding="utf-8")
    env_file.update(target, template, ["MY_TEST_USATA"])
    env_file.update(target, template, ["MY_TEST_USATA"])
    text = target.read_text(encoding="utf-8")
    assert text.startswith("MY_TEST_UNO=mio\n# MY_TEST_DUE=commentata\nALTRA=x\n")
    assert text.count("MY_TEST_USATA=") == 1
    assert "MY_TEST_USATA=\n" in text
    assert "valore-di-sistema" not in text
    assert "MY_TEST_DUE=\n" not in text


def test_missing_file_is_created_from_template(tmp_path):
    template = tmp_path / "modello.env"
    template.write_text("MY_TEST_UNO=\n", encoding="utf-8")
    target = tmp_path / "home.env"
    messages = env_file.update(target, template, [])
    assert target.read_text(encoding="utf-8") == "MY_TEST_UNO=\n"
    assert messages


def test_template_lists_every_variable_empty():
    from myeasymp3toiphone.environment import VARIABLES
    values, bad = env_file.parse_lines(env_file.TEMPLATE_PATH.read_text(encoding="utf-8-sig").splitlines())
    assert bad == []
    assert all(value == "" for value in values.values())
    for name in VARIABLES:
        if name != "MYEASYMP3TOIPHONE_HOME":
            assert name in values
    assert "MYEASYMP3TOIPHONE_HOME" not in values
