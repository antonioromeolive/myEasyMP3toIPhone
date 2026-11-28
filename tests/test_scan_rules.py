# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""I controlli rifatti con checks_requirements.md: un modo solo di dire "uguale" (names), la grafia che vince (D-1,
D-2, D-3), le regole nuove R18-R31, i livelli (ogni passo vede le correzioni di quelli prima) e Applica che segue
l'ordine dei passi. Brani in memoria, nomi e valori inventati."""

from pathlib import Path

from myeasymp3toiphone import accepted, check_flow, names, scan, scan_rules
from myeasymp3toiphone.library import Track
from myeasymp3toiphone.tags import TrackTags


def _track(path: str, error: str = "", **values) -> Track:
    result = Track(path=Path("C:/Musica") / path, tags=TrackTags(**values), error=error)
    return result


def _rules(tracks: list, context: list = None, check_files: bool = False) -> dict:
    """{regola senza il numero: [problemi]} dei controlli sul PC."""
    result = {}
    for issue in scan.rule_issues(tracks, check_files=check_files, context=context):
        result.setdefault(issue.rule_id.split(".")[0], []).append(issue)
    return result


def _changes(issue) -> dict:
    result = {}
    for path, values in issue.fix.changes:
        result[Path(path).name] = values
    return result


# --------------------------------------------------------------------------- names

def test_one_way_to_say_equal_with_explicit_levels():
    assert names.fold("  Pink   Floyd ", names.LEVEL_SPACES) == "Pink Floyd"
    assert names.fold("Pérez", names.LEVEL_CASE) == "pérez"
    assert names.fold("Pérez", names.LEVEL_ACCENTS) == "perez"
    assert names.fold("AC/DC", names.LEVEL_PUNCT) == "ac dc"
    assert names.fold("The Battiato Franco", names.LEVEL_WORDS) == names.fold("Franco Battiato", names.LEVEL_WORDS)
    assert names.fold("e\u0301", names.LEVEL_SPACES) == "\u00e9"            # la stessa "é" salvata in due modi


def test_capital_initials_d1():
    assert names.capital_initials("Franco Battiato")
    assert names.capital_initials("Elio e le Storie Tese")                  # le parole corte sono libere
    assert names.capital_initials("McCartney")
    assert not names.capital_initials("franco battiato")
    assert not names.capital_initials("Franco battiato")
    assert not names.capital_initials("FRANCO BATTIATO")                    # tutto maiuscolo: dopo
    assert not names.capital_initials("xtc")
    assert names.capital_rank("AC/DC") == 1 and names.capital_rank("queen") == 2


def test_which_spelling_wins():
    counts = {"franco battiato": 10, "FRANCO BATTIATO": 3, "Franco Battiato": 1}
    assert names.choose_spelling(list(counts), counts).spelling == "Franco Battiato"      # iniziali maiuscole
    counts = {"QUEEN": 5, "queen": 9}
    assert names.choose_spelling(list(counts), counts).spelling == "QUEEN"                # meglio tutto maiuscolo
    counts = {"Lucio Dalla": 2, "Lucio Dalla ": 7}
    assert names.choose_spelling(list(counts), counts).spelling == "Lucio Dalla "          # la più usata
    assert names.choose_spelling(["Uno Due", "Uno Tre"], {"Uno Tre": 1, "Uno Due": 1}).spelling == "Uno Due"
    assert names.choose_spelling(["AA.VV.", "Artisti Vari"], policy=names.POLICY_FIRST).spelling == "Artisti Vari"
    choice = names.choose_spelling(["Perez", "Pérez"], {"Perez": 9, "Pérez": 1})
    assert choice.spelling == "Pérez" and not choice.accents_differ                       # vince l'accento (D-3)
    choice = names.choose_spelling(["Perchè", "Perché"], {"Perchè": 3, "Perché": 1})
    assert choice.spelling == "Perchè" and choice.accents_differ                          # da controllare
    counts = {"la voce del padrone": 3, "La Voce Del Padrone": 1}
    assert names.choose_spelling(list(counts), counts, capitals=False).spelling == "la voce del padrone"


def test_garbled_text_is_repaired():
    assert names.repaired_mojibake("PerchÃ©") == "Perché"
    assert names.repaired_mojibake("CittÃ  vuota") == "Città vuota"     # "à" letta come Windows-1252
    assert names.repaired_mojibake("Perché") == "" and names.repaired_mojibake("Queen") == ""


# --------------------------------------------------------------------------- livelli 1 e 2

def test_files_formats_and_long_paths():
    tracks = [_track("A/Disco/01.mp3", title="Uno", artist="A", album="Disco"),
              _track("A/Disco/02.ogg", title="Due", artist="A", album="Disco"),
              _track("A/Disco/03.wma", title="Tre", artist="A", album="Disco"),
              _track("A/" + "x" * 250 + "/04.mp3", error="non trovato", title="Quattro", artist="A", album="Disco")]
    found = _rules(tracks, check_files=True)      # i file non ci sono: R2 e R3 non trovano niente
    assert found["R18"][0].title.endswith("(OGG 1, WMA 1)") and len(found["R18"][0].files) == 2
    assert found["R19"][0].rule_id == "R19.1" and found["R19"][0].severity == scan.SEVERITY_HIGH
    assert "R5" not in found                         # il percorso troppo lungo lo spiega R19, non "illeggibile"


def test_track_fields_placeholders_prefixes_spaces_and_garbled_letters():
    tracks = [_track("Gruppo/Disco/01 - Alba.mp3", title="Track 01", artist="Unknown Artist", album="Disco",
                     track_number=1),
              _track("Gruppo/Disco/02.mp3", title="02 - Sera", artist="Gruppo", album="Disco", track_number=2),
              _track("Gruppo/Disco/03.mp3", title="Gruppo - Notte", artist="Gruppo", album="Disco", track_number=3),
              _track("Gruppo/Disco/04.mp3", title="Luna ", artist="Gruppo", album="Disco", track_number=4),
              _track("Gruppo/Disco/05.mp3", title="PerchÃ©", artist="Gruppo", album="Disco", track_number=5),
              _track("Gruppo/Disco/06.mp3", title="Citt\ufffd", artist="Gruppo", album="Disco", track_number=6)]
    found = _rules(tracks)
    assert _changes(found["R6"][0])["01 - Alba.mp3"] == {"artist": "Gruppo", "title": "Alba"}
    assert _changes(found["R20"][0]) == {"02.mp3": {"title": "Sera"}, "03.mp3": {"title": "Notte"}}
    assert _changes(found["R21"][0]) == {"04.mp3": {"title": "Luna"}}
    garbled = {issue.rule_id: issue for issue in found["R22"]}
    assert _changes(garbled["R22.1"]) == {"05.mp3": {"title": "Perché"}}
    assert garbled["R22.2"].fix is None and [p.name for p in garbled["R22.2"].files] == ["06.mp3"]


# --------------------------------------------------------------------------- livello 3: nomi in tutta la musica

def test_one_spelling_per_name_in_all_the_music():
    chosen = [_track("a/1.mp3", title="Uno", artist="franco battiato", album="Primo")]
    rest = [_track(f"b/{n}.mp3", title=f"B{n}", artist="Franco Battiato", album="Secondo") for n in range(3)]
    rest += [_track("c/1.mp3", title="C", artist="Rino Gaetano", album="Terzo"),
             _track("c/2.mp3", title="D", artist="rino gaetano", album="Terzo")]
    found = _rules(chosen, context=chosen + rest)
    spellings = found["R23"]
    assert len(spellings) == 1                       # Rino Gaetano non tocca i brani controllati
    assert _changes(spellings[0]) == {"1.mp3": {"artist": "Franco Battiato"}}
    assert spellings[0].fix.description == "Scrivi ovunque \"Franco Battiato\""


def test_different_accents_are_flagged_to_check():
    tracks = [_track("a/1.mp3", title="Uno", artist="Perchè Band", album="X"),
              _track("b/1.mp3", title="Due", artist="Perché Band", album="Y")]
    issue = _rules(tracks)["R23"][0]
    assert issue.title.startswith("Accenti diversi") and issue.severity == scan.SEVERITY_LOW


def test_artist_variants_look_at_the_track_artist_too():
    tracks = [_track("q/1.mp3", title="Uno", artist="Queen", album_artist="Queen", album="Live"),
              _track("q/2.mp3", title="Due", artist="Queen", album_artist="Queen", album="Live"),
              _track("q/3.mp3", title="Tre", artist="The Queen", album_artist="Queen", album="Live")]
    issue = _rules(tracks)["R14"][0]
    assert _changes(issue) == {"3.mp3": {"artist": "Queen"}}                 # REQ-18: l'artista del brano


# --------------------------------------------------------------------------- livello 4: coerenza dell'album

def test_album_artist_identical_on_every_track_d1():
    tracks = [_track("r/1.mp3", title="Uno", artist="Rossi", album_artist="AA.VV.", album="Estate", compilation=True),
              _track("r/2.mp3", title="Due", artist="Bianchi", album_artist="Artisti Vari", album="Estate",
                     compilation=True),
              _track("r/3.mp3", title="Tre", artist="Verdi", album_artist="Artisti Vari", album="Estate",
                     compilation=True)]
    issue = _rules(tracks)["R25"][0]
    assert _changes(issue) == {"1.mp3": {"album_artist": "Artisti Vari"}}
    assert issue.severity == scan.SEVERITY_HIGH


def test_album_artist_filled_from_the_single_artist():
    plain = [_track(f"s/{n}.mp3", title=f"T{n}", artist="Solista", album="Solo") for n in range(2)]
    wrong = [_track(f"v/{n}.mp3", title=f"T{n}", artist="Cantante", album_artist="AA.VV.", album="Falsa Raccolta",
                    compilation=True) for n in range(2)]
    found = {issue.title: issue for issue in _rules(plain + wrong)["R26"]}
    empty = found["Solista — Solo: senza artista dell'album"]
    assert all(values == {"album_artist": "Solista"} for values in _changes(empty).values())
    various = [issue for title, issue in found.items() if "Falsa Raccolta" in title][0]
    assert all(values == {"album_artist": "Cantante", "compilation": False} for values in _changes(various).values())


def test_compilation_flag_follows_the_album_artist():
    tracks = [_track("c/1.mp3", title="Uno", artist="Rossi", album_artist="Artisti Vari", album="Hit", compilation=True),
              _track("c/2.mp3", title="Due", artist="Bianchi", album_artist="Artisti Vari", album="Hit")]
    issue = _rules(tracks)["R27"][0]
    assert _changes(issue) == {"2.mp3": {"compilation": True}} and "1 brani su 2" in issue.title


def test_albums_the_iphone_would_merge():
    tracks = [_track("r1/1.mp3", title="Uno", artist="Coro", album="Raccolta 01", track_number=1),
              _track("r1/2.mp3", title="Due", artist="Coro", album="Raccolta 01", track_number=2),
              _track("r2/1.mp3", title="Tre", artist="Coro", album="Raccolta 1", track_number=3)]
    issue = _rules(tracks)["R28"][0]
    assert _changes(issue) == {"1.mp3": {"album": "Raccolta 01"}}         # r2/1.mp3: il nome più usato


def test_disc_numbers_and_totals():
    tracks = [_track("d/1.mp3", title="Uno", artist="Duo", album="Doppio", track_number=1, track_total=2,
                     disc_number=1),
              _track("d/2.mp3", title="Due", artist="Duo", album="Doppio", track_number=2, track_total=2,
                     disc_number=1),
              _track("d/3.mp3", title="Tre", artist="Duo", album="Doppio", track_number=3, track_total=12,
                     disc_number=2),
              _track("d/4.mp3", title="Quattro", artist="Duo", album="Doppio", track_number=4, track_total=3)]
    found = _rules(tracks)
    assert "non ha il numero del disco" in found["R30"][0].detail and found["R30"][0].severity != scan.SEVERITY_INFO
    assert "Quattro (traccia 4 di 3)" in found["R34"][0].detail and found["R34"][0].severity == scan.SEVERITY_INFO
    assert _changes(found["R31"][0]) == {"4.mp3": {"track_total": 2}}       # disco 1: il totale più frequente
    assert found["R31"][0].severity == scan.SEVERITY_INFO                    # sull'iPhone non cambia niente


def test_split_folder_keeps_the_disc_number():
    tracks = [_track("Live/1.mp3", title="Uno", artist="Rossi", album="Live (CD 1)", track_number=1),
              _track("Live/2.mp3", title="Due", artist="Bianchi", album="Live (CD 2)", track_number=1)]
    issue = _rules(tracks)["R11"][0]
    assert _changes(issue)["2.mp3"]["disc_number"] == 2 and _changes(issue)["2.mp3"]["album"] == "Live"


# --------------------------------------------------------------------------- livello 6

def test_same_number_different_titles():
    tracks = [_track("gh1/1.mp3", title="Alba", artist="Gruppo", album="Greatest Hits", track_number=1),
              _track("gh2/1.mp3", title="Sera", artist="Gruppo", album="Greatest Hits", track_number=1),
              _track("gh2/1.flac", title="Notte", artist="Gruppo", album="Greatest Hits", track_number=2)]
    issue = _rules(tracks)["R29"][0]
    assert "1 numeri di traccia" in issue.title and "2 cartelle" in issue.detail and issue.fix is None


# --------------------------------------------------------------------------- livelli e Applica

def test_each_step_sees_the_fixes_before_it_and_apply_follows_the_steps():
    tracks = [_track("q/1.mp3", title="Uno", artist="queen ", album="Live"),
              _track("q/2.mp3", title="Due", artist="Queen", album="Live"),
              _track("q/3.mp3", title="Tre", artist="Queen", album="Live")]
    issues = scan.rule_issues(tracks, check_files=False)
    by_rule = {issue.rule_id.split(".")[0]: issue for issue in issues}
    assert by_rule["R21"].step < by_rule["R23"].step
    assert _changes(by_rule["R21"]) == {"1.mp3": {"artist": "queen"}}
    assert _changes(by_rule["R23"]) == {"1.mp3": {"artist": "Queen"}}      # parte da "queen", già senza spazio
    targets = {}

    def resolve(path):
        if str(path) not in targets:
            track = [t for t in tracks if str(t.path) == str(path)][0]
            targets[str(path)] = check_flow.Target(track, pc=track)
        return targets[str(path)]

    entries = check_flow.group_by_album([by_rule["R23"], by_rule["R21"]], resolve)   # il passo dopo prima
    rows = []
    for entry in entries:
        rows += entry.rows()
    plan = check_flow.plan_apply(rows)
    assert plan.pc[0][1] == {"artist": "Queen"} and plan.conflicts == []


def test_conflicting_fixes_of_the_same_step_are_reported():
    track = _track("x/1.mp3", title="Uno", album="Disco")
    target = check_flow.Target(track, pc=track)
    rows = [check_flow.Row(target, "album", "Disco", "Disco A", 0, 5),
            check_flow.Row(target, "album", "Disco", "Disco B", 1, 5)]
    plan = check_flow.plan_apply(rows)
    assert plan.pc[0][1] == {"album": "Disco B"}
    assert plan.conflicts == [("Uno", "Album", ["Disco A", "Disco B"])]


def test_case_only_differences_are_fixes_now():
    track = _track("x/1.mp3", title="uno", album="Disco")
    issue = scan.Issue(scan.KIND_NAMES, scan.SEVERITY_LOW, "t", "d", [track.path],
                       scan.Fix(scan.FIX_TAGS, "f", changes=[(track.path, {"title": "Uno"})]), rule_id="R23.1")
    entries = check_flow.group_by_album([issue], lambda path: check_flow.Target(track, pc=track))
    assert [(row.old, row.new) for row in entries[0].rows()] == [("uno", "Uno")]


def test_fine_for_the_whole_album_does_not_hide_spellings(tmp_path):
    store = accepted.Accepted(tmp_path)
    store.accept(("Queen", "Live"), accepted.WHOLE_ALBUM)
    assert store.is_accepted(("Queen", "Live"), "R9")
    assert not store.is_accepted(("Queen", "Live"), "R23")
    store.accept(("Queen", "Live"), "R23")
    assert store.is_accepted(("queen", "live"), "R23")


def test_new_rules_only_on_the_pc():
    tracks = [_track("q/1.mp3", title="Uno ", artist="queen", album="Live"),
              _track("q/2.mp3", title="Due", artist="Queen", album="Live")]
    rules = set()
    for issue in scan.rule_issues(tracks, check_files=False, pc=False):
        rules.add(issue.rule_id.split(".")[0])
    assert not rules & {"R21", "R23", "R25", "R26", "R27"}
    assert scan_rules.SUPPORTED_MUSIC == (".mp3", ".flac", ".m4a")


def test_short_words_in_lowercase_win_d10():
    counts = {"Frankie Goes To Hollywood": 5, "Frankie Goes to Hollywood": 2}
    assert names.choose_spelling(list(counts), counts).spelling == "Frankie Goes to Hollywood"
    counts = {"Tears For Fears": 9, "Tears for Fears": 1, "TEARS FOR FEARS": 3}
    assert names.choose_spelling(list(counts), counts).spelling == "Tears for Fears"
    counts = {"Elio E Le Storie Tese": 4, "Elio e le Storie Tese": 1}
    assert names.choose_spelling(list(counts), counts).spelling == "Elio e le Storie Tese"
    counts = {"The Who": 3, "the Who": 1}                    # la prima parola resta com'è
    assert names.choose_spelling(list(counts), counts).spelling == "The Who"


def test_rule_results_arrive_before_the_fingerprints():
    order = []
    tracks = [_track("q/1.mp3", title="Uno", artist="queen", album="Live", track_number=1),
              _track("q/2.mp3", title="Due", artist="Queen", album="Live", track_number=2)]

    def prints():
        order.append("impronte")
        return {}

    scan.scan_tracks(tracks, "PC", partial=lambda issues: order.append(f"risultati {len(issues)}"),
                     fingerprint_fn=prints)
    assert order[0].startswith("risultati") and order[0] != "risultati 0" and "impronte" in order
    order.clear()
    scan.scan_tracks(tracks, "PC", checks=frozenset({scan.CHECK_SPLIT}), fingerprint_fn=prints)
    assert order == []                                       # senza Brani duplicati le impronte non servono


def test_the_characters_that_change_are_highlighted():
    from myeasymp3toiphone.gui.check_results import diff_pieces
    old, new = diff_pieces("Frankie Goes to Hollywood", "Frankie Goes To Hollywood")
    assert [text for text, changed in old if changed] == ["t"]
    assert [text for text, changed in new if changed] == ["T"]
    assert "".join(text for text, _changed in new) == "Frankie Goes To Hollywood"


def test_a_compilation_with_the_numbers_of_the_original_albums():
    """Una raccolta con nei tag i numeri degli album originali (doppi, oltre il totale) e quelli giusti nei nomi dei
    file: R29 prende i numeri dai nomi, e R9 conta i brani mancanti su quelli (non "almeno 25" su 15)."""
    tags = [("01 - Uno", 13), ("04 - Due", 1), ("05 - Tre", 5), ("06 - Quattro", 15), ("09 - Cinque", 21),
            ("10 - Sei", 3), ("11 - Sette", 15), ("12 - Otto", 8), ("13 - Nove", 13), ("14 - Dieci", 3),
            ("15 - Undici", 1)]
    tracks = []
    for name, wrong in tags:
        tracks.append(_track(f"Raccolta/{name}.mp3", title=name[5:], artist=f"Cantante {name[5:]}",
                             album_artist="Artisti Vari", album="Raccolta Inverno", compilation=True,
                             track_number=wrong, track_total=15, disc_number=1, disc_total=1))
    found = _rules(tracks)
    clash = found["R29"][0]
    assert clash.fix.description == "Numero di traccia dal nome del file"
    assert _changes(clash)["09 - Cinque.mp3"] == {"track_number": 9}
    missing = found["R9"][0]
    assert "mancano 4 numeri di traccia (11 brani qui, l'album ne ha almeno 15)" in missing.title
    assert "2, 3, 7, 8" in missing.detail
    assert "R30" not in found                    # 21 di 15 non c'è più: il numero giusto è 9


def test_open_in_tagscanner(tmp_path, monkeypatch):
    from myeasymp3toiphone.gui import file_actions
    program = tmp_path / "Programmi" / "TagScanner"
    program.mkdir(parents=True)
    (program / "Tagscan.exe").write_bytes(b"")
    monkeypatch.setenv("ProgramFiles", str(tmp_path / "Programmi"))
    monkeypatch.setenv("ProgramFiles(x86)", str(tmp_path / "nessuno"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "nessuno"))
    assert file_actions.find_tagscan("") == program / "Tagscan.exe"                  # i posti soliti
    assert file_actions.find_tagscan(str(program)) == program / "Tagscan.exe"         # la cartella
    assert file_actions.find_tagscan(str(tmp_path / "altro.exe")) is None             # scelto e non c'è
    album = tmp_path / "Musica" / "Album"
    for disc in ("CD1", "CD2"):
        (album / disc).mkdir(parents=True)
    paths = [album / "CD1" / "01.mp3", album / "CD2" / "01.mp3"]
    assert file_actions.start_folder(paths) == str(album)                           # la cartella dell'album
    assert file_actions.start_folder(paths[:1]) == str(album / "CD1")
    started = []
    monkeypatch.setattr(file_actions.subprocess, "Popen", lambda arguments: started.append(arguments))
    assert file_actions.open_in_tagscan(program / "Tagscan.exe", paths) == str(album)
    assert started == [[str(program / "Tagscan.exe"), str(album)]]
    assert file_actions.open_in_tagscan(program / "Tagscan.exe", [tmp_path / "manca" / "x.mp3"]) == ""


def test_two_real_albums_with_a_common_name_are_not_a_split_compilation():
    tracks = [_track("s/1.mp3", title="Uno", artist="Supertramp", album_artist="Supertramp", album="Essentials",
                     year="2019"),
              _track("g/1.mp3", title="Due", artist="Gruppo", album_artist="Gruppo", album="Essentials", year="2005"),
              _track("r/1.mp3", title="Tre", artist="Rossi", album="Estate", year="1999"),
              _track("b/1.mp3", title="Quattro", artist="Bianchi", album="Estate", year="1999")]
    splits = _rules(tracks).get("R13", [])
    assert [issue.title for issue in splits] == ["\"Estate\" diviso tra 2 artisti"]      # solo la raccolta probabile


def _copy(folder: str, suffix: str, titles: list, artist: str = "Gruppo", album_artist: str = "Gruppo",
          album: str = "Ricordi") -> list:
    result = []
    for number, title in enumerate(titles, start=1):
        result.append(_track(f"{folder}/{number:02d} - {title}{suffix}", title=title, artist=artist,
                             album_artist=album_artist, album=album, track_number=number))
    return result


def test_the_worse_copy_of_an_album_is_a_duplicate(monkeypatch):
    rates = {"mp3_192": 192, "mp3_128": 128, "mp3_320": 320}
    monkeypatch.setattr(scan_rules, "mp3_bitrate", lambda track: rates[track.path.parent.name])
    flac = _copy("flac", ".flac", ["Alba", "Sera", "Notte"])
    mp3 = _copy("mp3_192", ".mp3", ["Alba", "Sera", "Notte", "Bonus"])
    found = _rules(flac + mp3)
    worse = found["R32"][0]
    assert "copia in MP3 192 kbps, c'è anche in FLAC" in worse.title
    assert len(worse.files) == 4 and "1 brano ci sono solo in questa copia (bonus)" in worse.detail
    assert worse.fix is None                                        # niente di automatico
    best = _copy("mp3_320", ".mp3", ["Alba", "Sera", "Notte"])
    assert "R32" not in _rules(flac + best)                         # FLAC e MP3 a 320: versioni, non si dice niente
    low = _copy("mp3_128", ".mp3", ["Alba", "Sera", "Notte"])
    found = _rules(mp3 + low)
    assert [issue.title.split(": ")[1] for issue in found["R32"]] == ["copia in MP3 128 kbps, c'è anche in MP3 192 kbps"]
    assert "R8" not in found                                        # i brani doppi li dice la copia, non uno per uno
    twice = _rules(flac + _copy("flac_bis", ".flac", ["Alba", "Sera", "Notte"]))["R33"][0]
    assert "l'album c'è due volte (FLAC)" in twice.title and len(twice.files) == 6


def test_two_compilations_with_the_same_name_are_not_copies(monkeypatch):
    monkeypatch.setattr(scan_rules, "mp3_bitrate", lambda track: 128 if "a" in track.path.parent.name else 320)
    first = _copy("a", ".mp3", ["Uno", "Due", "Tre"], artist="Rossi", album_artist="Artisti Vari", album="Hits")
    second = _copy("b", ".mp3", ["Quattro", "Cinque", "Sei"], artist="Bianchi", album_artist="Artisti Vari",
                   album="Hits")
    found = _rules(first + second)
    assert "R32" not in found and "R33" not in found and "R29" in found     # due raccolte diverse
    same = _copy("b", ".mp3", ["Uno", "Due", "Tre"], artist="Rossi", album_artist="Artisti Vari", album="Hits")
    assert "R32" in _rules(first + same)                            # le stesse canzoni: è la stessa raccolta


def test_the_catalog_disproves_a_split_compilation():
    tracks = [_track("s/1.mp3", title="Uno", artist="Supertramp", album="Essentials"),
              _track("g/1.mp3", title="Due", artist="Gruppo", album="Essentials")]
    split = _rules(tracks)["R13"][0]
    assert "Non verificato online" in split.detail and split.fix is not None
    release = type("R", (), {"artist": "Supertramp"})()
    result = type("A", (), {"release": release, "local_tracks": [tracks[0]]})()
    assert check_flow.drop_disproved_compilations([split], [result]) == []
    various = type("A", (), {"release": type("R", (), {"artist": "Various Artists"})(), "local_tracks": tracks})()
    assert check_flow.drop_disproved_compilations([split], [various]) == [split]
