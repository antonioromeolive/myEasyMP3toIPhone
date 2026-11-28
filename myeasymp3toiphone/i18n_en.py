# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""L'interfaccia in inglese: per ogni testo italiano del programma (come lo estrae tools/i18n_catalog.py, con {0},
{1}… al posto delle parti variabili) la traduzione inglese. Un testo nuovo nel codice va aggiunto qui: un test lo
controlla. I testi tecnici restano uguali."""

CATALOG = {
    "impronte dei brani dell'iPhone: {0} di {1}":
        "iPhone track fingerprints: {0} of {1}",
    "{0} | {1} | artist: {2} | album artist: {3} | album: {4} | {5}":
        "{0} | {1} | artist: {2} | album artist: {3} | album: {4} | {5}",
    "   {0} | {1} | artist: {2} | album artist: {3} | album: {4} | {5} | folder: {6}":
        "   {0} | {1} | artist: {2} | album artist: {3} | album: {4} | {5} | folder: {6}",
    "l'AI confronta {0} brani dubbi":
        "the AI compares {0} doubtful tracks",
    "TRACKS\n":
        "TRACKS\n",
    "AI ({0}): {1}":
        "AI ({0}): {1}",
    "impronte dei file del PC":
        "PC file fingerprints",
    "stesso audio":
        "same audio",
    "stesso audio (la preferita di {0} copie)":
        "same audio (the preferred of {0} copies)",
    "stessa durata, titolo e artista quasi uguali (audio diverso: forse un'altra codifica)":
        "same duration, almost the same title and artist (different audio: maybe another encoding)",
    "il più simile di {0} candidati: controlla":
        "the most similar of {0} candidates: check it",
    "stesso audio (impronta): certo":
        "same audio (fingerprint): certain",
    "titolo, artista e durata simili ({0})":
        "similar title, artist and duration ({0})",
    "high":
        "high",
    "mistral":
        "mistral",
    "La risposta dell'AI non è JSON valido: {0}":
        "The AI reply is not valid JSON: {0}",
    "La risposta dell'AI non è un oggetto JSON: {0}":
        "The AI reply is not a JSON object: {0}",
    "{0}: richiesta non riuscita ({1})":
        "{0}: request failed ({1})",
    "{0}: errore {1}: {2}":
        "{0}: error {1}: {2}",
    "{0}: la risposta non è quella di un'API {1} (indirizzo sbagliato?): {2}":
        "{0}: the reply is not from a {1} API (wrong address?): {2}",
    "Profilo {0}: nessun server ({1} non ha valore)":
        "Profile {0}: no server ({1} has no value)",
    "Bearer {0}":
        "Bearer {0}",
    "system":
        "system",
    "user":
        "user",
    "Ollama":
        "Ollama",
    "Ollama non raggiungibile su {0}: {1}":
        "Ollama not reachable at {0}: {1}",
    "risposta":
        "reply",
    "{0}: il filtro dei contenuti ha bloccato la risposta":
        "{0}: the content filter blocked the reply",
    "Il profilo Azure OpenAI richiede un endpoint e il nome del deployment":
        "The Azure OpenAI profile needs an endpoint and the deployment name",
    "Nessuna chiave API per il profilo {0}":
        "No API key for profile {0}",
    "Azure OpenAI":
        "Azure OpenAI",
    "Il profilo OpenAI richiede il nome del modello":
        "The OpenAI profile needs the model name",
    "OpenAI":
        "OpenAI",
    "Il profilo Anthropic richiede il nome del modello":
        "The Anthropic profile needs the model name",
    "default":
        "default",
    "Anthropic: chiave API non valida":
        "Anthropic: invalid API key",
    "Anthropic: la chiave non ha accesso a questo modello ({0})":
        "Anthropic: the key has no access to this model ({0})",
    "Anthropic: modello {0} non trovato":
        "Anthropic: model {0} not found",
    "Anthropic: troppe richieste, riprova tra poco":
        "Anthropic: too many requests, try again shortly",
    "Anthropic: richiesta rifiutata ({0})":
        "Anthropic: request refused ({0})",
    "Anthropic: errore {0} ({1})":
        "Anthropic: error {0} ({1})",
    "Anthropic: connessione non riuscita ({0})":
        "Anthropic: connection failed ({0})",
    "Anthropic: il modello ha rifiutato la richiesta":
        "Anthropic: the model refused the request",
    "Anthropic: risposta troncata (troppo lunga)":
        "Anthropic: reply truncated (too long)",
    "Tipo di AI sconosciuto {0}":
        "Unknown AI type {0}",
    "You answer with a JSON object only.":
        "You answer with a JSON object only.",
    "Reply with {{\"ok\": true, \"colour\": \"<the colour of a clear daytime sky, one English word>\"}}.":
        "Reply with {{\"ok\": true, \"colour\": \"<the colour of a clear daytime sky, one English word>\"}}.",
    "Il modello risponde correttamente (colore: {0}).":
        "The model answers correctly (colour: {0}).",
    "Il modello ha risposto, ma non come richiesto: {0}":
        "The model answered, but not as requested: {0}",
    "DVD":
        "DVD",
    "VHS":
        "VHS",
    "complete":
        "complete",
    "incomplete":
        "incomplete",
    "error":
        "error",
    "data ?":
        "date ?",
    "paese ?":
        "country ?",
    "formato ?":
        "format ?",
    "{0} tracce":
        "{0} tracks",
    "Errore: {0}":
        "Error: {0}",
    "Non trovato su MusicBrainz":
        "Not found on MusicBrainz",
    "Incompleto: mancano {0} di {1} tracce":
        "Incomplete: {0} of {1} tracks missing",
    "Completo ({0} tracce)":
        "Complete ({0} tracks)",
    ", {0} copie in un altro formato":
        ", {0} copies in another format",
    "presente (copia)":
        "present (copy)",
    "La stessa traccia in un altro formato (lo stesso album in FLAC e in MP3): va bene":
        "The same track in another format (the same album in FLAC and in MP3): that is fine",
    ", {0} tracce non riconosciute":
        ", {0} tracks not recognised",
    "NFKD":
        "NFKD",
    "connessione a MusicBrainz non riuscita ({0})":
        "connection to MusicBrainz failed ({0})",
    "MusicBrainz è sovraccarico in questo momento: riprova tra qualche minuto":
        "MusicBrainz is overloaded right now: try again in a few minutes",
    "MusicBrainz ha risposto con l'errore {0}":
        "MusicBrainz answered with error {0}",
    "artist:{0}":
        "artist:{0}",
    "json":
        "json",
    "release:{0}":
        "release:{0}",
    " AND artist:{0}":
        " AND artist:{0}",
    "recordings":
        "recordings",
    "l'album non ha un nome: compila il tag Album":
        "the album has no name: fill in the Album tag",
    "myEasyMP3toIPhone è già aperto: usa la finestra che c'è già.\n\nDue copie aperte insieme si contendono la cartella dati.":
        "myEasyMP3toIPhone is already open: use the window that is already there.\n\nTwo copies open together fight over the data folder.",
    "requests":
        "requests",
    "keyring":
        "keyring",
    "anthropic":
        "anthropic",
    "ERRORE  {0}: {1}: {2}":
        "ERROR  {0}: {1}: {2}",
    "ERRORE  manca {0}":
        "ERROR  missing {0}",
    "info    credential store: {0}":
        "info    credential store: {0}",
    "Profilo AI {0} non trovato (Impostazioni → Profili AI)":
        "AI profile {0} not found (Settings → AI profiles)",
    "Cartella non trovata: {0}":
        "Folder not found: {0}",
    "Rapporto salvato in {0}":
        "Report saved in {0}",
    "myEasyMP3toIPhone, console":
        "myEasyMP3toIPhone, console",
    "iii":
        "iii",
    "{0} (feat. {1})":
        "{0} (feat. {1})",
    "solo il cognome":
        "surname only",
    "iniziali":
        "initials",
    "l'AI confronta {0} gruppi di nomi d'artista":
        "the AI compares {0} groups of artist names",
    "   {0} | {1} tracks | {2}":
        "   {0} | {1} tracks | {2}",
    "GROUPS\n":
        "GROUPS\n",
    "nomi degli artisti: {0}":
        "artist names: {0}",
    "ollama":
        "ollama",
    "azure":
        "azure",
    "openai":
        "openai",
    "Anthropic (Claude)":
        "Anthropic (Claude)",
    "(nel credential store)":
        "(in the credential store)",
    "Ollama locale":
        "Local Ollama",
    "Gestione credenziali di Windows":
        "Windows Credential Manager",
    "il credential store del sistema":
        "the system credential store",
    "secrets.json nella cartella dati":
        "secrets.json in the data folder",
    "CalibreDuplicateRemover":
        "CalibreDuplicateRemover",
    "(in the credential store)":
        "(in the credential store)",
    "Music":
        "Music",
    "il server salvato per {0}":
        "the server saved for {0}",
    "AppSettings":
        "AppSettings",
    "# Aggiunte da myEasyMP3toIPhone: variabili lette dal programma o dalle tue Impostazioni":
        "# Added by myEasyMP3toIPhone: variables read by the program or by your Settings",
    "ciclo":
        "cycle",
    "senza valore":
        "no value",
    "{0} ignorata nel file delle variabili: la cartella dati si sceglie prima di leggerlo. Usa la variabile di sistema {1} e lascia vuota questa riga":
        "{0} ignored in the variables file: the data folder is chosen before reading it. Use the system variable {1} and leave this line empty",
    "{0}: i riferimenti $NOME formano un ciclo, la riga non si usa":
        "{0}: the $NAME references form a cycle, the line is not used",
    "{0} legge una variabile senza valore: la riga non si usa (un valore che inizia davvero con $ si scrive $$)":
        "{0} reads a variable with no value: the line is not used (a value that really starts with $ is written $$)",
    "{0} NON letto ({1}): le sue variabili non sono impostate. Controlla che sia leggibile e salvato in UTF-8":
        "{0} NOT read ({1}): its variables are not set. Check that it is readable and saved in UTF-8",
    "{0}: righe ignorate {1}, non sono NOME=valore (correggile o iniziale con #)":
        "{0}: lines ignored {1}, they are not NAME=value (fix them or start them with #)",
    "file":
        "file",
    "sistema":
        "system",
    "Creato {0}":
        "Created {0}",
    "Aggiunte a {0}: {1}":
        "Added to {0}: {1}",
    "{0} NON aggiornato ({1}): controlla che sia scrivibile e in UTF-8":
        "{0} NOT updated ({1}): check that it is writable and in UTF-8",
    " (la variabile non è impostata)":
        " (the variable is not set)",
    "nessuna chiave":
        "no key",
    "impostata, ignorata: non è un percorso completo":
        "set, ignored: not a full path",
    "impostata ({0})":
        "set ({0})",
    "frozen":
        "frozen",
    "impostata":
        "set",
    " (il valore impostato è ignorato: non è un percorso completo)":
        " (the value set is ignored: not a full path)",
    " (il valore impostato non è un livello)":
        " (the value set is not a level)",
    "la variabile d'ambiente ${0}":
        "the environment variable ${0}",
    "la chiave salvata in {0}":
        "the key saved in {0}",
    "${0} non ha valore: {1}":
        "${0} has no value: {1}",
    "Cartella dati: {0}":
        "Data folder: {0}",
    "Variabili d'ambiente. Impostale in {0}: un valore scritto lì vince, una riga vuota usa quello del sistema":
        "Environment variables. Set them in {0}: a value written there wins, an empty line uses the system one",
    "Le chiavi API dei profili AI:":
        "The API keys of the AI profiles:",
    "Antonio Romeo":
        "Antonio Romeo",
    "with Claude Code et al.":
        "with Claude Code et al.",
    "MIT License":
        "MIT License",
    "<p><b>Le chiavi API dei profili AI</b>: dove è salvata ciascuna, mai la chiave.</p><table>{0}</table>":
        "<p><b>The API keys of the AI profiles</b>: where each one is saved, never the key.</p><table>{0}</table>",
    "<h3>{0}</h3><p>Versione {1}</p><p>Autore: <b>{2}</b> ({3})<br>{4}</p><p>Cartella dati: <code>{5}</code><br>File delle variabili: <code>{6}</code></p><p><b>Variabili d'ambiente</b> e valore usato: <i>(file)</i> = scritto nel file delle variabili, <i>(sistema)</i> = dalle variabili di Windows. Riavvia il programma dopo averne cambiata una.</p><table>{7}</table>{8}":
        "<h3>{0}</h3><p>Version {1}</p><p>Author: <b>{2}</b> ({3})<br>{4}</p><p>Data folder: <code>{5}</code><br>Variables file: <code>{6}</code></p><p><b>Environment variables</b> and the value used: <i>(file)</i> = written in the variables file, <i>(system)</i> = from the Windows variables. Restart the program after changing one.</p><table>{7}</table>{8}",
    "Informazioni su {0}":
        "About {0}",
    "regole":
        "rules",
    "impronta":
        "fingerprint",
    "<b>{0}</b> brani dell'iPhone ritrovati sul PC con l'impronta dell'audio: si associano alla loro sorgente senza chiedere.":
        "<b>{0}</b> iPhone tracks found on the PC by their audio fingerprint: they are linked to their source without asking.",
    "<b>{0}</b> proposte da controllare ({1} già spuntate perché quasi certe).":
        "<b>{0}</b> proposals to check ({1} already ticked because almost certain).",
    "<b>{0}</b> brani senza un file sul PC: restano <i>senza sorgente</i>, il programma non li tocca.":
        "<b>{0}</b> tracks without a file on the PC: they stay <i>without source</i>, the program does not touch them.",
    "{0} brani avevano già la sorgente.":
        "{0} tracks already had their source.",
    "{0} brani acquistati o scaricati sul telefono: non hanno una sorgente.":
        "{0} tracks bought or downloaded on the phone: they have no source.",
    "<span style='color:#c33'>AI non riuscita: {0}</span>":
        "<span style='color:#c33'>AI failed: {0}</span>",
    "Associa sorgenti: i file del PC dei brani dell'iPhone":
        "Link sources: the PC files of the iPhone tracks",
    "Brano sull'iPhone":
        "Track on the iPhone",
    "File sul PC":
        "File on the PC",
    "Come":
        "How",
    "Perché":
        "Why",
    "Spunta tutte":
        "Tick all",
    "Togli tutte":
        "Untick all",
    "Associa":
        "Link",
    "Annulla":
        "Cancel",
    "Associare scrive solo il registro della provenienza (sul PC e sull'iPhone): né i brani dell'iPhone né i file del PC cambiano.":
        "Linking only writes the provenance register (on the PC and on the iPhone): neither the iPhone tracks nor the PC files change.",
    "Verifica completezza album":
        "Album completeness check",
    "Mostra solo gli album da sistemare":
        "Show only the albums to fix",
    "Edizione su MusicBrainz:":
        "Edition on MusicBrainz:",
    "Traccia":
        "Track",
    "Titolo su MusicBrainz":
        "Title on MusicBrainz",
    "Stato":
        "Status",
    "scarica anche la copertina":
        "also download the cover",
    "Correggi i tag con questi dati":
        "Fix the tags with this data",
    "Imposta titolo, numero traccia/disco, album, artista album e anno dei brani riconosciuti secondo MusicBrainz":
        "Sets title, track/disc number, album, album artist and year of the recognised tracks as on MusicBrainz",
    "Apri su MusicBrainz":
        "Open on MusicBrainz",
    "Riprova la verifica":
        "Check again",
    "Chiudi":
        "Close",
    "{0} album verificati: {1} completi, {2} incompleti":
        "{0} albums checked: {1} complete, {2} incomplete",
    ", {0} non trovati o con errori":
        ", {0} not found or with errors",
    "MANCANTE":
        "MISSING",
    "presente":
        "present",
    "non riconosciuta":
        "not recognised",
    "Il brano non corrisponde a nessuna traccia di questa edizione":
        "The track does not match any track of this edition",
    "Verifica edizione":
        "Edition check",
    "Verifica album":
        "Check albums",
    "Correggi tag":
        "Fix tags",
    "Aggiornare i tag di {0} brani con i dati di MusicBrainz?\n\n{1}":
        "Update the tags of {0} tracks with the MusicBrainz data?\n\n{1}",
    "download copertina":
        "cover download",
    "Tag corretti su {0} brani, salvati per l'iPhone: i file sul PC non cambiano. Inviali all'iPhone per applicarli.":
        "Tags fixed on {0} tracks, saved for the iPhone: the files on the PC do not change. Send them to the iPhone to apply them.",
    "\nNessuna copertina disponibile per questa edizione.":
        "\nNo cover available for this edition.",
    "Correzione tag":
        "Tag fix",
    "Artista":
        "Artist",
    "Album":
        "Album",
    "Brani":
        "Tracks",
    "Anno":
        "Year",
    "Artisti":
        "Artists",
    "(Tutti gli artisti: {0})":
        "(All artists: {0})",
    "(Tutti gli album":
        "(All albums",
    " degli artisti scelti":
        " of the chosen artists",
    "pinned":
        "pinned",
    "<table cellspacing='0' cellpadding='3'>":
        "<table cellspacing='0' cellpadding='3'>",
    "<tr><td colspan='3'><b>{0}</b><br><span style='white-space:pre'>{1}</span><br><span style='color:{2}'>{3}</span></td></tr>":
        "<tr><td colspan='3'><b>{0}</b><br><span style='white-space:pre'>{1}</span><br><span style='color:{2}'>{3}</span></td></tr>",
    "<tr><th align='left'>Campo</th><th align='left'>Sul PC</th><th align='left'>Sull'iPhone</th></tr>":
        "<tr><th align='left'>Field</th><th align='left'>On the PC</th><th align='left'>On the iPhone</th></tr>",
    " style='color:{0}; font-weight:bold'":
        " style='color:{0}; font-weight:bold'",
    "Sul PC":
        "On the PC",
    "Sorgente":
        "Source",
    "Titolo":
        "Title",
    "Genere":
        "Genre",
    "Durata":
        "Duration",
    "questo PC":
        "this PC",
    "nessuna":
        "none",
    "telefono":
        "phone",
    "file non trovato":
        "file not found",
    "Tutti i brani":
        "All tracks",
    "Senza sorgente (solo sull'iPhone)":
        "Without source (only on the iPhone)",
    "Con la sorgente su questo PC":
        "With the source on this PC",
    "Da altri computer":
        "From other computers",
    "File del PC non trovato":
        "PC file not found",
    "Acquistati o scaricati sul telefono":
        "Bought or downloaded on the phone",
    "Senza file sull'iPhone (fantasmi)":
        "Without a file on the iPhone (ghosts)",
    "Sul PC c'è lo stesso brano, con gli stessi tag":
        "On the PC there is the same track, with the same tags",
    "Sul PC c'è lo stesso brano, ma con tag diversi:\n":
        "On the PC there is the same track, but with different tags:\n",
    "Non è nella cartella aperta sul PC (confronto per artista, album e titolo)":
        "Not in the folder open on the PC (compared by artist, album and title)",
    "Se l'app Musica era aperta, chiudila del tutto e riaprila per vedere le modifiche (cerca nella tua libreria, non in Apple Music).":
        "If the Music app was open, close it completely and reopen it to see the changes (look in your library, not in Apple Music).",
    "iPhone non connesso":
        "iPhone not connected",
    "Connetti iPhone":
        "Connect iPhone",
    "Disconnetti iPhone":
        "Disconnect iPhone",
    "connesso":
        "connected",
    "connessione":
        "connection",
    "non connesso":
        "not connected",
    "Non premere mai \"Sincronizza\" in iTunes o in Dispositivi Apple: con la musica messa da un altro programma, iTunes la toglierebbe dall'iPhone.":
        "Never press \"Sync\" in iTunes or in Apple Devices: with music put there by another program, iTunes would remove it from the iPhone.",
    "<b>Come funziona.</b> Qui vedi la musica dell'app <b>Musica</b> dell'iPhone, con i titoli, gli artisti e gli album che mostra l'app. La colonna <b>Sul PC</b> la confronta con la cartella aperta nella scheda PC: ✔ stesso brano, ⟳ stesso brano con tag diversi, vuoto = non c'è. <b>Sorgente</b>: il file da cui viene il brano (questo PC, un altro computer, nessuna, telefono); <b>Associa sorgenti</b> la ritrova per tutti, <b>Mostra</b> filtra.<br>Tasto destro su uno o più brani: <b>Salva su PC</b>, <b>Mostra nella scheda PC</b>, <b>Rimpiazza con la versione del PC</b> (per i ⟳), <b>Cambia tag</b>, <b>Associa sorgente</b>, <b>Togli sorgente</b>, <b>Elimina dall'iPhone</b>. Per mandare brani nuovi: tasto destro nella scheda PC → <b>Invia all'iPhone</b>. I file del PC non cambiano mai.<br><b>Attenzione:</b> {0}":
        "<b>How it works.</b> Here you see the music of the iPhone <b>Music</b> app, with the titles, artists and albums the app shows. The <b>On the PC</b> column compares it with the folder open in the PC tab: ✔ same track, ⟳ same track with different tags, empty = not there. <b>Source</b>: the file the track comes from (this PC, another computer, none, phone); <b>Link sources</b> finds it for all of them, <b>Show</b> filters.<br>Right-click on one or more tracks: <b>Save to PC</b>, <b>Show in the PC tab</b>, <b>Replace with the PC version</b> (for the ⟳), <b>Change tags</b>, <b>Link source</b>, <b>Remove source</b>, <b>Delete from the iPhone</b>. To send new tracks: right-click in the PC tab → <b>Send to the iPhone</b>. The PC files never change.<br><b>Warning:</b> {0}",
    "Saltati":
        "Skipped",
    "Non riusciti":
        "Failed",
    "… e altri {0}":
        "… and {0} more",
    "\n\nI brani rimpiazzati non sono più nelle playlist fatte sull'iPhone: rimettili a mano (app Musica, playlist, Modifica, Aggiungi musica):\n":
        "\n\nThe replaced tracks are no longer in the playlists made on the iPhone: put them back by hand (Music app, playlist, Edit, Add Music):\n",
    "Cambia tag sull'iPhone":
        "Change tags on the iPhone",
    "title":
        "title",
    "album":
        "album",
    "genre":
        "genre",
    "year":
        "year",
    "N. traccia":
        "Track no.",
    "N. disco":
        "Disc no.",
    "(si cambia un brano alla volta)":
        "(changed one track at a time)",
    "Compilation (album di artisti vari)":
        "Compilation (album by various artists)",
    "Valori diversi tra i brani scelti: lasciala così per non cambiarla.":
        "Different values among the chosen tracks: leave it like this to keep them.",
    "{0} brani. Artista e artista dell'album non si cambiano qui: sull'iPhone rinominerebbero l'artista per tutti i suoi brani. Cambiali nella scheda PC, poi usa <i>Rimpiazza con la versione del PC</i>. Anno o numero 0: lo svuota.<br>Una compilation vuole anche l'artista dell'album <i>Artisti vari</i>: se nell'app Musica i brani non si raccolgono in un solo album, metti la spunta e \"Artisti vari\" nella scheda PC e usa <i>Rimpiazza con la versione del PC</i>.":
        "{0} tracks. Artist and album artist are not changed here: on the iPhone they would rename the artist for all their tracks. Change them in the PC tab, then use <i>Replace with the PC version</i>. Year or number 0: clears it.<br>A compilation also wants the album artist <i>Various artists</i>: if in the Music app the tracks do not gather into one album, tick the box and set \"Various artists\" in the PC tab and use <i>Replace with the PC version</i>.",
    "Applica sull'iPhone":
        "Apply on the iPhone",
    "{0}: serve un numero":
        "{0}: a number is needed",
    "Cambia tag":
        "Change tags",
    "Non hai cambiato niente.":
        "You did not change anything.",
    "iPhone":
        "iPhone",
    "Cerca per titolo, artista o album…":
        "Search by title, artist or album…",
    "Quali brani mostrare, secondo la loro origine (il registro della provenienza)":
        "Which tracks to show, by their origin (the provenance register)",
    "Mostra:":
        "Show:",
    "Aggiorna elenco":
        "Refresh list",
    "Rilegge la musica dell'app Musica dall'iPhone connesso":
        "Reads the Music app music again from the connected iPhone",
    "Salva i selezionati sul PC…":
        "Save the selected to the PC…",
    "Associa sorgenti…":
        "Link sources…",
    "Ritrova nella cartella aperta sul PC la sorgente (il file) di ogni brano dell'iPhone: impronta dell'audio, poi regole e AI per i dubbi. Scrive solo il registro della provenienza: né i brani né i file cambiano.":
        "Finds in the folder open on the PC the source (the file) of every iPhone track: audio fingerprint, then rules and AI for the doubtful ones. It only writes the provenance register: neither the tracks nor the files change.",
    "Musica nell'app Musica dell'iPhone":
        "Music in the iPhone Music app",
    "Messo sull'iPhone dal telefono stesso (acquisto o download): non si gestisce da un computer":
        "Put on the iPhone by the phone itself (purchase or download): not managed from a computer",
    "Origine sconosciuta: messo sull'iPhone da un altro programma o da un altro computer":
        "Unknown origin: put on the iPhone by another program or another computer",
    "Da {0} ({1}, {2}):\n{3}":
        "From {0} ({1}, {2}):\n{3}",
    "Brano \"fantasma\": è nell'elenco dell'app Musica, ma il suo file sull'iPhone non c'è, quindi non si può ascoltare. Toglilo con Elimina dall'iPhone (tasto destro).\n":
        "\"Ghost\" track: it is in the Music app list, but its file is not on the iPhone, so it cannot be played. Remove it with Delete from the iPhone (right-click).\n",
    "Abbinato dal registro della provenienza ({0}): certo":
        "Matched by the provenance register ({0}): certain",
    "Abbinato per artista, album e titolo: probabile, non certo":
        "Matched by artist, album and title: probable, not certain",
    "{0} di {1} brani":
        "{0} of {1} tracks",
    "{0} brani":
        "{0} tracks",
    "Associa sorgente…":
        "Link source…",
    "Associa sorgente da una cartella… ({0} brani)":
        "Link source from a folder… ({0} tracks)",
    "Salva su PC… ({0} brani)":
        "Save to PC… ({0} tracks)",
    "Mostra nella scheda PC ({0} brani)":
        "Show in the PC tab ({0} tracks)",
    "Rimpiazza con la versione del PC ({0} brani ⟳)":
        "Replace with the PC version ({0} tracks ⟳)",
    "Cambia tag… ({0} brani)":
        "Change tags… ({0} tracks)",
    "Togli sorgente ({0} brani)":
        "Remove source ({0} tracks)",
    "Elimina dall'iPhone… ({0} brani)":
        "Delete from the iPhone… ({0} tracks)",
    "Connetti l'iPhone":
        "Connect the iPhone",
    "lettura della musica dell'app Musica":
        "reading the Music app music",
    "Lettura dell'iPhone":
        "Reading the iPhone",
    "{0} brani dell'iPhone senza file (fantasmi): Mostra → \"Senza file sull'iPhone\", poi tasto destro → Elimina dall'iPhone":
        "{0} iPhone tracks without a file (ghosts): Show → \"Without a file on the iPhone\", then right-click → Delete from the iPhone",
    "{0} brani ora sono senza sorgente":
        "{0} tracks are now without source",
    "rilettura della musica dell'iPhone":
        "reading the iPhone music again",
    "Inviare {0} brani all'app Musica dell'iPhone ({1})?\n\nVanno copie con i tag e la copertina modificati: i file del PC non cambiano.":
        "Send {0} tracks to the iPhone Music app ({1})?\n\nCopies with the changed tags and cover are sent: the PC files do not change.",
    "Invia all'iPhone":
        "Send to the iPhone",
    "Invio all'iPhone":
        "Sending to the iPhone",
    "inviati":
        "sent",
    "Rimpiazzare {0} brani dell'iPhone con la versione del PC?\n\nPrima si invia la versione del PC, poi si toglie quella vecchia. I brani rimpiazzati perdono il conteggio degli ascolti e spariscono dalle playlist fatte sull'iPhone.":
        "Replace {0} iPhone tracks with the PC version?\n\nFirst the PC version is sent, then the old one is removed. The replaced tracks lose their play count and disappear from the playlists made on the iPhone.",
    "\n\nSono nelle playlist (alla fine te le ricordo, per rimetterli a mano):\n":
        "\n\nThey are in the playlists (I will remind you at the end, to put them back by hand):\n",
    "Rimpiazza":
        "Replace",
    "Rimpiazzo sull'iPhone":
        "Replacing on the iPhone",
    "rimpiazzati":
        "replaced",
    "• {0} brani da inviare":
        "• {0} tracks to send",
    "• {0} brani da togliere dall'iPhone (sul PC non cambia niente)":
        "• {0} tracks to remove from the iPhone (nothing changes on the PC)",
    "• {0} brani da aggiornare con Cambia tag (restano ascolti e playlist)":
        "• {0} tracks to update with Change tags (play counts and playlists stay)",
    "• {0} brani da rimpiazzare (artista, artista dell'album o un campo da svuotare: perdono ascolti e playlist)":
        "• {0} tracks to replace (artist, album artist or a field to clear: they lose play counts and playlists)",
    "Applicare all'iPhone le modifiche in attesa?\n\n":
        "Apply the pending changes to the iPhone?\n\n",
    "\n\nI brani da rimpiazzare sono nelle playlist (alla fine te le ricordo):\n":
        "\n\nThe tracks to replace are in the playlists (I will remind you at the end):\n",
    "Applica":
        "Apply",
    "Applica all'iPhone":
        "Apply to the iPhone",
    "sistemati sull'iPhone":
        "done on the iPhone",
    "{0} brani sull'iPhone vengono da questi file e ora sono diversi: sono in attesa di aggiornamento (⟳ blu), premi Applica quando l'iPhone è connesso":
        "{0} tracks on the iPhone come from these files and are now different: they are waiting to be updated (blue ⟳), press Apply when the iPhone is connected",
    "Il brano modificato è anche sull'iPhone. Aggiornarlo anche lì?\n":
        "The changed track is also on the iPhone. Update it there too?\n",
    "I {0} brani modificati sono anche sull'iPhone. Aggiornarli anche lì?\n":
        "The {0} changed tracks are also on the iPhone. Update them there too?\n",
    "{0} dei {1} brani modificati sono anche sull'iPhone. Aggiornarli anche lì?\n":
        "{0} of the {1} changed tracks are also on the iPhone. Update them there too?\n",
    "\n• {0} con Cambia tag (titolo, album, genere, anno, numeri, compilation): restano ascolti e playlist.":
        "\n• {0} with Change tags (title, album, genre, year, numbers, compilation): play counts and playlists stay.",
    "\n• {0} con Rimpiazza (artista, artista dell'album o copertina): perdono ascolti e playlist; alla fine ti dico in quali playlist rimetterli.":
        "\n• {0} with Replace (artist, album artist or cover): they lose play counts and playlists; at the end I tell you which playlists to put them back in.",
    "\n\n{0} brani non sono sull'iPhone o lì non vengono da questi file: cambiano solo sul PC.":
        "\n\n{0} tracks are not on the iPhone or there they do not come from these files: they change only on the PC.",
    "Aggiorna anche l'iPhone":
        "Update the iPhone too",
    "Aggiornamento dell'iPhone":
        "Updating the iPhone",
    "aggiornati":
        "updated",
    "{0} dei {1} brani vengono da file di questo PC. Salvare le stesse modifiche anche per quei file?\n\nSul PC le modifiche restano in sospeso (i file non cambiano) e valgono per le copie inviate, esportate o importate.":
        "{0} of the {1} tracks come from files of this PC. Save the same changes for those files too?\n\nOn the PC the changes stay pending (the files do not change) and apply to the copies sent, exported or imported.",
    "modificati":
        "changed",
    "Eliminare {0} brani dall'app Musica dell'iPhone?\n\n":
        "Delete {0} tracks from the iPhone Music app?\n\n",
    "\n\nSpariscono dall'iPhone con i loro ascolti. Sul PC non cambia niente. ":
        "\n\nThey disappear from the iPhone with their play counts. Nothing changes on the PC. ",
    "Elimina dall'iPhone":
        "Delete from the iPhone",
    "Eliminazione dall'iPhone":
        "Deleting from the iPhone",
    "eliminati":
        "deleted",
    "Associa sorgenti":
        "Link sources",
    "Apri prima nella scheda PC la cartella con la tua musica.":
        "First open the folder with your music in the PC tab.",
    "Cercare la sorgente di {0} brani dell'iPhone nei file della cartella aperta ({1} brani)?\n\n":
        "Look for the source of {0} iPhone tracks among the files of the open folder ({1} tracks)?\n\n",
    "Prima legge l'impronta dell'audio di {0} brani dall'iPhone: circa {1} minuti. Puoi annullare e riprendere: quelle già lette si ricordano.\n\n":
        "First it reads the audio fingerprint of {0} tracks from the iPhone: about {1} minutes. You can cancel and resume: the ones already read are remembered.\n\n",
    "I casi dubbi li confronta l'AI ({0}).\n\n":
        "The AI compares the doubtful cases ({0}).\n\n",
    "I casi dubbi te li mostro da controllare (l'AI della scansione è spenta).\n\n":
        "I show you the doubtful cases to check (the scan AI is off).\n\n",
    "Alla fine vedi tutto prima di confermare; i brani e i file non cambiano.":
        "At the end you see everything before confirming; tracks and files do not change.",
    "Associazione delle sorgenti":
        "Linking the sources",
    "Interrotto. Le impronte già lette sono ricordate: riprendi quando vuoi con Associa sorgenti.":
        "Interrupted. The fingerprints already read are remembered: resume when you want with Link sources.",
    "registro della provenienza sull'iPhone":
        "provenance register on the iPhone",
    "{0} brani associati alla loro sorgente sul PC.":
        "{0} tracks linked to their source on the PC.",
    "Registro della provenienza":
        "Provenance register",
    "registro della provenienza":
        "provenance register",
    "ricerca dei file possibili":
        "looking for the possible files",
    "Associa sorgente":
        "Link source",
    " (sul computer {0})":
        " (on the computer {0})",
    "Il brano ha già una sorgente:\n{0}{1}\n\nSostituirla con:\n{2}?":
        "The track already has a source:\n{0}{1}\n\nReplace it with:\n{2}?",
    "Sorgente associata: {0}":
        "Source linked: {0}",
    "La cartella del PC con le sorgenti di {0} brani (anche nelle sottocartelle)":
        "The PC folder with the sources of {0} tracks (subfolders too)",
    "impronte dell'audio":
        "audio fingerprints",
    "Associa sorgente da una cartella":
        "Link source from a folder",
    "Sorgente associata a {0} brani":
        "Source linked to {0} tracks",
    "Togli sorgente":
        "Remove source",
    "Togliere la sorgente (il file del PC) di {0} brani dell'iPhone?\n\nI brani restano sull'iPhone e i file sul PC: diventano brani senza sorgente.":
        "Remove the source (the PC file) of {0} iPhone tracks?\n\nThe tracks stay on the iPhone and the files on the PC: they become tracks without source.",
    "Tolta la sorgente di {0} brani":
        "Source removed from {0} tracks",
    "Salva su PC":
        "Save to PC",
    "Seleziona prima uno o più brani nell'elenco.":
        "First select one or more tracks in the list.",
    "Connetti l'iPhone per copiarne i brani sul PC.":
        "Connect the iPhone to copy its tracks to the PC.",
    "Dove salvare i brani (in cartelle Artista/Album)":
        "Where to save the tracks (in Artist/Album folders)",
    "Salvataggio dall'iPhone":
        "Saving from the iPhone",
    "Copiati dall'iPhone: {0}\nNella cartella {1}: {2}\nAssociati ai file salvati (sorgente): {3}":
        "Copied from the iPhone: {0}\nIn the folder {1}: {2}\nLinked to the saved files (source): {3}",
    "\n\nNon copiati:\n":
        "\n\nNot copied:\n",
    "\n\nOperazione annullata.":
        "\n\nOperation cancelled.",
    "danger":
        "danger",
    "Chiude la connessione: il programma non si riconnette da solo finché non premi Connetti iPhone o stacchi e riattacchi il cavo":
        "Closes the connection: the program does not reconnect by itself until you press Connect iPhone or unplug and plug the cable again",
    "Connessione…":
        "Connecting…",
    "Si connette all'iPhone attaccato con il cavo e ne legge la musica":
        "Connects to the iPhone plugged in with the cable and reads its music",
    "iPhone disconnesso: premi Connetti iPhone per riconnetterlo":
        "iPhone disconnected: press Connect iPhone to connect it again",
    "iPhone disconnesso":
        "iPhone disconnected",
    "Driver Apple mancante: installa l'app gratuita \"Dispositivi Apple\" dal Microsoft Store (oppure iTunes)":
        "Apple driver missing: install the free \"Apple Devices\" app from the Microsoft Store (or iTunes)",
    "iPhone disconnesso (cavo staccato)":
        "iPhone disconnected (cable unplugged)",
    "Attacca l'iPhone con il cavo USB e sbloccalo":
        "Plug in the iPhone with the USB cable and unlock it",
    "iPhone rilevato: connessione… se l'iPhone lo chiede, tocca \"Autorizza\" e inserisci il codice":
        "iPhone detected: connecting… if the iPhone asks, tap \"Trust\" and enter the passcode",
    "iPhone rilevato: connessione in corso":
        "iPhone detected: connecting",
    "se l'iPhone lo chiede, tocca Autorizza e inserisci il codice":
        "if the iPhone asks, tap Trust and enter the passcode",
    "Connessione all'iPhone":
        "Connecting to the iPhone",
    "Connesso: ":
        "Connected: ",
    "iPhone connesso: ":
        "iPhone connected: ",
    "Tutti i formati":
        "All formats",
    "FLAC":
        "FLAC",
    "M4A / AAC":
        "M4A / AAC",
    "OGG / Opus":
        "OGG / Opus",
    "Nell'app Musica dell'iPhone c'è questo brano, con gli stessi tag":
        "The iPhone Music app has this track, with the same tags",
    "Nell'app Musica dell'iPhone c'è questo brano, ma con tag diversi:":
        "The iPhone Music app has this track, but with different tags:",
    "Non è nell'app Musica dell'iPhone":
        "Not in the iPhone Music app",
    "In attesa: da inviare all'iPhone (Applica)":
        "Pending: to send to the iPhone (Apply)",
    "In attesa: da togliere dall'iPhone (Applica)":
        "Pending: to remove from the iPhone (Apply)",
    "In attesa: da aggiornare sull'iPhone (Applica)":
        "Pending: to update on the iPhone (Apply)",
    "ascii":
        "ascii",
    "Azioni":
        "Actions",
    "Libreria":
        "Library",
    "Mostra la tua Libreria musicale":
        "Show your music Library",
    "Apri cartella":
        "Open folder",
    "Mostra i brani di una cartella qualsiasi, in sola lettura: i file non vengono mai modificati":
        "Shows the tracks of any folder, read-only: the files are never modified",
    "Importa cartella":
        "Import folder",
    "Copia una cartella nella Libreria, ordinandola per Artista/Album":
        "Copies a folder into the Library, sorting it by Artist/Album",
    "Esporta":
        "Export",
    "Copia i brani selezionati in una cartella, ordinati per Artista/Album":
        "Copies the selected tracks into a folder, sorted by Artist/Album",
    "Controlla su MusicBrainz che gli album selezionati (o tutti) siano completi":
        "Checks on MusicBrainz that the selected albums (or all) are complete",
    "Controlla la musica":
        "Check the music",
    "Cerca i problemi nella cartella aperta o sull'iPhone: file non aggiornati, album con pochi brani, collezioni divise su più album, brani duplicati (con l'AI, se configurata)":
        "Looks for problems in the open folder or on the iPhone: files not updated, albums with few tracks, collections split over several albums, duplicate tracks (with the AI, if configured)",
    "Impostazioni":
        "Settings",
    "Cartella della Libreria, profili AI e chiavi":
        "Library folder, AI profiles and keys",
    "Informazioni":
        "About",
    "Versione, cartella dati, variabili d'ambiente e dove sono salvate le chiavi":
        "Version, data folder, environment variables and where the keys are saved",
    "Mostra solo i brani di un formato: vale per gli elenchi, la tabella, l'esportazione, Verifica album, la scansione e l'invio all'iPhone":
        "Show only the tracks of one format: applies to the lists, the table, the export, Check albums, the scan and sending to the iPhone",
    "Formato:":
        "Format:",
    "Annulla le modifiche":
        "Undo the changes",
    "Applica…":
        "Apply…",
    "{0}, elenco del {1}":
        "{0}, list of {1}",
    "iPhone ●":
        "iPhone ●",
    "iPhone connesso":
        "iPhone connected",
    "{0}, letto ora":
        "{0}, read now",
    "Nell'app Musica dell'iPhone ({0}): ✔ stesso brano, ⟳ stesso brano con tag diversi, vuoto = non c'è; la spunta: voglio il brano sull'iPhone":
        "In the iPhone Music app ({0}): ✔ same track, ⟳ same track with different tags, empty = not there; the tick: I want the track on the iPhone",
    "L'ultima cartella usata non è disponibile ({0}): apro la Libreria":
        "The last folder used is not available ({0}): opening the Library",
    "Benvenuto! Premi \"Apri cartella\" per vedere la tua musica, o \"Importa cartella\" per copiarla nella Libreria.":
        "Welcome! Press \"Open folder\" to see your music, or \"Import folder\" to copy it into the Library.",
    "Cartella da aprire":
        "Folder to open",
    "Libreria: {0}":
        "Library: {0}",
    "Cartella: {0}":
        "Folder: {0}",
    "{0} brani caricati (sola lettura: i file non vengono modificati)":
        "{0} tracks loaded (read-only: the files are not modified)",
    "Lettura brani":
        "Reading tracks",
    "{0} brani restano sull'iPhone: sono abbinati solo per i tag. Per toglierli da qui associa prima la sorgente (scheda iPhone, tasto destro), oppure eliminali dalla scheda iPhone.":
        "{0} tracks stay on the iPhone: they are matched only by their tags. To remove them from here first link the source (iPhone tab, right-click), or delete them from the iPhone tab.",
    "Modifiche in attesa non salvate nella cartella dati: {0}":
        "Pending changes not saved in the data folder: {0}",
    "<b>In attesa per l'iPhone:</b> {0} da inviare, {1} da togliere, {2} da aggiornare":
        "<b>Pending for the iPhone:</b> {0} to send, {1} to remove, {2} to update",
    "Annullare le {0} modifiche all'iPhone in attesa? Le spunte tornano come sono sull'iPhone.":
        "Undo the {0} pending changes to the iPhone? The ticks go back to how things are on the iPhone.",
    "Nessuna modifica da fare tra i brani della cartella aperta: le altre restano in attesa finché apri la cartella dei loro file.":
        "No change to make among the tracks of the open folder: the others stay pending until you open the folder of their files.",
    "Invia all'iPhone ({0} brani che non ci sono)":
        "Send to the iPhone ({0} tracks not there)",
    "Rimpiazza sull'iPhone ({0} brani con tag diversi ⟳)":
        "Replace on the iPhone ({0} tracks with different tags ⟳)",
    "Aggiorna più tardi: in attesa ({0} brani ⟳)":
        "Update later: pending ({0} tracks ⟳)",
    "{0} brani già sull'iPhone uguali ✔":
        "{0} tracks already on the iPhone, the same ✔",
    "Modifiche salvate per l'iPhone su {0} brani: i file sul PC non cambiano":
        "Changes saved for the iPhone on {0} tracks: the files on the PC do not change",
    "Tornati ai tag del file: {0} brani":
        "Back to the file tags: {0} tracks",
    "Numera in ordine":
        "Number in order",
    "Assegnare i numeri da 1 a {0} ai brani selezionati, nell'ordine della tabella?":
        "Give the numbers from 1 to {0} to the selected tracks, in the order of the table?",
    "Cartella da importare nella Libreria":
        "Folder to import into the Library",
    "Importa":
        "Import",
    "Questa cartella è già la Libreria.":
        "This folder is already the Library.",
    "Importazione":
        "Import",
    "Seleziona i brani in tabella, oppure scegli un artista o un album negli elenchi in alto.":
        "Select the tracks in the table, or choose an artist or an album in the lists above.",
    "Cartella in cui esportare {0} brani":
        "Folder where to export {0} tracks",
    "Esportazione":
        "Export",
    "copiati":
        "copied",
    "Non ci sono album da verificare.":
        "There are no albums to check.",
    "Verificare {0} album su MusicBrainz?\nServono circa {1} minuti (il servizio accetta una richiesta al secondo).\n\nPer verificarne solo alcuni, sceglili negli elenchi Artisti o Album.":
        "Check {0} albums on MusicBrainz?\nIt takes about {1} minutes (the service accepts one request per second).\n\nTo check only some of them, choose them in the Artists or Albums lists.",
    "C'è un'operazione in corso. Interromperla e uscire?":
        "An operation is running. Stop it and quit?",
    "search":
        "search",
    "orphan":
        "orphan",
    "delete":
        "delete",
    "Sorgenti sparite dal PC":
        "Sources gone from the PC",
    "<b>{0}</b> brani dell'iPhone vengono da file di questo PC che non ci sono più (spostati o cancellati). Il programma non li toglie dall'iPhone da solo: scegli tu cosa fare con quelli spuntati.<br>Se il file è su un disco che ora non è collegato, collegalo e premi <i>Più tardi</i>.":
        "<b>{0}</b> iPhone tracks come from files of this PC that are no longer there (moved or deleted). The program does not remove them from the iPhone by itself: you choose what to do with the ticked ones.<br>If the file is on a disk that is not connected now, connect it and press <i>Later</i>.",
    "Il file che non c'è più":
        "The file that is no longer there",
    "Spunta tutti":
        "Tick all",
    "Togli tutti":
        "Untick all",
    "Cerca un'altra sorgente…":
        "Look for another source…",
    "Uno alla volta, la finestra di Associa sorgente: per prima la copia con lo stesso audio":
        "One at a time, the Link source window: first the copy with the same audio",
    "Lascia senza sorgente":
        "Leave without source",
    "Restano sull'iPhone come brani senza sorgente":
        "They stay on the iPhone as tracks without source",
    "Elimina dall'iPhone…":
        "Delete from the iPhone…",
    "Toglie i brani dall'iPhone (chiede conferma); sul PC non cambia niente":
        "Removes the tracks from the iPhone (asks first); nothing changes on the PC",
    "Più tardi":
        "Later",
    "Li ritrovi quando vuoi con Mostra → \"File del PC non trovato\" e il tasto destro.":
        "You find them again whenever you want with Show → \"PC file not found\" and right-click.",
    "I brani della cartella aperta ({0})":
        "The tracks of the open folder ({0})",
    "Nessuna cartella aperta":
        "No folder open",
    "La musica dell'app Musica dell'iPhone ({0} brani, {1}), confrontata con la Libreria":
        "The music of the iPhone Music app ({0} tracks, {1}), compared with the Library",
    "L'iPhone (connettilo una volta: la sua musica resta ricordata)":
        "The iPhone (connect it once: its music is remembered)",
    "…e i nomi dubbi anche su MusicBrainz (nomi e alias dell'artista; lento: un artista al secondo, serve internet)":
        "…and the doubtful names on MusicBrainz too (names and aliases of the artist; slow: one artist per second, needs internet)",
    "Cosa controllare":
        "What to check",
    "Tutti":
        "All",
    "Nessuno":
        "None",
    "Usa l'AI ({0})":
        "Use the AI ({0})",
    "Usa l'AI (scegli un profilo in Impostazioni → Generale)":
        "Use the AI (choose a profile in Settings → General)",
    "Brani duplicati: la prima volta si legge l'impronta dell'audio di ogni file (qualche minuto per una collezione grande), poi si ricorda. Il rapporto resta nella cartella dati (scansioni).":
        "Duplicate tracks: the first time the audio fingerprint of every file is read (a few minutes for a large collection), then it is remembered. The report stays in the data folder (scansioni).",
    "Avvia":
        "Start",
    "Controllo della musica":
        "Checking the music",
    "iPhone, app Musica ({0})":
        "iPhone, Music app ({0})",
    "Controllo della musica dell'iPhone":
        "Checking the iPhone music",
    "<b>{0} problemi</b> in {1} brani e {2} album":
        "<b>{0} problems</b> in {1} tracks and {2} albums",
    " — analisi AI con {0}":
        " — AI analysis with {0}",
    " — <b>controllo interrotto: risultati parziali</b>":
        " — <b>check interrupted: partial results</b>",
    "<br><span style='color:#c33'>Errore AI: {0}</span>":
        "<br><span style='color:#c33'>AI error: {0}</span>",
    "Problema":
        "Problem",
    "Gravità":
        "Severity",
    "Origine":
        "Origin",
    "Correzione":
        "Fix",
    "Applica la correzione":
        "Apply the fix",
    "Mostra i brani":
        "Show the tracks",
    "Seleziona questi brani nella scheda PC":
        "Select these tracks in the PC tab",
    "Apri il rapporto":
        "Open the report",
    "L'AI ritiene che non sia un problema: {0}":
        "The AI thinks it is not a problem: {0}",
    "<p><i>Trovato dall'AI.</i></p>":
        "<p><i>Found by the AI.</i></p>",
    "<p><b>L'AI ritiene che non sia un problema:</b> {0}</p>":
        "<p><b>The AI thinks it is not a problem:</b> {0}</p>",
    "<p style='color:#1e8c3c'><b>Correzione applicata.</b></p>":
        "<p style='color:#1e8c3c'><b>Fix applied.</b></p>",
    "<p><b>Correzione proposta:</b> {0}</p>":
        "<p><b>Proposed fix:</b> {0}</p>",
    "<p>… e altri {0}</p>":
        "<p>… and {0} more</p>",
    "<p><b>{0} file:</b></p><ul>{1}</ul>{2}":
        "<p><b>{0} files:</b></p><ul>{1}</ul>{2}",
    "<p>Seleziona un problema per vederne i dettagli.</p>":
        "<p>Select a problem to see its details.</p>",
    "applicata":
        "applied",
    "Salvare queste modifiche per l'iPhone?\n\n{0}\n\nI file sul PC non cambiano: le modifiche vanno sulle copie che invierai all'iPhone.":
        "Save these changes for the iPhone?\n\n{0}\n\nThe files on the PC do not change: the changes go on the copies you will send to the iPhone.",
    "Modifiche salvate per l'iPhone su {0} brani. Inviali all'iPhone per applicarle.":
        "Changes saved for the iPhone on {0} tracks. Send them to the iPhone to apply them.",
    "\n{0} brani non sono più nella cartella aperta: ripeti la scansione.":
        "\n{0} tracks are no longer in the open folder: run the check again.",
    "(nessuna: solo le regole)":
        "(none: rules only)",
    "$NOME legge il valore dalla variabile d'ambiente NOME: si salva solo il nome. La variabile si imposta nel file\n%USERPROFILE%\\.myEasyMP3toIPhone\\myEasyMP3toIPhone.env (vince sul sistema) o nelle variabili di Windows.\nRiavvia il programma dopo averla cambiata.":
        "$NAME reads the value from the environment variable NAME: only the name is saved. Set the variable in the file\n%USERPROFILE%\\.myEasyMP3toIPhone\\myEasyMP3toIPhone.env (it wins over the system) or in the Windows variables.\nRestart the program after changing it.",
    "Generale":
        "General",
    "Profili AI":
        "AI profiles",
    "Sfoglia…":
        "Browse…",
    "La scansione usa sempre le regole locali (gratuite). Con un profilo AI, l'AI riceve una tabella degli album (artisti, titoli, numeri di traccia, nomi delle cartelle) e propone altri problemi e le correzioni. Con un'AI nel cloud questi dati escono dal computer; con Ollama restano qui.":
        "The scan always uses the local rules (free). With an AI profile, the AI receives a table of the albums (artists, titles, track numbers, folder names) and proposes more problems and the fixes. With a cloud AI this data leaves the computer; with Ollama it stays here.",
    "Cartella della Libreria":
        "Library folder",
    "AI della scansione":
        "Scan AI",
    "Aggiungi":
        "Add",
    "Duplica":
        "Duplicate",
    "Elimina":
        "Delete",
    "Importa da myCalibreTools…":
        "Import from myCalibreTools…",
    "Copia i profili AI di myCalibreTools ({0}), con le chiavi salvate nella Gestione credenziali":
        "Copies the AI profiles of myCalibreTools ({0}), with the keys saved in the Credential Manager",
    "\nUn indirizzo scritto qui va nella Gestione credenziali di Windows, non in un file.":
        "\nAn address written here goes into the Windows Credential Manager, not into a file.",
    "Aggiorna modelli":
        "Refresh models",
    "\nUna chiave scritta qui va nella Gestione credenziali di Windows; se inizia davvero con $, scrivi $$.":
        "\nA key written here goes into the Windows Credential Manager; if it really starts with $, write $$.",
    "Invia la temperatura":
        "Send the temperature",
    "Prova la connessione":
        "Test the connection",
    "Nome":
        "Name",
    "Tipo":
        "Type",
    "Chiave API":
        "API key",
    "Versione API":
        "API version",
    "Temperatura":
        "Temperature",
    "Timeout":
        "Timeout",
    "Contesto (Ollama)":
        "Context (Ollama)",
    "Al massimo per richiesta":
        "At most per request",
    " album":
        " albums",
    " brani":
        " tracks",
    "Controlla la musica con l'AI: quanti album e quanti brani mandare all'AI in ogni richiesta. Ci si ferma al primo dei due limiti; un album non si divide mai, quindi da solo può superare i brani. Con un modello piccolo, o un contesto corto, tienili bassi.":
        "Check the music with AI: how many albums and how many tracks to send to the AI in each request. It stops at "
        "the first of the two limits; an album is never split, so on its own it can exceed the tracks. With a small "
        "model, or a short context, keep them low.",
    "Endpoint":
        "Endpoint",
    "Server":
        "Server",
    "Deployment":
        "Deployment",
    "Modello":
        "Model",
    "nessuna: solo per un server che la chiede, es. $OLLAMA_API_KEY":
        "none: only for a server that asks for it, e.g. $OLLAMA_API_KEY",
    "la chiave, oppure $NOME di una variabile d'ambiente":
        "the key, or $NAME of an environment variable",
    "Ollama: l'indirizzo del server (predefinito http://localhost:11434) o $OLLAMA_API_BASE. \"Aggiorna modelli\" elenca i modelli installati. Con Ollama i dati restano sul computer.":
        "Ollama: the server address (default http://localhost:11434) or $OLLAMA_API_BASE. \"Refresh models\" lists the installed models. With Ollama the data stays on the computer.",
    "Azure OpenAI: l'endpoint della risorsa ($AZURE_FOUNDRY_EP) e il nome del deployment, la chiave $AZURE_FOUNDRY_KEY (gli stessi nomi di myCalibreTools); versione API per esempio 2024-10-21, oppure v1. Togli \"Invia la temperatura\" per i modelli di ragionamento.":
        "Azure OpenAI: the resource endpoint ($AZURE_FOUNDRY_EP) and the deployment name, the key $AZURE_FOUNDRY_KEY (the same names as myCalibreTools); API version for example 2024-10-21, or v1. Untick \"Send the temperature\" for reasoning models.",
    "OpenAI: il nome del modello e la chiave. L'endpoint è api.openai.com.":
        "OpenAI: the model name and the key. The endpoint is api.openai.com.",
    "Anthropic (Claude): il nome del modello (predefinito claude-opus-5-5) e la chiave. La temperatura non si invia: i modelli attuali non la accettano.":
        "Anthropic (Claude): the model name (default claude-opus-5-5) and the key. The temperature is not sent: current models do not accept it.",
    "Prova in corso…":
        "Testing…",
    "\n\nChiave usata: {0}.":
        "\n\nKey used: {0}.",
    "Prova: {0}":
        "Test: {0}",
    "Nuovo profilo":
        "New profile",
    "Importa da myCalibreTools":
        "Import from myCalibreTools",
    "Nessun profilo AI trovato in {0}.":
        "No AI profile found in {0}.",
    "Importati {0} profili: {1}.\nChiavi copiate nella Gestione credenziali: {2}.\nI profili che leggono una chiave da $NOME continuano a leggerla da lì.":
        "Imported {0} profiles: {1}.\nKeys copied into the Credential Manager: {2}.\nThe profiles that read a key from $NAME keep reading it from there.",
    "a mano":
        "by hand",
    "inviato":
        "sent",
    "salvato":
        "saved",
    "Si scrive solo il registro della provenienza: né i brani dell'iPhone né i file del PC cambiano.":
        "Only the provenance register is written: neither the iPhone tracks nor the PC files change.",
    "Il file del PC":
        "The PC file",
    "Audio ({0})":
        "Audio ({0})",
    "{0} (sul computer {1})":
        "{0} (on the computer {1})",
    "<br>Sorgente attuale: {0} — {1}. Scegliendo un altro file la sostituisci.":
        "<br>Current source: {0} — {1}. Choosing another file replaces it.",
    "<br>Scegli il file del PC da cui viene questo brano (il primo è il più probabile):":
        "<br>Choose the PC file this track comes from (the first is the most probable):",
    "Percorso":
        "Path",
    "consigliato — {0}":
        "recommended — {0}",
    "Associa sorgente annullata":
        "Link source cancelled",
    "Nessun file simile nella cartella aperta: scegli un file con il pulsante qui sotto.":
        "No similar file in the open folder: choose a file with the button below.",
    "Scegli un altro file…":
        "Choose another file…",
    "Salta (ne restano {0})":
        "Skip ({0} left)",
    "Cartella <b>{0}</b> (e sottocartelle): trovata la sorgente di <b>{1}</b> brani su {2}.":
        "Folder <b>{0}</b> (and subfolders): source found for <b>{1}</b> tracks out of {2}.",
    " <span style='color:#c33'>{0} non trovati</span> (in rosso).":
        " <span style='color:#c33'>{0} not found</span> (in red).",
    "File nella cartella":
        "File in the folder",
    "non trovato":
        "not found",
    "nessun file simile nella cartella":
        "no similar file in the folder",
    "Dopo, associa uno alla volta i {0} brani non trovati":
        "Afterwards, link the {0} tracks not found one at a time",
    "(valori diversi)":
        "(different values)",
    "Seleziona uno o più brani":
        "Select one or more tracks",
    "album di più artisti":
        "album by several artists",
    "Compilation: l'artista dell'album è \"Artisti vari\", quello del brano è il suo. Senza, l'app Musica dell'iPhone divide l'album in un album per artista.":
        "Compilation: the album artist is \"Various artists\", the track artist is its own. Without it, the iPhone Music app splits the album into one album per artist.",
    "Tag":
        "Tags",
    "Cambia copertina…":
        "Change cover…",
    "Copertina":
        "Cover",
    "Salva modifiche":
        "Save changes",
    "Salva le modifiche per l'iPhone: il file sul PC non cambia":
        "Save the changes for the iPhone: the file on the PC does not change",
    "Assegna i numeri di traccia 1, 2, 3… ai brani selezionati, nell'ordine mostrato in tabella":
        "Gives the track numbers 1, 2, 3… to the selected tracks, in the order shown in the table",
    "Torna ai tag del file":
        "Back to the file tags",
    "Annulla le modifiche in sospeso dei brani selezionati":
        "Undo the pending changes of the selected tracks",
    "I file sul PC sono in sola lettura: le modifiche restano in sospeso e valgono per le copie inviate all'iPhone (ed esportate).":
        "The files on the PC are read-only: the changes stay pending and apply to the copies sent to the iPhone (and exported).",
    "{0} brani selezionati: i campi modificati verranno applicati a tutti":
        "{0} tracks selected: the changed fields will be applied to all of them",
    "Scegli l'immagine di copertina":
        "Choose the cover image",
    "Immagini (*.jpg *.jpeg *.png)":
        "Images (*.jpg *.jpeg *.png)",
    "rgba(128, 128, 128, 0.22)":
        "rgba(128, 128, 128, 0.22)",
    "rgba(128, 128, 128, 0.95)":
        "rgba(128, 128, 128, 0.95)",
    "rgba(128, 128, 128, 0.35)":
        "rgba(128, 128, 128, 0.35)",
    "Fusion":
        "Fusion",
    "qtbase":
        "qtbase",
    "File":
        "File",
    "Modificato per l'iPhone (il file sul PC non cambia):\n":
        "Changed for the iPhone (the file on the PC does not change):\n",
    "Operazione in corso":
        "Operation running",
    "Attendi la fine dell'operazione in corso.":
        "Wait for the running operation to finish.",
    "annullamento…":
        "cancelling…",
    "version":
        "version",
    "{0} NON scritto ({1}): una copia futura della cartella dati potrebbe non dire con quale versione usarla. Controlla che la cartella sia scrivibile":
        "{0} NOT written ({1}): a future copy of the data folder might not say which version to use it with. Check that the folder is writable",
    "un'altra copia del programma sta facendo la copia da troppo tempo":
        "another copy of the program has been making the copy for too long",
    "Questa versione cambia il formato di alcuni file della cartella dati: la copio in {0}. Può richiedere qualche minuto.":
        "This version changes the format of some files of the data folder: I copy it to {0}. It may take a few minutes.",
    "La copia della cartella dati NON è stata fatta ({0}: {1}). Il programma si ferma e la cartella dati resta com'è. Chiudi le altre finestre di myEasyMP3toIPhone, controlla lo spazio libero e che {2} sia scrivibile, poi riavvia.":
        "The copy of the data folder was NOT made ({0}: {1}). The program stops and the data folder stays as it is. Close the other myEasyMP3toIPhone windows, check the free space and that {2} is writable, then restart.",
    "Il servizio Apple per i dispositivi non è attivo.\n\nInstalla l'app gratuita \"Dispositivi Apple\" dal Microsoft Store (oppure iTunes), poi riattacca l'iPhone.":
        "The Apple device service is not running.\n\nInstall the free \"Apple Devices\" app from the Microsoft Store (or iTunes), then plug the iPhone in again.",
    "Nessun iPhone trovato. Attacca l'iPhone con il cavo USB e sbloccalo.":
        "No iPhone found. Plug in the iPhone with the USB cable and unlock it.",
    "Sull'iPhone non c'è la libreria dell'app Musica (nessun brano è mai stato caricato).":
        "The iPhone has no Music app library (no track has ever been loaded).",
    "{0} — {1}, iOS {2}":
        "{0} — {1}, iOS {2}",
    "{0} file trasferiti":
        "{0} files transferred",
    "{0} già presenti":
        "{0} already there",
    "{0} errori":
        "{0} errors",
    "operazione annullata":
        "operation cancelled",
    "Sincronizzazione con l'iPhone non riuscita: {0}":
        "Sync with the iPhone failed: {0}",
    "L'iPhone è bloccato: sbloccalo e riprova.":
        "The iPhone is locked: unlock it and try again.",
    "Sull'iPhone tocca \"Autorizza\" e inserisci il codice, poi riprova.":
        "On the iPhone tap \"Trust\" and enter the passcode, then try again.",
    "L'autorizzazione è stata negata sull'iPhone. Stacca e riattacca il cavo per riprovare.":
        "Authorisation was denied on the iPhone. Unplug and plug the cable again to retry.",
    "Errore di comunicazione con l'iPhone: {0}":
        "Communication error with the iPhone: {0}",
    "Non riesco a leggere la musica dell'iPhone: {0}. Riprova; se succede ancora, la versione di iOS potrebbe usare un formato diverso.":
        "I cannot read the iPhone music: {0}. Try again; if it happens again, the iOS version might use a different format.",
    "Artista sconosciuto":
        "Unknown artist",
    "Album sconosciuto":
        "Unknown album",
    "CON":
        "CON",
    "PRN":
        "PRN",
    "AUX":
        "AUX",
    "NUL":
        "NUL",
    "COM{0}":
        "COM{0}",
    "LPT{0}":
        "LPT{0}",
    "{0} file copiati":
        "{0} files copied",
    "{0} aggiornati":
        "{0} updated",
    "{0} lasciati perché la destinazione è più recente":
        "{0} left because the destination is newer",
    "{0} brani già noti, ne leggo {1}":
        "{0} tracks already known, reading {1}",
    "Copertina nuova":
        "New cover",
    "invia":
        "send",
    "togli":
        "remove",
    "aggiorna":
        "update",
    "L'iPhone toglie i file dei brani eliminati da solo, entro qualche minuto.":
        "The iPhone removes the files of the deleted tracks by itself, within a few minutes.",
    "ActionReport":
        "ActionReport",
    "{0} brani {1}":
        "{0} tracks {1}",
    "{0} saltati":
        "{0} skipped",
    "{0} non riusciti":
        "{0} failed",
    "artwork":
        "artwork",
    "preparazione: {0}":
        "preparing: {0}",
    "invio all'iPhone di {0} brani":
        "sending {0} tracks to the iPhone",
    "eliminazione di {0} brani":
        "deleting {0} tracks",
    "non è più sull'iPhone":
        "is no longer on the iPhone",
    "non è stato messo da un computer":
        "was not put there by a computer",
    "versione vecchia non tolta: ":
        "old version not removed: ",
    "compilation":
        "compilation",
    "l'album non può essere vuoto":
        "the album cannot be empty",
    "il titolo non può essere vuoto":
        "the title cannot be empty",
    "il brano non ha un album con identificativo: usa Rimpiazza con la versione del PC":
        "the track has no album with an identifier: use Replace with the PC version",
    "il genere non si può svuotare sull'iPhone":
        "the genre cannot be cleared on the iPhone",
    "modifica di {0} brani":
        "changing {0} tracks",
    "modifica non applicabile":
        "change not applicable",
    "artist":
        "artist",
    "same":
        "same",
    "stale":
        "stale",
    "Artista album":
        "Album artist",
    "Compilation":
        "Compilation",
    "il database dell'app Musica non si legge ({0})":
        "the Music app database cannot be read ({0})",
    " e altri {0}":
        " and {0} more",
    "{0}: sul PC \"{1}\", sull'iPhone \"{2}\"":
        "{0}: on the PC \"{1}\", on the iPhone \"{2}\"",
    "la risposta Grappa deve essere di 83 byte":
        "the Grappa reply must be 83 bytes",
    "risposta Grappa di forma sconosciuta":
        "Grappa reply of unknown form",
    "file delle operazioni vuoto o troppo grande":
        "operations file empty or too large",
    "le preferenze dell'iPhone non sono né dati frpd né un plist":
        "the iPhone preferences are neither frpd data nor a plist",
    "il plist delle preferenze non contiene iPodPrefs":
        "the preferences plist does not contain iPodPrefs",
    "preferenze dell'iPhone di formato sconosciuto":
        "iPhone preferences of unknown format",
    "versione delle preferenze diversa da 1.25":
        "preferences version other than 1.25",
    "le preferenze dicono che la libreria non è configurata":
        "the preferences say the library is not configured",
    "identità della libreria nulla":
        "empty library identity",
    "iTunesCDB troncato":
        "iTunesCDB truncated",
    "iTunesCDB di formato sconosciuto":
        "iTunesCDB of unknown format",
    "IIIII":
        "IIIII",
    "intestazione di iTunesCDB inattesa":
        "unexpected iTunesCDB header",
    "versione o compressione di iTunesCDB inattese":
        "unexpected iTunesCDB version or compression",
    "sezione di iTunesCDB troncata":
        "iTunesCDB section truncated",
    "IIII":
        "IIII",
    "sezione di iTunesCDB rovinata":
        "iTunesCDB section damaged",
    "ancore di iTunesCDB di forma inattesa":
        "iTunesCDB anchors of unexpected form",
    "ancore assenti in iTunesCDB":
        "anchors missing in iTunesCDB",
    "il database dell'app Musica non ha la forma attesa ({0})":
        "the Music app database does not have the expected form ({0})",
    "il database dell'app Musica non ha esattamente una riga db_info":
        "the Music app database does not have exactly one db_info row",
    "il database dell'app Musica non ha l'ancora di sincronizzazione":
        "the Music app database has no sync anchor",
    "identità del database dell'app Musica nulla":
        "empty Music app database identity",
    "ancora di sincronizzazione non numerica":
        "non-numeric sync anchor",
    "Media":
        "Media",
    "iTunes":
        "iTunes",
    "RequestingSync":
        "RequestingSync",
    "Book":
        "Book",
    "Keybag":
        "Keybag",
    "FinishedSyncingMetadata":
        "FinishedSyncingMetadata",
    "SyncAllowed senza parametri":
        "SyncAllowed without parameters",
    "l'iPhone non accetta la gestione manuale della musica (in iTunes: Gestisci manualmente musica)":
        "the iPhone does not accept manual music management (in iTunes: Manually manage music)",
    "l'iPhone è bloccato: sbloccalo e riprova":
        "the iPhone is locked: unlock it and try again",
    "iPhone in modalità educativa":
        "iPhone in educational mode",
    "l'iPhone non accetta musica da un computer (probabilmente è attivo Sincronizza libreria di Apple Music)":
        "the iPhone does not accept music from a computer (probably Apple Music Sync Library is on)",
    "messaggio ATC senza comando":
        "ATC message without a command",
    "Pong":
        "Pong",
    "Ping":
        "Ping",
    "capacità Grappa dell'iPhone diverse da quelle note":
        "iPhone Grappa capabilities different from the known ones",
    "messaggio inatteso nella presentazione: {0}":
        "unexpected message in the handshake: {0}",
    "presentazione con l'iPhone incompleta":
        "incomplete handshake with the iPhone",
    "l'iPhone ha un'ancora diversa da quella letta ({0} invece di {1}): rileggi l'iPhone e riprova":
        "the iPhone has an anchor different from the one read ({0} instead of {1}): read the iPhone again and retry",
    "ReadyForSync senza Grappa":
        "ReadyForSync without Grappa",
    "l'iPhone ha rifiutato la sincronizzazione (codice {0})":
        "the iPhone refused the sync (code {0})",
    "messaggio inatteso invece di ReadyForSync: {0}":
        "unexpected message instead of ReadyForSync: {0}",
    "l'iPhone non ha risposto ReadyForSync":
        "the iPhone did not answer ReadyForSync",
    "numero di operazioni fuori dai limiti":
        "number of operations out of range",
    "MPEG audio file":
        "MPEG audio file",
    "FLAC audio file":
        "FLAC audio file",
    "AAC audio file":
        "AAC audio file",
    "{0}: non è un MP3 leggibile ({1})":
        "{0}: not a readable MP3 ({1})",
    "{0}: non è MPEG Layer III":
        "{0}: not MPEG Layer III",
    "{0}: frequenza o canali non validi per l'iPhone":
        "{0}: sample rate or channels not valid for the iPhone",
    "{0}: bitrate costante non standard ({1} kbit/s)":
        "{0}: non-standard constant bitrate ({1} kbit/s)",
    "{0}: bitrate medio fuori dai limiti ({1} kbit/s)":
        "{0}: average bitrate out of range ({1} kbit/s)",
    "{0}: durata nulla":
        "{0}: zero duration",
    "{0}: non è un FLAC leggibile ({1})":
        "{0}: not a readable FLAC ({1})",
    "{0}: l'iPhone accetta FLAC mono o stereo, non a {1} canali":
        "{0}: the iPhone accepts mono or stereo FLAC, not {1} channels",
    "{0}: non è un M4A leggibile ({1})":
        "{0}: not a readable M4A ({1})",
    "codec":
        "codec",
    "{0}: formato {1} non ancora gestito (solo AAC)":
        "{0}: format {1} not handled yet (AAC only)",
    "{0}: solo mono o stereo":
        "{0}: mono or stereo only",
    "{0}: l'iPhone qui accetta MP3, FLAC e M4A (AAC)":
        "{0}: here the iPhone accepts MP3, FLAC and M4A (AAC)",
    "{0} vuoto o troppo lungo":
        "{0} empty or too long",
    "identificativi del brano non validi":
        "invalid track identifiers",
    "titolo":
        "title",
    "artista":
        "artist",
    "copertina senza dimensione":
        "cover without size",
    "artista dell'album":
        "album artist",
    "genere":
        "genre",
    "track":
        "track",
    "disc":
        "disc",
    "aggiornamento vuoto":
        "empty update",
    "campo {0} non modificabile così":
        "field {0} cannot be changed this way",
    "is_compilation vuole un booleano":
        "is_compilation wants a boolean",
    "titolo e sort_name vanno insieme":
        "title and sort_name go together",
    "album e sort_album vanno insieme":
        "album and sort_album go together",
    "titolo e album vogliono anche album_pid":
        "title and album also want album_pid",
    "brano senza sync_id":
        "track without sync_id",
    "sull'iPhone c'è già {0}: niente da fare":
        "{0} is already on the iPhone: nothing to do",
    "manca la cartella di sincronizzazione sull'iPhone":
        "the sync folder is missing on the iPhone",
    "nella cartella di sincronizzazione dell'iPhone c'è già {0}: un'altra sincronizzazione non è finita, niente da fare":
        "the iPhone sync folder already contains {0}: another sync has not finished, nothing to do",
    "il file delle operazioni riletto dall'iPhone è diverso: non confermo niente":
        "the operations file read back from the iPhone is different: I confirm nothing",
    "l'iPhone ha interrotto la sincronizzazione (codice {0})":
        "the iPhone interrupted the sync (code {0})",
    "l'iPhone ha chiuso la sincronizzazione per inattività":
        "the iPhone closed the sync for inactivity",
    "messaggio inatteso durante la sincronizzazione: {0}":
        "unexpected message during the sync: {0}",
    "l'iPhone non ha chiesto l'audio di tutti i brani nuovi":
        "the iPhone did not ask for the audio of all the new tracks",
    "copertina riletta diversa":
        "cover read back different",
    "l'audio caricato ha una dimensione diversa":
        "the uploaded audio has a different size",
    "FileComplete":
        "FileComplete",
    "FileError":
        "FileError",
    "flac:":
        "flac:",
    "big":
        "big",
    "flacpcm:":
        "flacpcm:",
    "impronte dei file del PC: {0} di {1}":
        "PC file fingerprints: {0} of {1}",
    "Registry":
        "Registry",
    "duplicato":
        "duplicate",
    "illeggibile":
        "unreadable",
    "File che non si aggiornano":
        "Files that do not update",
    "Album con pochi brani":
        "Albums with few tracks",
    "Collezioni divise su più album":
        "Collections split over several albums",
    "Brani duplicati":
        "Duplicate tracks",
    "Tag mancanti":
        "Missing tags",
    "File illeggibili":
        "Unreadable files",
    "Solo sull'iPhone":
        "Only on the iPhone",
    "alta":
        "high",
    "media":
        "medium",
    "bassa":
        "low",
    "regola":
        "rule",
    "tags":
        "tags",
    "Artisti vari":
        "Various artists",
    "artisti":
        "artists",
    "illeggibili":
        "unreadable",
    "duplicati":
        "duplicates",
    "MP3 con un vecchio tag ID3v1 diverso o un tag APE; sull'iPhone, brani con tag diversi da quelli del PC":
        "MP3 with an old different ID3v1 tag or an APE tag; on the iPhone, tracks with tags different from the PC",
    "numeri di traccia mancanti, meno brani del totale dichiarato, album di 1-2 brani":
        "missing track numbers, fewer tracks than the declared total, albums of 1-2 tracks",
    "una cartella con album diversi, lo stesso album scritto in modi diversi o con \"CD 1\" nel nome, compilation senza artista dell'album":
        "a folder with different albums, the same album written in different ways or with \"CD 1\" in the name, compilations without album artist",
    "Artisti scritti in modi diversi":
        "Artists written in different ways",
    "\"The Beatles\" e \"Beatles\", \"AC/DC\" e \"ACDC\", accenti (le maiuscole da sole non contano)":
        "\"The Beatles\" and \"Beatles\", \"AC/DC\" and \"ACDC\", accents (capitals alone do not count)",
    "brani senza titolo, album o artista":
        "tracks without title, album or artist",
    "file danneggiati, bloccati o disponibili solo online":
        "damaged, locked or online-only files",
    "lo stesso brano due volte nello stesso album e formato: stesso audio anche con tag diversi, oppure stessa durata, titolo e artista; vanno bene una copia in un altro formato (FLAC e MP3) o in un altro album, e le versioni nominate nel titolo (Unplugged, Live, Remix…)":
        "the same track twice in the same album and format: same audio even with different tags, or same duration, "
        "title and artist; a copy in another format (FLAC and MP3) or in another album is fine, and so are the "
        "versions named in the title (Unplugged, Live, Remix…)",
    "Lo stesso brano più volte nello stesso album e nello stesso formato: di solito una copia in più da togliere; quale tenere lo decidi tu (Mostra i brani). Le copie in un altro formato (FLAC e MP3) e lo stesso brano in un altro album (una raccolta) non si segnalano.\n{0}":
        "The same track several times in the same album and the same format: usually an extra copy to remove; you "
        "decide which one to keep (Show the tracks). Copies in another format (FLAC and MP3) and the same track in "
        "another album (a compilation) are not reported.\n{0}",
    "1 brano":
        "1 track",
    "controllo file: {0}":
        "checking files: {0}",
    " Le copie inviate all'iPhone ne sono già ripulite. Applica la correzione lo toglie anche dai file del PC, dopo l'elenco dei file da approvare (i suoi valori passano prima nel tag ID3v2).":
        " The copies sent to the iPhone are already cleaned. Apply the fix removes it from the files on the PC too, "
        "after the list of files to approve (its values first go into the ID3v2 tag).",
    "Togli il tag ID3v1 dai file del PC":
        "Remove the ID3v1 tag from the files on the PC",
    "Togli il tag APE dai file del PC":
        "Remove the APE tag from the files on the PC",
    "Tag ID3v1":
        "ID3v1 tag",
    "Tag APE":
        "APE tag",
    "c'è":
        "present",
    "tolto":
        "removed",
    "Togli i vecchi tag dai file (prima vedi l'elenco da approvare; i loro valori passano nel tag ID3v2)":
        "Remove the old tags from the files (first you see the list to approve; their values go into the ID3v2 tag)",
    "{0} MP3 del PC con vecchi tag (ID3v1, APE)":
        "{0} MP3s on the PC with old tags (ID3v1, APE)",
    "Spenta: i file restano così. Le copie per l'iPhone ne sono comunque senza.":
        "Off: the files stay as they are. The copies for the iPhone are without them anyway.",
    "{0} MP3 con un vecchio tag ID3v1 diverso":
        "{0} MP3s with an old different ID3v1 tag",
    "Oltre al tag moderno (ID3v2) questi file hanno un vecchio tag ID3v1 con valori diversi: alcuni lettori, autoradio e app leggono quello e mostrano i valori vecchi.":
        "Besides the modern tag (ID3v2) these files have an old ID3v1 tag with different values: some players, car radios and apps read that one and show the old values.",
    "{0} MP3 con un tag APE":
        "{0} MP3s with an APE tag",
    "Questi file hanno anche un tag APE (di solito lasciato da programmi di normalizzazione del volume): alcuni lettori lo leggono al posto dell'ID3.":
        "These files also have an APE tag (usually left by volume normalisation programs): some players read it instead of the ID3.",
    "{0} file illeggibili":
        "{0} unreadable files",
    "Questi file non si possono leggere: sono danneggiati o non sono davvero file audio.":
        "These files cannot be read: they are damaged or not really audio files.",
    "Ricava titolo, album e artista dai nomi di file e cartelle":
        "Take title, album and artist from the file and folder names",
    "{0} brani senza titolo, album o artista in {1}":
        "{0} tracks without title, album or artist in {1}",
    "Senza album o artista i brani finiscono in \"Album sconosciuto\" / \"Artista sconosciuto\" e la collezione appare divisa.":
        "Without album or artist the tracks end up in \"Unknown album\" / \"Unknown artist\" and the collection looks split.",
    "{0} brani copiati due volte (\"… (2)\")":
        "{0} tracks copied twice (\"… (2)\")",
    "Accanto al file c'è una sua copia con \" (2)\" nel nome, nello stesso album: di solito una delle due è la versione vecchia, con i tag non aggiornati. Ascoltale e tieni la più recente.":
        "Next to the file there is a copy of it with \" (2)\" in the name, in the same album: usually one of the two is the old version, with tags not updated. Listen to them and keep the newer one.",
    "{0} brani presenti più volte nello stesso album":
        "{0} tracks present more than once in the same album",
    "Più file hanno lo stesso album, numero di traccia e titolo.":
        "Several files have the same album, track number and title.",
    "{0} — {1}: mancano {2} di traccia ({3} qui, l'album ne ha almeno {4})":
        "{0} — {1}: {2} missing among the track numbers ({3} here, the album has at least {4})",
    "1 numero":
        "1 number",
    "{0} numeri":
        "{0} numbers",
    "Mancano i numeri di traccia {0}. \"Verifica album\" controlla l'elenco completo su MusicBrainz.":
        "Track numbers {0} are missing. \"Check albums\" checks the full list on MusicBrainz.",
    "{0} — {1}: solo {2}":
        "{0} — {1}: only {2}",
    "Può essere un singolo, oppure un album di cui hai solo pochi brani, oppure brani di un album finiti in un album a parte per un tag scritto diversamente.":
        "It can be a single, or an album of which you have only a few tracks, or tracks of an album that ended up in a separate album because of a tag written differently.",
    "{0}: un album diviso in {1}":
        "{0}: an album split into {1}",
    "I brani di questa cartella risultano in album diversi: ":
        "The tracks of this folder are in different albums: ",
    ". Di solito l'\"Artista album\" manca o è scritto in modo diverso: per una compilation va messo \"Artisti vari\" su tutti i brani.":
        ". Usually the \"Album artist\" is missing or written differently: for a compilation set \"Various artists\" on all the tracks.",
    "Album \"{0}\", artista album \"{1}\" su tutti i brani":
        "Album \"{0}\", album artist \"{1}\" on all the tracks",
    "\"{0}\" anche come {1}":
        "\"{0}\" also as {1}",
    "\"{0}\" scritto in {1} modi diversi: {2}":
        "\"{0}\" written in {1} different ways: {2}",
    "\"{0}\" scritto in {1} modi diversi":
        "\"{0}\" written in {1} different ways",
    "Lo stesso album compare come: {0}. Maiuscole, punteggiatura o un \"CD 1\"/\"Disc 2\" nel nome lo dividono; il numero del disco va nel campo N. disco.":
        "The same album appears as: {0}. Capitals, punctuation or a \"CD 1\"/\"Disc 2\" in the name split it; the disc number goes in the Disc no. field.",
    "Album \"{0}\" e artista album \"{1}\" su tutti i brani, numero del disco dal nome":
        "Album \"{0}\" and album artist \"{1}\" on all the tracks, disc number from the name",
    "Artista album \"{0}\" e album \"{1}\" su tutti i brani":
        "Album artist \"{0}\" and album \"{1}\" on all the tracks",
    "\"{0}\" diviso tra {1} artisti":
        "\"{0}\" split among {1} artists",
    "L'album compare come: {0}. Se è una compilation, senza \"Artista album\" ogni artista forma un album a parte. Se invece sono album diversi con lo stesso nome, ignora.":
        "The album appears as: {0}. If it is a compilation, without \"Album artist\" every artist forms a separate album. If they are different albums with the same name, ignore it.",
    "Artista scritto in {0} modi: ":
        "Artist written in {0} ways: ",
    "Le varianti dividono la collezione dell'artista negli elenchi e sull'iPhone.":
        "The variants split the artist's collection in the lists and on the iPhone.",
    "Scrivi ovunque \"{0}\"":
        "Write \"{0}\" everywhere",
    "MusicBrainz: nomi d'artista dubbi ({0} di {1})":
        "MusicBrainz: doubtful artist names ({0} of {1})",
    "nomi degli artisti su MusicBrainz: {0}":
        "artist names on MusicBrainz: {0}",
    "nomi o alias dello stesso artista su MusicBrainz":
        "names or aliases of the same artist on MusicBrainz",
    "da controllare: ":
        "to check: ",
    "Lo stesso artista scritto in modi diversi: ":
        "The same artist written in different ways: ",
    "Forse lo stesso artista: ":
        "Maybe the same artist: ",
    "Le varianti dividono la collezione dell'artista negli elenchi e sull'iPhone ({0}). Vince la forma più usata.":
        "The variants split the artist's collection in the lists and on the iPhone ({0}). The most used form wins.",
    " L'album è anche diviso in più parti: correggi prima la divisione, poi ripeti la scansione.":
        " The album is also split into several parts: fix the split first, then run the check again.",
    "{0} | artist: {1} | album: {2} | {3}:{4} | {5} | folder: {6}":
        "{0} | artist: {1} | album: {2} | {3}:{4} | {5} | folder: {6}",
    "l'AI confronta {0} coppie di versioni forse diverse":
        "the AI compares {0} pairs of possibly different versions",
    "P{0}\n   A: {1}\n   B: {2}":
        "P{0}\n   A: {1}\n   B: {2}",
    "PAIRS\n":
        "PAIRS\n",
    "brani duplicati: {0}":
        "duplicate tracks: {0}",
    "stesso brano, file diversi":
        "same track, different files",
    "Lo stesso brano in più file. Può essere giusto (l'album originale e una raccolta, un MP3 e un FLAC tenuti apposta) oppure un doppione da togliere: quale tenere lo decidi tu (Mostra i brani).\n":
        "The same track in several files. It can be right (the original album and a compilation, an MP3 and a FLAC kept on purpose) or a duplicate to remove: you decide which to keep (Show the tracks).\n",
    "{0}: {1} in più copie":
        "{0}: {1} in several copies",
    "brani duplicati: l'AI ha visto le prime {0} coppie dubbie su {1}; le altre sono segnate \"da controllare\"":
        "duplicate tracks: the AI saw the first {0} doubtful pairs out of {1}; the others are marked \"to check\"",
    "{0} dell'iPhone senza file (fantasmi)":
        "{0} of the iPhone without a file (ghosts)",
    "Sono nell'elenco dell'app Musica, ma il loro file sull'iPhone non c'è: non si possono ascoltare. Toglili dalla scheda iPhone: Mostra → \"Senza file sull'iPhone\", tasto destro → Elimina dall'iPhone. Sul PC non cambia niente.":
        "They are in the Music app list, but their file is not on the iPhone: they cannot be played. Remove them from the iPhone tab: Show → \"Without a file on the iPhone\", right-click → Delete from the iPhone. Nothing changes on the PC.",
    "{0} brani sull'iPhone con tag diversi da quelli del PC":
        "{0} tracks on the iPhone with tags different from the PC",
    "Il brano è nell'app Musica dell'iPhone, ma titolo, artista, album, anno, genere o numeri non sono quelli del PC (per esempio dopo una modifica sul PC). Nella scheda PC, la colonna iPhone mostra le differenze.":
        "The track is in the iPhone Music app, but title, artist, album, year, genre or numbers are not those of the PC (for example after a change on the PC). In the PC tab, the iPhone column shows the differences.",
    "{0} — {1}: mancano {2} sull'iPhone":
        "{0} — {1}: {2} missing on the iPhone",
    "Sul PC l'album ha più brani di quelli nell'app Musica dell'iPhone.":
        "On the PC the album has more tracks than in the iPhone Music app.",
    "{0} brani sull'iPhone che non sono sul PC":
        "{0} tracks on the iPhone that are not on the PC",
    "Non c'è un brano con lo stesso artista, album e titolo nella Libreria del PC. Se vuoi conservarli, salvali sul PC dalla scheda iPhone (tasto destro → Salva su PC); a volte sono solo scritti in modo diverso.":
        "There is no track with the same artist, album and title in the PC Library. If you want to keep them, save them to the PC from the iPhone tab (right-click → Save to PC); sometimes they are just written differently.",
    "disco {0}: {1}":
        "disc {0}: {1}",
    "nessuno":
        "none",
    "A{0} | album artist: {1} | album: {2} | anni: {3} | brani: {4} | numeri: {5} | totale dichiarato: {6} | mancanti: {7} | cartella: {8} | generi: {9}":
        "A{0} | album artist: {1} | album: {2} | anni: {3} | brani: {4} | numeri: {5} | totale dichiarato: {6} | mancanti: {7} | cartella: {8} | generi: {9}",
    " | formati: {0}":
        " | formati: {0}",
    " | immagine CUE: {0} tracce in {1} file":
        " | immagine CUE: {0} tracce in {1} file",
    " Il CUE ha tutte le tracce in un file solo: dal catalogo solo album, artista dell'album e anno.":
        " The CUE has all the tracks in a single file: from the catalog only album, album artist and year.",
    " | altri artisti: {0}":
        " | altri artisti: {0}",
    "Imposta {0} su tutti i brani":
        "Set {0} on all the tracks",
    "Problema trovato dall'AI":
        "Problem found by the AI",
    "analisi AI {0} di {1}":
        "AI analysis {0} of {1}",
    "{0} | {1} | {2} | album: {3}":
        "{0} | {1} | {2} | album: {3}",
    "ALBUMS\n":
        "ALBUMS\n",
    "\n\nRULE FINDINGS\n":
        "\n\nRULE FINDINGS\n",
    "none":
        "none",
    "L'AI ritiene che non sia un problema":
        "The AI thinks it is not a problem",
    "nomi d'artista dubbi":
        "doubtful artist names",
    "brani duplicati":
        "duplicate tracks",
    " Correggi i brani sul PC (scheda PC).":
        " Fix the tracks on the PC (PC tab).",
    "Controllo di {0} — {1}":
        "Check of {0} — {1}",
    "{0} brani, {1} album, {2} problemi":
        "{0} tracks, {1} albums, {2} problems",
    "Analisi AI: {0}":
        "AI analysis: {0}",
    "Errore AI: {0}":
        "AI error: {0}",
    "Controllo interrotto: i risultati sono parziali":
        "Check interrupted: the results are partial",
    "    Correzione proposta: {0}":
        "    Proposed fix: {0}",
    "\n=== avvio {0}: qui sotto, se ci sono, i blocchi dell'interfaccia (più di {1} s) ===\n":
        "\n=== start {0}: below, if any, the freezes of the interface (more than {1} s) ===\n",
    "<br><b>Annullati: {0}</b> — i risultati sono quelli senza (tasto destro sugli album: Controlla con l'AI, Controlla online)":
        "<br><b>Cancelled: {0}</b> — the results are those without (right click on the albums: Check with the AI, "
        "Check online)",
    "Si corregge qui: lascia accese le caselle delle righe che vuoi e premi Applica le correzioni scelte":
        "It is fixed here: leave on the boxes of the rows you want and press Apply the chosen fixes",
    "Nessuna correzione automatica: leggi Cosa fare (sotto, o qui)":
        "No automatic fix: read What to do (below, or here)",
    "{0} automatiche, {1} a mano":
        "{0} automatic, {1} by hand",
    "{0} automatiche":
        "{0} automatic",
    "{0} a mano":
        "{0} by hand",
    "Problemi che si correggono qui (con le caselle) e problemi da sistemare a mano (Cosa fare, nel dettaglio sotto)":
        "Problems fixed here (with the boxes) and problems to sort out by hand (What to do, in the details below)",
    "automatica ({0})":
        "automatic ({0})",
    "a mano":
        "by hand",
    "si corregge nell'altro album":
        "fixed in the other album",
    "nell'altro album":
        "in the other album",
    "Qui c'è già la forma giusta: si corregge con la correzione automatica di {0}. Qui non c'è niente da fare.":
        "The right form is already here: it is fixed by the automatic fix of {0}. Nothing to do here.",
    "<p style='color:gray'><b>Si correggono nell'altro album</b> (qui c'è già la forma giusta, niente da fare):</p><ul>{0}</ul>":
        "<p style='color:gray'><b>Fixed in the other album</b> (the right form is already here, nothing to do):</p>"
        "<ul>{0}</ul>",
    "<p>Seleziona un album o un problema per vederne i dettagli e cosa fare.</p><p><b>Correzione automatica</b> (in verde): il problema ha righe con la casella; lascia accese quelle che vuoi e premi <i>Applica le correzioni scelte</i>. <b>A mano</b> (in arancione): il programma non lo corregge da solo; <i>Cosa fare</i> dice come.</p>":
        "<p>Select an album or a problem to see its details and what to do.</p><p><b>Automatic fix</b> (green): "
        "the problem has rows with a box; leave on the ones you want and press <i>Apply the chosen fixes</i>. <b>By "
        "hand</b> (orange): the program does not fix it by itself; <i>What to do</i> says how.</p>",
    "<p style='color:#1e8c3c'><b>Si correggono qui</b>: lascia accese le caselle delle righe che vuoi e premi <i>Applica le correzioni scelte</i>.</p><ul>{0}</ul>":
        "<p style='color:#1e8c3c'><b>Fixed here</b>: leave on the boxes of the rows you want and press <i>Apply the "
        "chosen fixes</i>.</p><ul>{0}</ul>",
    "<p style='color:#d28200'><b>Da fare a mano</b> (nessuna correzione automatica):</p><ul>{0}</ul>":
        "<p style='color:#d28200'><b>To do by hand</b> (no automatic fix):</p><ul>{0}</ul>",
    "AI disattivata dopo {0} errori di fila (si può cambiare nel profilo AI: Errori di fila prima di smettere)":
        "AI turned off after {0} errors in a row (it can be changed in the AI profile: Errors in a row before "
        "stopping)",
    "Premuto: si controlla tutto, la selezione della scheda {0} non conta (e non cambia). Alzato: si controlla la selezione della scheda.":
        "Pressed: everything is checked, the selection of the {0} tab does not count (and does not change). Raised: "
        "the selection of the tab is checked.",
    "Ferma l'invio all'iPhone: quello che è già sull'iPhone resta, il resto resta in attesa per il prossimo Applica":
        "Stops sending to the iPhone: what is already on the iPhone stays, the rest stays waiting for the next Apply",
    "Ferma: finisco l'album già cominciato":
        "Stop: finishing the album already started",
    "Regole":
        "Rules",
    "Ferma l'AI":
        "Stop the AI",
    "Ferma l'Analisi AI che va in background: i risultati restano quelli delle regole e della Verifica online (e quelli già applicati)":
        "Stops the AI analysis running in the background: the results stay those of the rules and of the Online "
        "check (and the ones already applied)",
    "Ferma la Verifica online (e l'Analisi AI che verrebbe dopo): le regole vanno comunque fino in fondo":
        "Stops the Online check (and the AI analysis that would come after): the rules still run to the end",
    "<b style='color:#d28200'>Analisi AI in corso, in background:</b> i suoi risultati si aggiungono man mano. Intanto puoi già applicare le correzioni.<br>":
        "<b style='color:#d28200'>AI analysis running in the background:</b> its results are added as they arrive. "
        "Meanwhile you can already apply the fixes.<br>",
    "Aspetta la fine dell'operazione in corso (o fermala).":
        "Wait for the end of the operation in progress (or stop it).",
    "Analisi AI fermata: i risultati sono quelli delle regole e della Verifica online":
        "AI analysis stopped: the results are those of the rules and of the Online check",
    "Aspetta la fine dell'Analisi AI in corso (o fermala).":
        "Wait for the end of the AI analysis in progress (or stop it).",
    "<b>▶ {0}</b>":
        "<b>▶ {0}</b>",
    " <span style='color: gray'>({0})</span>":
        " <span style='color: gray'>({0})</span>",
    "<span style='color: #1e8c3c'>✔ {0}</span>":
        "<span style='color: #1e8c3c'>✔ {0}</span>",
    "<span style='color: gray'>{0}</span>":
        "<span style='color: gray'>{0}</span>",
    "Ferma il controllo":
        "Stop the check",
    "Ferma l'Analisi AI e la Verifica online: le regole vanno comunque fino in fondo, e i risultati sono come se AI e Verifica online non fossero scelte":
        "Stops the AI analysis and the Online check: the rules still run to the end, and the results are as if AI "
        "and Online check had not been chosen",
    "Mi fermo…":
        "Stopping…",
    "<b style='color:#d28200'>Controllo in corso: i risultati arrivano man mano.</b> Applica le correzioni scelte si può usare alla fine.<br>":
        "<b style='color:#d28200'>Check in progress: the results arrive as they are found.</b> Apply the chosen "
        "fixes can be used at the end.<br>",
    "mai":
        "never",
    "In un controllo, dopo tanti errori di fila (nessuna risposta, risposta vuota…) l'AI smette: il resto del controllo va avanti senza, senza aspettare il server. 0 = non smette mai.":
        "In a check, after this many errors in a row (no answer, empty answer…) the AI stops: the rest of the check "
        "goes on without it, without waiting for the server. 0 = it never stops.",
    "Errori di fila prima di smettere":
        "Errors in a row before stopping",
    "tutto l'album":
        "the whole album",
    "differenze con il catalogo online":
        "differences with the online catalog",
    "vecchio tag ID3v1":
        "old ID3v1 tag",
    "tag APE":
        "APE tag",
    "file illeggibili":
        "unreadable files",
    "tag mancanti":
        "missing tags",
    "copie \"(2)\"":
        "\"(2)\" copies",
    "brani più volte nell'album":
        "tracks several times in the album",
    "numeri di traccia mancanti":
        "missing track numbers",
    "album con 1-2 brani":
        "albums with 1-2 tracks",
    "cartella divisa in più album":
        "folder split into several albums",
    "album scritto in modi diversi":
        "album written in different ways",
    "compilation divisa per artista":
        "compilation split by artist",
    "artista scritto in modi diversi":
        "artist written in different ways",
    "forse lo stesso artista":
        "maybe the same artist",
    "duetti":
        "duets",
    "tag diversi tra PC e iPhone":
        "different tags between PC and iPhone",
    "brani che mancano sull'iPhone":
        "tracks missing on the iPhone",
    "brani fantasma sull'iPhone":
        "ghost tracks on the iPhone",
    "Mostra anche quelli che vanno bene così ({0})":
        "Also show the ones that are fine as they are ({0})",
    "I problemi segnati \"va bene così\" (tasto destro): in grigio, e da lì si tolgono. Anche in Impostazioni → Controlli":
        "The problems marked \"fine as it is\" (right click): in grey, and they can be unmarked from there. Also in "
        "Settings → Checks",
    "va bene così":
        "fine as it is",
    "Segnato \"va bene così\": i controlli non lo mostrano più (tasto destro → Togli \"va bene così\")":
        "Marked \"fine as it is\": the checks do not show it any more (right click → Unmark \"fine as it is\")",
    "Va bene così: {0} (per questo album)":
        "Fine as it is: {0} (for this album)",
    "I controlli non mostreranno più questo tipo di problema per questo album, qualunque cosa propongano; si toglie da qui (Mostra anche quelli che vanno bene così) o da Impostazioni → Controlli":
        "The checks will no longer show this kind of problem for this album, whatever they propose; it can be "
        "unmarked from here (Also show the ones that are fine as they are) or from Settings → Checks",
    "Va bene così: tutto l'album ({0} album)":
        "Fine as it is: the whole album ({0} albums)",
    "Nessun problema di questi album si mostrerà più, e l'AI e la Verifica online li saltano":
        "No problem of these albums will be shown any more, and the AI and the Online check skip them",
    "Togli \"va bene così\"":
        "Unmark \"fine as it is\"",
    "Gli album segnati \"va bene così\" nei risultati dei Controlli (tasto destro): quel tipo di problema, o tutto l'album, non si mostra più, qualunque cosa propongano i controlli. Togli quelli che vuoi rivedere: vale con OK.":
        "The albums marked \"fine as it is\" in the results of the Checks (right click): that kind of problem, or the "
        "whole album, is no longer shown, whatever the checks propose. Remove the ones you want to see again: it "
        "takes effect with OK.",
    "Artista dell'album":
        "Album artist",
    "Che cosa va bene così":
        "What is fine as it is",
    "Da quando":
        "Since",
    "Togli quelli selezionati":
        "Remove the selected ones",
    "Nessun album segnato.":
        "No album marked.",
    "Controlla con l'AI ({0} album)":
        "Check with the AI ({0} albums)",
    "Di nuovo l'Analisi AI, solo su questi album: i loro risultati dell'AI si sostituiscono":
        "The AI analysis again, only on these albums: their AI results are replaced",
    "Controlla online ({0} album)":
        "Check online ({0} albums)",
    "Di nuovo la Verifica online, con i cataloghi scelti sopra, solo su questi album":
        "The Online check again, with the catalogs chosen above, only on these albums",
    "Questi album non sono tra quelli controllati.":
        "These albums are not among the ones checked.",
    "Scegli l'AI della scansione in Impostazioni → Generale.":
        "Choose the scan AI in Settings → General.",
    "Scegli almeno un catalogo sotto Verifica online.":
        "Choose at least one catalog under Online check.",
    "Analisi AI annullata: i risultati restano quelli di prima":
        "AI analysis cancelled: the results stay as before",
    "Analisi AI di {0} album":
        "AI analysis of {0} albums",
    "Verifica online annullata: i risultati restano quelli di prima":
        "Online check cancelled: the results stay as before",
    "Verifica online di {0} album":
        "Online check of {0} albums",
    "Analisi AI":
        "AI analysis",
    "Annullati: {0} (i risultati sono quelli senza)":
        "Cancelled: {0} (the results are those without)",
    # la linguetta Controlli: su cosa, cosa controllare, i risultati per album, dove vanno le correzioni
    "PC e iPhone":
        "PC and iPhone",
    "solo PC":
        "PC only",
    "solo iPhone":
        "iPhone only",
    "misto":
        "mixed",
    "Niente da controllare: nella scheda {0} non ci sono brani.":
        "Nothing to check: there are no tracks in the {0} tab.",
    "Si controlla: <b>{0} brani</b> selezionati nella lista della scheda {1}, da {2} album.":
        "Checking: <b>{0} tracks</b> selected in the list of the {1} tab, from {2} albums.",
    "Si controlla l'album <b>{0} — {1}</b> scelto nella scheda {2} ({3} brani).":
        "Checking the album <b>{0} — {1}</b> chosen in the {2} tab ({3} tracks).",
    "Si controlla: <b>{0} album</b> scelti nella scheda {1} ({2} brani).":
        "Checking: <b>{0} albums</b> chosen in the {1} tab ({2} tracks).",
    "Si controlla l'artista <b>{0}</b> scelto nella scheda {1}: {2} album, {3} brani.":
        "Checking the artist <b>{0}</b> chosen in the {1} tab: {2} albums, {3} tracks.",
    "Si controlla: <b>{0} artisti</b> scelti nella scheda {1}: {2} album, {3} brani.":
        "Checking: <b>{0} artists</b> chosen in the {1} tab: {2} albums, {3} tracks.",
    "Si controlla: <b>tutti i brani della scheda PC</b> ({0}): {1} album, {2} brani.":
        "Checking: <b>all the tracks of the PC tab</b> ({0}): {1} albums, {2} tracks.",
    "Si controlla: <b>tutta la musica dell'iPhone</b>: {0} album, {1} brani.":
        "Checking: <b>all the music on the iPhone</b>: {0} albums, {1} tracks.",
    " · e altri {0}":
        " · and {0} more",
    "Nessun catalogo ha dato questo album: {0}.":
        "No catalog gave this album: {0}.",
    "Edizione di {0}: {1}.":
        "Edition from {0}: {1}.",
    " Scelta dall'AI ({0}).":
        " Chosen by the AI ({0}).",
    "{0}: mancano {1} di {2} brani ({3})":
        "{0}: {1} of {2} tracks missing ({3})",
    "{0} Mancano: {1}{2}.":
        "{0} Missing: {1}{2}.",
    "{0}: tag diversi da {1} su {2} brani":
        "{0}: tags different from {1} on {2} tracks",
    "I tag di {0}":
        "The tags of {0}",
    "Altri problemi":
        "Other problems",
    "non è stato messo da un computer: i suoi tag non si cambiano":
        "it was not put there by a computer: its tags cannot be changed",
    "sull'iPhone senza il file sul PC non si cambia: {0}":
        "on the iPhone without the file on the PC this cannot be changed: {0}",
    "PC (i brani della scheda PC)":
        "PC (the tracks of the PC tab)",
    "iPhone (la musica dell'app Musica)":
        "iPhone (the music of the Music app)",
    "<b>Su cosa:</b>":
        "<b>On what:</b>",
    "solo sugli album con problemi (gli altri si saltano)":
        "only on the albums with problems (the others are skipped)",
    "l'AI guarda la tabella degli album: conferma o scarta i problemi delle regole, ne trova altri e propone le correzioni; con la Verifica online sceglie tra edizioni dubbie":
        "the AI looks at the table of the albums: it confirms or discards the problems found by the rules, finds "
        "others and proposes the fixes; with the Online check it chooses between doubtful editions",
    "Verifica online":
        "Online check",
    "solo sugli album con problemi (spenta: tutti gli album, è lento)":
        "only on the albums with problems (off: all the albums, it is slow)",
    "confronta gli album con i cataloghi su internet: brani che mancano anche se i numeri tornano, i tag giusti":
        "compares the albums with the catalogs on the internet: tracks missing even when the numbers add up, the "
        "right tags",
    "Cataloghi, in quest'ordine finché uno dà l'album completo:":
        "Catalogs, in this order until one gives the whole album:",
    "Senza regole nessun album ha \"problemi\": l'AI e la Verifica online guardano tutti gli album di quello che si controlla.":
        "Without rules no album has \"problems\": the AI and the Online check look at all the albums being checked.",
    "Solo AI":
        "AI only",
    "Spegne gli altri controlli, accende l'Analisi AI su tutto quello che si controlla e parte":
        "Turns off the other checks, turns on the AI analysis on everything being checked and starts",
    "<b>Cosa controllare</b>":
        "<b>What to check</b>",
    "Modifica la selezione nella scheda {0}":
        "Change the selection in the {0} tab",
    "Usa la selezione della scheda {0}":
        "Use the selection of the {0} tab",
    "Tutto il PC":
        "The whole PC",
    "Tutto l'iPhone":
        "The whole iPhone",
    "Come la barra delle azioni: i brani selezionati nella lista della scheda {0}; se non ce ne sono, gli artisti o gli album scelti negli elenchi; se non c'è niente, tutto.":
        "Like the action bar: the tracks selected in the list of the {0} tab; if there are none, the artists or "
        "albums chosen in the lists; if there is nothing, everything.",
    "Analisi AI ({0})":
        "AI analysis ({0})",
    "Analisi AI (scegli un profilo in Impostazioni → Generale)":
        "AI analysis (choose a profile in Settings → General)",
    "Imposta la variabile {0} (nel file delle variabili o in Windows) con un token personale di Discogs, poi riavvia":
        "Set the variable {0} (in the variables file or in Windows) to a personal Discogs token, then restart",
    "Album, problema, brano":
        "Album, problem, track",
    "Dove":
        "Where",
    "Ora":
        "Now",
    "Applica le correzioni scelte":
        "Apply the chosen fixes",
    "Dove va ogni correzione dipende da dove c'è il brano.":
        "Where each fix goes depends on where the track is.",
    "Sul PC: scrivi nei file (prima vedi l'elenco di ogni file e campo, da approvare)":
        "On the PC: write into the files (first you see the list of every file and field, to approve)",
    "Sull'iPhone: Usa i tag da PC a iPhone, in attesa (parte con Applica)":
        "On the iPhone: Use the tags from PC to iPhone, waiting (starts with Apply)",
    "Spenta: sul PC le correzioni restano in sospeso, solo per le copie (i file non cambiano).":
        "Off: on the PC the fixes stay pending, only for the copies (the files do not change).",
    "{0} brani sul PC e sull'iPhone (collegati)":
        "{0} tracks on the PC and on the iPhone (linked)",
    "{0} brani solo sul PC":
        "{0} tracks only on the PC",
    "{0} brani solo sull'iPhone":
        "{0} tracks only on the iPhone",
    "Cambia i tag sull'iPhone, in attesa (parte con Applica). Sul PC non c'è niente da cambiare.":
        "Change the tags on the iPhone, waiting (starts with Apply). There is nothing to change on the PC.",
    "Non si possono fare:\n{0}":
        "These cannot be done:\n{0}",
    "Ogni scrittura sull'iPhone va in attesa e parte con Applica (barra blu), dove ogni azione si toglie con la ✕. Nei file del PC si scrive solo dopo l'elenco di ogni file e campo (Modifica N file; non si può annullare).":
        "Every write to the iPhone waits and starts with Apply (blue bar), where each action can be removed with the "
        "✕. The PC files are written only after the list of every file and field (Change N files; it cannot be "
        "undone).",
    "Continua":
        "Continue",
    "Applica le correzioni scelte…":
        "Apply the chosen fixes…",
    "Seleziona i brani degli album o dei problemi scelti nella loro scheda":
        "Select the tracks of the chosen albums or problems in their tab",
    "Controlla di nuovo questi album":
        "Check these albums again",
    "Lo stesso controllo, con le scelte di sopra, solo sugli album scelti qui":
        "The same check, with the choices above, only on the albums chosen here",
    "Dettagli della verifica online":
        "Details of the online check",
    "Le tracce dell'edizione trovata e i tuoi file; un'altra edizione, la copertina":
        "The tracks of the edition found and your files; another edition, the cover",
    "<b>{0} album con problemi</b> su {1} controllati ({2} brani, {3}): {4} problemi":
        "<b>{0} albums with problems</b> out of {1} checked ({2} tracks, {3}): {4} problems",
    "{0} correzioni scelte":
        "{0} fixes chosen",
    "Nessuna correzione scelta":
        "No fix chosen",
    "<br><i>Cosa fare:</i> {0}":
        "<br><i>What to do:</i> {0}",
    "<p>Seleziona un album o un problema per vederne i dettagli e cosa fare. Le caselle scelgono le correzioni da applicare.</p>":
        "<p>Select an album or a problem to see its details and what to do. The boxes choose the fixes to apply.</p>",
    "<p><b>L'AI ritiene che non sia un problema:</b> {0} (le sue correzioni sono spente)</p>":
        "<p><b>The AI thinks it is not a problem:</b> {0} (its fixes are off)</p>",
    "<p><b>{0} file in questo album:</b></p><ul>{1}</ul>{2}":
        "<p><b>{0} files in this album:</b></p><ul>{1}</ul>{2}",
    "Applica le correzioni":
        "Apply the fixes",
    "Correzioni salvate in sospeso su {0} brani del PC: i file non cambiano":
        "Fixes saved as pending on {0} PC tracks: the files do not change",
    "Correzione applicata":
        "Fix applied",
    "Controlla la musica  <span style='color: gray; font-weight: normal'>F6</span>":
        "Check the music  <span style='color: gray; font-weight: normal'>F6</span>",
    "Qui compaiono i risultati del controllo, per album: i problemi, cosa fare e le correzioni da applicare.":
        "The results of the check appear here, by album: the problems, what to do and the fixes to apply.",
    "verifica online: {0} — {1}":
        "online check: {0} — {1}",
    "Non c'è niente da controllare.":
        "There is nothing to check.",
    "PC, {0} brani":
        "PC, {0} tracks",
    "iPhone, {0} brani ({1})":
        "iPhone, {0} tracks ({1})",
    "Diversi dal catalogo online":
        "Different from the online catalog",
    "online":
        "online",
    "Se i brani ti servono, aggiungili alla cartella dell'album. Se l'edizione trovata non è la tua, Dettagli della verifica online per sceglierne un'altra.":
        "If you need the tracks, add them to the album folder. If the edition found is not yours, Details of the "
        "online check to choose another one.",
    "Applica le correzioni scelte scrive i tag del catalogo. Controlla prima l'edizione (Dettagli della verifica online): se non è la tua, sceglierne un'altra cambia le correzioni.":
        "Apply the chosen fixes writes the tags of the catalog. Check the edition first (Details of the online "
        "check): if it is not yours, choosing another one changes the fixes.",
    "Controlla che artista e album siano scritti bene, poi riprova; oppure prova un altro catalogo.":
        "Check that artist and album are written correctly, then try again; or try another catalog.",
    "Applica le correzioni scelte scrive i tag del catalogo; controlla prima l'edizione.":
        "Apply the chosen fixes writes the tags of the catalog; check the edition first.",
    "Nessuna copertina disponibile per questa edizione":
        "No cover available for this edition",
    "si scrivono nel file i tag di {0} dei campi scelti (la copertina va solo sulle copie per l'iPhone)":
        "the tags of {0} for the chosen fields are written into the file (the cover goes only on the copies for the "
        "iPhone)",
    "si scrivono nel file i tag dell'iPhone dei campi scelti":
        "the iPhone tags of the chosen fields are written into the file",
    "<b>Questi {0} file del PC verranno modificati</b>: {1}. Non si può annullare.":
        "<b>These {0} files on the PC will be changed</b>: {1}. This cannot be undone.",
    "Solo per l'iPhone: i file del PC non cambiano e la differenza resta da allineare. Anche nei file del PC: prima vedi l'elenco di ogni file e campo che cambia, e decidi.":
        "Only for the iPhone: the files on the PC do not change and the difference is left to align. Also in the PC "
        "files: first you see the list of every file and field that changes, and you decide.",
    "Solo per l'iPhone":
        "Only for the iPhone",
    "Anche nei file del PC…":
        "Also in the PC files…",
    "Nei file del PC non c'è niente da cambiare.":
        "There is nothing to change in the PC files.",
    "{0}: modifica dei file del PC":
        "{0}: changing the PC files",
    "File del PC non modificati: le correzioni valgono solo per l'iPhone":
        "PC files not changed: the fixes are only for the iPhone",
    "Applicare queste correzioni?\n\n{0}":
        "Apply these fixes?\n\n{0}",
    "si scrivono nel file le correzioni dei campi scelti":
        "the fixes of the chosen fields are written into the file",
    "    Cosa fare: {0}":
        "    What to do: {0}",
    "<p><b>Cosa fare:</b> {0}</p>":
        "<p><b>What to do:</b> {0}</p>",
    "Verifica online questi album":
        "Check these albums online",
    "Verifica album online, con le scelte del suo riquadro, sugli album interi dei problemi selezionati (non su quelli scelti nella scheda PC)":
        "Check albums online, with the choices of its box, on the whole albums of the selected problems (not on the "
        "ones chosen in the PC tab)",
    "<b>Verificare l'album {0}</b> (scelto negli elenchi della scheda PC).":
        "<b>Check the album {0}</b> (chosen in the lists of the PC tab).",
    "<br>Per gli album dei problemi trovati da Controlla la musica: selezionali nei risultati e premi <i>Verifica online questi album</i>.":
        "<br>For the albums of the problems found by Check the music: select them in the results and press <i>Check "
        "these albums online</i>.",
    "Mostra i brani. Se sono davvero lo stesso brano, tieni una copia e sposta l'altra fuori dalle cartelle della musica con Esplora file (il programma non cancella i file del PC). Se sono due versioni diverse tenute apposta, scrivi la versione nel titolo (Cambia i tag: \"(Live)\", \"(Unplugged)\"…) e non saranno più segnalate. Per i doppioni sull'iPhone: scheda iPhone, Mostra → \"Doppioni: stessa canzone nello stesso album\".":
        "Show the tracks. If they really are the same track, keep one copy and move the other out of the music "
        "folders with File Explorer (the program never deletes files on the PC). If they are two different versions "
        "kept on purpose, write the version in the title (Change the tags: \"(Live)\", \"(Unplugged)\"…) and they will "
        "not be reported any more. For the duplicates on the iPhone: iPhone tab, Show → \"Duplicates: same song in "
        "the same album\".",
    "Mostra i brani e prova ad aprirli in Esplora file. Se sono su OneDrive: tasto destro → Mantieni sempre su questo dispositivo. Se sono danneggiati, ricopiali dall'originale o riscaricali, poi Rileggi (F5).":
        "Show the tracks and try to open them in File Explorer. If they are on OneDrive: right click → Always keep on "
        "this device. If they are damaged, copy them again from the original or download them again, then Reload "
        "(F5).",
    "Mostra i brani, poi Cambia i tag (tasto E) e scrivi titolo, album e artista.":
        "Show the tracks, then Change the tags (E key) and write title, album and artist.",
    "Per tenerli: scheda iPhone, tasto destro → Copia da iPhone a PC. Se non servono: Elimina dall'iPhone, poi Applica. Se sul PC ci sono ma scritti in modo diverso, correggi i tag sul PC.":
        "To keep them: iPhone tab, right click → Copy from iPhone to PC. If you don't need them: Delete from the "
        "iPhone, then Apply. If they are on the PC but written differently, fix the tags on the PC.",
    "Niente di urgente: le copie inviate all'iPhone sono già senza il vecchio tag. Per pulire anche i file del PC: Applica la correzione, poi approva l'elenco dei file (il tag ID3v1 si toglie, i valori restano nell'ID3v2).":
        "Nothing urgent: the copies sent to the iPhone are already without the old tag. To clean the files on the PC "
        "too: Apply the fix, then approve the list of files (the ID3v1 tag is removed, the values stay in the ID3v2).",
    "Niente di urgente: le copie inviate all'iPhone sono già senza il tag APE. Per pulire anche i file del PC: Applica la correzione, poi approva l'elenco dei file (il tag APE si toglie, i valori restano nell'ID3v2).":
        "Nothing urgent: the copies sent to the iPhone are already without the APE tag. To clean the files on the PC "
        "too: Apply the fix, then approve the list of files (the APE tag is removed, the values stay in the ID3v2).",
    "Applica la correzione (se c'è) ricava i tag dai nomi di file e cartelle. Altrimenti Mostra i brani, poi Cambia i tag (tasto E) e scrivi titolo, album e artista.":
        "Apply the fix (if there is one) takes the tags from the file and folder names. Otherwise Show the tracks, "
        "then Change the tags (E key) and write title, album and artist.",
    "Mostra i brani e confronta le due copie (tag, durata, qualità nell'editor dei tag). Tieni la migliore e sposta l'altra fuori dalle cartelle della musica con Esplora file (il programma non cancella i file del PC).":
        "Show the tracks and compare the two copies (tags, length, quality in the tag editor). Keep the best one and "
        "move the other out of the music folders with File Explorer (the program never deletes files on the PC).",
    "Mostra i brani. Se sono lo stesso brano, tieni una copia e sposta l'altra fuori dalle cartelle della musica con Esplora file. Se sono brani diversi, titolo o numero di traccia sono sbagliati: correggili con Cambia i tag (tasto E).":
        "Show the tracks. If they are the same track, keep one copy and move the other out of the music folders with "
        "File Explorer. If they are different tracks, the title or track number is wrong: fix it with Change the tags "
        "(E key).",
    "Premi Verifica online questi album: i cataloghi dicono quali brani mancano e quali sono i tag giusti. Se i brani mancano davvero, aggiungili alla cartella; se è sbagliato il numero di traccia, correggilo con Cambia i tag.":
        "Press Check these albums online: the catalogs tell which tracks are missing and which tags are right. If "
        "the tracks are really missing, add them to the folder; if the track number is wrong, fix it with Change the "
        "tags.",
    "Se è un singolo, o vuoi solo questi brani, va bene così. Se sono brani di un album più grande, rendi album e artista dell'album uguali a quelli degli altri brani (Cambia i tag), oppure premi Verifica online questi album.":
        "If it is a single, or you only want these tracks, it is fine. If they are tracks of a bigger album, make "
        "album and album artist the same as the other tracks (Change the tags), or press Check these albums online.",
    "Applica la correzione mette lo stesso album e lo stesso artista dell'album su tutti i brani della cartella. Se la cartella contiene davvero album diversi, ignora.":
        "Apply the fix puts the same album and album artist on all the tracks of the folder. If the folder really "
        "holds different albums, ignore it.",
    "Applica la correzione unifica il nome dell'album e sposta \"CD 1\" / \"Disc 2\" nel numero del disco.":
        "Apply the fix makes the album name the same and moves \"CD 1\" / \"Disc 2\" into the disc number.",
    "Se è una compilation: Applica la correzione (se c'è), oppure Mostra i brani e Cambia i tag con artista dell'album \"Artisti vari\" su tutti. Se sono album diversi che si chiamano allo stesso modo, ignora.":
        "If it is a compilation: Apply the fix (if there is one), or Show the tracks and Change the tags with album "
        "artist \"Various artists\" on all of them. If they are different albums with the same name, ignore it.",
    "Applica la correzione scrive ovunque la forma più usata. Per sceglierne un'altra: Mostra i brani e Cambia i tag.":
        "Apply the fix writes the most used form everywhere. To choose another one: Show the tracks and Change the "
        "tags.",
    "Se è davvero lo stesso artista: Applica la correzione (vince la forma più usata). Se non sei sicuro, accendi MusicBrainz o l'AI e ripeti il controllo. Se sono artisti diversi, ignora.":
        "If it really is the same artist: Apply the fix (the most used form wins). If you are not sure, turn on "
        "MusicBrainz or the AI and run the check again. If they are different artists, ignore it.",
    "Mostra i brani, poi nella scheda PC Usa i tag da PC a iPhone e Applica. Se sono giusti quelli dell'iPhone: scheda iPhone, Usa i tag da iPhone a PC.":
        "Show the tracks, then in the PC tab Use the tags from PC to iPhone and Apply. If the iPhone ones are right: "
        "iPhone tab, Use the tags from iPhone to PC.",
    "Mostra i brani, poi Copia da PC a iPhone e Applica. Se sull'iPhone non li vuoi, ignora.":
        "Show the tracks, then Copy from PC to iPhone and Apply. If you don't want them on the iPhone, ignore it.",
    "Scheda iPhone: Mostra → \"Senza file sull'iPhone (fantasmi)\", seleziona i brani, Elimina dall'iPhone e Applica.":
        "iPhone tab: Show → \"Without a file on the iPhone (ghosts)\", select the tracks, Delete from the iPhone and "
        "Apply.",
    "Mostra i brani e confronta i tag con Cambia i tag (tasto E).":
        "Show the tracks and compare the tags with Change the tags (E key).",
    "Premi Verifica online questi album: i cataloghi dicono quali brani mancano.":
        "Press Check these albums online: the catalogs tell which tracks are missing.",
    "Applica la correzione (se c'è); altrimenti Mostra i brani e rendi uguali album e artista dell'album con Cambia i tag. Se l'AI si sbaglia, ignora.":
        "Apply the fix (if there is one); otherwise Show the tracks and make album and album artist the same with "
        "Change the tags. If the AI is wrong, ignore it.",
    "    … e altri {0}":
        "    … and {0} more",
    "File delle variabili rinominato in {0} (MYCOPIASTIMP3_… -> MYEASYMP3TOIPHONE_…)":
        "Variables file renamed to {0} (MYCOPIASTIMP3_… -> MYEASYMP3TOIPHONE_…)",
    "{0} chiavi spostate nel credential store da {1} a {2}":
        "{0} keys moved in the credential store from {1} to {2}",
    "Impostazioni della versione precedente (registro di Windows) copiate in {0}":
        "Settings of the previous version (Windows registry) copied to {0}",
    "{0} ignorata: non è un percorso completo. La cartella dati è {1}":
        "{0} ignored: not a full path. The data folder is {1}",
    "Creato il profilo AI \"{0}\" (Ollama su questo computer) per la scansione":
        "Created the AI profile \"{0}\" (Ollama on this computer) for the scan",
    "La cartella dati non si può usare ({0}: {1}): il programma si ferma. Controlla la cartella, o la variabile {2} che la sceglie.":
        "The data folder cannot be used ({0}: {1}): the program stops. Check the folder, or the variable {2} that chooses it.",
    "Tracce totali":
        "Total tracks",
    "Dischi totali":
        "Total discs",
    "{0}: la cartella è in sola lettura, il file sul PC non si modifica":
        "{0}: the folder is read-only, the file on the PC is not modified",
    "TrackTags":
        "TrackTags",
    "Impossibile leggere {0}: {1}":
        "Cannot read {0}: {1}",
    "Formato non supportato: {0}":
        "Unsupported format: {0}",
    "albumartist":
        "albumartist",
    "date":
        "date",
    "tracknumber":
        "tracknumber",
    "discnumber":
        "discnumber",
    "tracktotal":
        "tracktotal",
    "totaltracks":
        "totaltracks",
    "disctotal":
        "disctotal",
    "totaldiscs":
        "totaldiscs",
    "length":
        "length",
    "Impossibile salvare {0}: {1}":
        "Cannot save {0}: {1}",
    "APIC":
        "APIC",
    "Cover":
        "Cover",
    "Copertina non supportata per i file {0}":
        "Cover not supported for {0} files",
    "Impossibile salvare la copertina di {0}: {1}":
        "Cannot save the cover of {0}: {1}",
    "git":
        "git",
    "HEAD":
        "HEAD",
    "status":
        "status",
    "log":
        "log",
    "{0}.{1}-dev ({2})":
        "{0}.{1}-dev ({2})",
    "Lingua dell'interfaccia":
        "Interface language",
    "Vale dal prossimo avvio del programma. Il README resta in italiano.":
        "It applies from the next start of the program. The README stays in Italian.",
    'certo':
        'certain',
    'molto probabile':
        'very likely',
    'probabile':
        'likely',
    'da controllare':
        'to check',
    'cartella "{0}": stesso titolo, numero e durata':
        'folder "{0}": same title, number and duration',
    'cartella "{0}": stesso titolo e durata':
        'folder "{0}": same title and duration',
    'cartella "{0}": titolo simile, stessa durata':
        'folder "{0}": similar title, same duration',
    'nomi delle cartelle':
        'folder names',
    'deezer':
        'deezer',
    'apple':
        'apple',
    'discogs':
        'discogs',
    'musicbrainz':
        'musicbrainz',
    'MusicBrainz':
        'MusicBrainz',
    'Non trovato su {0}':
        'Not found on {0}',
    'connessione a {0} non riuscita ({1})':
        'connection to {0} failed ({1})',
    '{0} ha risposto con dati non validi':
        '{0} answered with invalid data',
    '{0} è sovraccarico in questo momento: riprova tra qualche minuto':
        '{0} is overloaded right now: try again in a few minutes',
    "{0} ha risposto con l'errore {1}":
        '{0} answered with error {1}',
    'Deezer':
        'Deezer',
    'Apple Music':
        'Apple Music',
    'lookup':
        'lookup',
    'song':
        'song',
    'Discogs':
        'Discogs',
    'Discogs token={0}':
        'Discogs token={0}',
    'Discogs vuole un token personale: la variabile {0} non è impostata':
        'Discogs needs a personal token: the variable {0} is not set',
    'release':
        'release',
    'PC: {0} - {1}, {2} files:':
        'PC: {0} - {1}, {2} files:',
    'cartella':
        'folder',
    'Tutti i brani senza sorgente ({0})':
        'All tracks without a source ({0})',
    'I brani selezionati ({0}), anche quelli che hanno già una sorgente':
        'The selected tracks ({0}), also those that already have a source',
    'Tutta la Libreria ({0})':
        'The whole Library ({0})',
    "Nome della cartella, titolo, numero e durata (veloce: non legge l'audio)":
        'Folder name, title, number and duration (fast: does not read the audio)',
    "Impronta dell'audio, per i brani non trovati dal nome della cartella (al più {0} da leggere dall'iPhone: circa {1} minuti; quelle lette si ricordano)":
        'Audio fingerprint, for the tracks the folder name did not find (at most {0} to read from the iPhone: about {1} minutes; the ones read are remembered)',
    "Impronta dell'audio: solo quelle già lette (l'iPhone non è connesso)":
        'Audio fingerprint: only those already read (the iPhone is not connected)',
    "Impronta dell'audio (già lette tutte: veloce)":
        'Audio fingerprint (all already read: fast)',
    'AI per i dubbi ({0})':
        'AI for the doubtful ones ({0})',
    "AI per i dubbi (scegli l'AI della scansione in Impostazioni)":
        'AI for the doubtful ones (choose the scan AI in Settings)',
    'Dove cercare (con le sottocartelle)':
        'Where to search (with subfolders)',
    'Come, in ordine':
        'How, in order',
    "Alla fine vedi tutte le proposte, con la loro certezza e le spunte, prima di associare. Un brano senza spunta resta com'è; né i brani dell'iPhone né i file del PC cambiano.":
        'At the end you see all the proposals, with their certainty and check marks, before linking. A track without a check mark stays as it is; neither the iPhone tracks nor the PC files change.',
    'Cerca':
        'Search',
    'Dove cercare le sorgenti (anche nelle sottocartelle)':
        'Where to search for the sources (also in subfolders)',
    "<b>{0}</b> brani dell'iPhone con una sorgente proposta sul PC ({1} già spuntati perché certi o molto probabili).":
        '<b>{0}</b> iPhone tracks with a proposed source on the PC ({1} already checked because certain or very likely).',
    "{0} con l'impronta dell'audio (certi).":
        '{0} with the audio fingerprint (certain).',
    "{0} dal nome della cartella, senza leggere l'audio.":
        '{0} from the folder name, without reading the audio.',
    "<span style='color:#c33'><b>{0}</b> brani non trovati</span> (in rosso): restano <i>senza sorgente</i>, a meno che non scegli tu il file.":
        "<span style='color:#c33'><b>{0}</b> tracks not found</span> (in red): they stay <i>without a source</i>, unless you choose the file.",
    'Certezza':
        'Certainty',
    'Per la riga selezionata: scegli tu il file del PC (anche per un brano non trovato)':
        'For the selected row: choose the PC file yourself (also for a track not found)',
    "Associare scrive solo il registro della provenienza (sul PC e sull'iPhone): né i brani dell'iPhone né i file del PC cambiano. Un brano senza spunta resta com'è.":
        'Linking writes only the provenance register (on the PC and on the iPhone): neither the iPhone tracks nor the PC files change. A track without a check mark stays as it is.',
    'nessun file simile':
        'no similar file',
    'scelto da te':
        'chosen by you',
    'Deezer: veloce, gratis, senza chiave':
        'Deezer: fast, free, no key',
    "Apple Music: i nomi che usa l'app Musica dell'iPhone; più lento (circa 20 richieste al minuto)":
        'Apple Music: the names the iPhone Music app uses; slower (about 20 requests a minute)',
    'Discogs: tante edizioni, anche rare e in vinile; vuole un token personale':
        'Discogs: many editions, also rare and vinyl ones; needs a personal token',
    'MusicBrainz: il più completo, ma lento (una richiesta al secondo)':
        'MusicBrainz: the most complete, but slow (one request a second)',
    "<b>Cosa succede dopo.</b> La verifica va in background: puoi continuare a usare il programma (la barra di stato dice a che punto è, <i>Ferma</i> la interrompe). L'icona accanto a ogni album nell'elenco Album ne dice l'esito man mano. Alla fine si apre la finestra dei risultati: per ogni album le tracce dell'edizione trovata e i tuoi file, le tracce mancanti in rosso; puoi scegliere un'altra edizione e <i>Correggere i tag</i> con quei dati e la copertina (restano in sospeso, per le copie: i file del PC non cambiano). La riapri con <i>Risultati della verifica</i> nella barra di stato.":
        '<b>What happens next.</b> The check runs in the background: you can keep using the program (the status bar tells how far it is, <i>Stop</i> interrupts it). The icon next to each album in the Album list shows its result as it arrives. At the end the results window opens: for each album the tracks of the edition found and your files, the missing tracks in red; you can choose another edition and <i>Fix the tags</i> with its data and the cover (they stay pending, for the copies: the PC files do not change). Reopen it with <i>Check results</i> in the status bar.',
    "<i>Verifica album online</i> confronta i tuoi album con un catalogo su internet: dice se manca qualche brano e propone i tag giusti e la copertina. <i>Controlla la musica</i> invece confronta i tuoi brani tra loro (e con l'iPhone), senza cataloghi: doppioni, artisti scritti in modi diversi, album divisi, tag mancanti.":
        '<i>Check albums online</i> compares your albums with a catalog on the internet: it tells whether a track is missing and proposes the right tags and the cover. <i>Check the music</i> instead compares your tracks with each other (and with the iPhone), without catalogs: duplicates, artists written in different ways, split albums, missing tags.',
    'Verifica album online':
        'Check albums online',
    '<b>Verificare {0} album</b> (quelli scelti negli elenchi, o tutti).<br>':
        '<b>Check {0} albums</b> (those chosen in the lists, or all).<br>',
    "Cataloghi da usare. Con più cataloghi si provano in quest'ordine, album per album, finché uno dà l'album completo:":
        'Catalogs to use. With more than one they are tried in this order, album by album, until one gives the complete album:',
    'Imposta la variabile {0} (nel file delle variabili o in Windows) con un token personale di Discogs (discogs.com, Impostazioni, Sviluppatori), poi riavvia':
        'Set the variable {0} (in the variables file or in Windows) to a personal Discogs token (discogs.com, Settings, Developers), then restart',
    ' ({0} non impostata)':
        ' ({0} not set)',
    'AI per scegliere tra edizioni dubbie ({0})':
        'AI to choose between doubtful editions ({0})',
    "AI per scegliere tra edizioni dubbie (scegli l'AI della scansione in Impostazioni)":
        'AI to choose between doubtful editions (choose the scan AI in Settings)',
    "Solo quando due edizioni di un album sono ugualmente probabili: l'AI riceve titoli e numero dei brani e le edizioni trovate, e sceglie":
        'Only when two editions of an album are equally likely: the AI gets the titles and number of the tracks and the editions found, and chooses',
    'Verifica':
        'Check',
    'Circa {0} minuti con {1}':
        'About {0} minutes with {1}',
    ', di più per gli album che vanno cercati anche negli altri cataloghi':
        ', more for the albums that must be searched in the other catalogs too',
    'Scegli almeno un catalogo':
        'Choose at least one catalog',
    'Verifica album online: i risultati':
        'Check albums online: the results',
    'Edizione:':
        'Edition:',
    'Titolo nel catalogo':
        'Title in the catalog',
    'Imposta titolo, numero traccia/disco, album, artista album e anno dei brani riconosciuti secondo il catalogo (in sospeso: i file non cambiano)':
        'Sets title, track/disc number, album, album artist and year of the recognized tracks from the catalog (pending: the files do not change)',
    'Apri nel catalogo':
        'Open in the catalog',
    "Per ogni album: le tracce dell'edizione trovata e i tuoi file (le mancanti in rosso). Puoi scegliere un'altra edizione e correggere i tag con i suoi dati: restano in sospeso e valgono per le copie (iPhone, esportazione), i file del PC non cambiano.":
        'For each album: the tracks of the edition found and your files (the missing ones in red). You can choose another edition and fix the tags with its data: they stay pending and apply to the copies (iPhone, export), the PC files do not change.',
    'Provati in ordine: ':
        'Tried in order: ',
    "Edizione scelta dall'AI. {0}":
        'Edition chosen by the AI. {0}',
    'Edizione su {0}:':
        'Edition on {0}:',
    'Apri su {0}':
        'Open on {0}',
    'Aggiornare i tag di {0} brani con i dati di {1}?\n\n{2}':
        'Update the tags of {0} tracks with the data of {1}?\n\n{2}',
    'explorer':
        'explorer',
    'Copiati negli appunti i nomi di {0} file':
        'Copied the names of {0} files to the clipboard',
    'Copiati negli appunti i percorsi di {0} file':
        'Copied the paths of {0} files to the clipboard',
    'Copiate negli appunti {0} cartelle':
        'Copied {0} folders to the clipboard',
    'Le cartelle non ci sono su questo PC (disco scollegato o file spostati)':
        'The folders are not on this PC (disk disconnected or files moved)',
    'Aperte le prime {0} cartelle di {1}':
        'Opened the first {0} folders of {1}',
    'Copia nome file ({0})':
        'Copy file name ({0})',
    'Copia percorso completo ({0})':
        'Copy full path ({0})',
    'Copia cartella ({0})':
        'Copy folder ({0})',
    'Apri la cartella in Esplora risorse ({0})':
        'Open the folder in File Explorer ({0})',
    'File della sorgente':
        'Source file',
    'uguale':
        'same',
    'tag diversi':
        'different tags',
    'sparito':
        'gone',
    'Da rivedere: abbinati solo per i tag (≈)':
        'To review: matched only by tags (≈)',
    'Sorgente con tag diversi (⟳)':
        'Source with different tags (⟳)',
    "Sul PC c'è la sorgente di questo brano, con gli stessi tag":
        'The source of this track is on the PC, with the same tags',
    "Sul PC c'è la sorgente di questo brano, ma con tag diversi":
        'The source of this track is on the PC, but with different tags',
    "Da rivedere: sul PC c'è un brano con lo stesso titolo, album e artista, ma non è certo che sia la sorgente":
        'To review: on the PC there is a track with the same title, album and artist, but it is not certain that it is the source',
    "<b>Come funziona.</b> Qui vedi la musica dell'app <b>Musica</b> dell'iPhone, con i titoli, gli artisti e gli album che mostra l'app. La colonna <b>Sul PC</b> la confronta con il PC: ✔ la sorgente, stessi tag; ⟳ la sorgente, tag diversi; ≈ da rivedere (un brano con gli stessi tag nella cartella aperta, non certo); ✖ la sorgente non c'è più; vuoto = non trovato. <b>Sorgente</b>: il file da cui viene il brano (questo PC, un altro computer, nessuna, telefono); <b>Associa sorgenti</b> la ritrova, <b>Mostra</b> filtra.<br>Tasto destro su uno o più brani: <b>Salva su PC</b>, <b>Mostra nella scheda PC</b>, <b>Rimpiazza con la versione del PC</b> (per i ⟳), <b>Cambia tag</b>, <b>Associa sorgente</b>, <b>Togli sorgente</b>, <b>Elimina dall'iPhone</b>. Per mandare brani nuovi: tasto destro nella scheda PC → <b>Invia all'iPhone</b>. I file del PC non cambiano mai.<br><b>Attenzione:</b> {0}":
        '<b>How it works.</b> Here you see the music of the iPhone <b>Music</b> app, with the titles, artists and albums the app shows. The <b>On the PC</b> column compares it with the PC: ✔ the source, same tags; ⟳ the source, different tags; ≈ to review (a track with the same tags in the open folder, not certain); ✖ the source is gone; empty = not found. <b>Source</b>: the file the track comes from (this PC, another computer, none, phone); <b>Link sources</b> finds it, <b>Show</b> filters.<br>Right click on one or more tracks: <b>Save to PC</b>, <b>Show in the PC tab</b>, <b>Replace with the PC version</b> (for ⟳), <b>Change tags</b>, <b>Link source</b>, <b>Remove source</b>, <b>Delete from the iPhone</b>. To send new tracks: right click in the PC tab → <b>Send to iPhone</b>. The PC files never change.<br><b>Warning:</b> {0}',
    'Aggiorna':
        'Refresh',
    "Rilegge la musica dell'app Musica dall'iPhone connesso; senza iPhone rifà il confronto con il PC":
        "Reads the Music app's music again from the connected iPhone; without an iPhone redoes the comparison with the PC",
    "Ritrova sul PC la sorgente (il file) dei brani dell'iPhone, di quelli selezionati o di tutti quelli senza sorgente: nome della cartella, impronta dell'audio, regole e AI per i dubbi. Scrive solo il registro della provenienza: né i brani né i file cambiano.":
        'Finds on the PC the source (the file) of the iPhone tracks, the selected ones or all those without a source: folder name, audio fingerprint, rules and AI for the doubtful ones. Writes only the provenance register: neither the tracks nor the files change.',
    "La sorgente di questo brano non c'è più sul PC:\n{0}\n(spostata o cancellata). Il brano resta sull'iPhone: tasto destro → Associa sorgente per sceglierne un'altra.":
        'The source of this track is no longer on the PC:\n{0}\n(moved or deleted). The track stays on the iPhone: right click → Link source to choose another one.',
    ' (fuori dalla cartella aperta)':
        ' (outside the open folder)',
    'Abbinato per artista, album e titolo: probabile, non certo. Se è giusto, tasto destro → Associa le probabili':
        'Matched by artist, album and title: likely, not certain. If it is right, right click → Link the likely ones',
    'Associa le probabili':
        'Link the likely ones',
    "Associare {0} brani dell'iPhone al file del PC con lo stesso titolo, album e artista (≈)?\n\nControlla prima che siano giusti (il suggerimento di ≈ li confronta). Scrive solo il registro della provenienza: né i brani né i file cambiano.":
        'Link {0} iPhone tracks to the PC file with the same title, album and artist (≈)?\n\nCheck first that they are right (the tooltip of ≈ compares them). Writes only the provenance register: neither the tracks nor the files change.',
    'stessi titolo, album e artista':
        'same title, album and artist',
    'Associa sorgenti… ({0} brani)':
        'Link sources… ({0} tracks)',
    'Associa le probabili ≈ ({0} brani)':
        'Link the likely ones ≈ ({0} tracks)',
    "iPhone non connesso: rifatto il confronto con il PC sull'ultimo elenco letto":
        'iPhone not connected: redid the comparison with the PC on the last list read',
    'Nessun brano da associare.':
        'No tracks to link.',
    'lettura di {0}':
        'reading {0}',
    ' ({0} sostituite)':
        ' ({0} replaced)',
    'WMA / WAV / AIFF':
        'WMA / WAV / AIFF',
    'Ferma':
        'Stop',
    'Interrompe Verifica album online: i risultati già trovati restano':
        'Stops Check albums online: the results already found stay',
    'Risultati della verifica…':
        'Check results…',
    'Confronta gli album scelti (o tutti) con i cataloghi online (Deezer, Apple Music, Discogs, MusicBrainz): brani mancanti, tag giusti, copertina. In background':
        'Compares the chosen albums (or all) with the online catalogs (Deezer, Apple Music, Discogs, MusicBrainz): missing tracks, right tags, cover. In the background',
    "Cerca i problemi confrontando i tuoi brani tra loro (cartella aperta o iPhone), senza cataloghi online: file non aggiornati, album con pochi brani, collezioni divise, artisti scritti in modi diversi, brani duplicati (con l'AI, se configurata)":
        'Looks for problems by comparing your tracks with each other (open folder or iPhone), without online catalogs: files not updated, albums with few tracks, split collections, artists written in different ways, duplicate tracks (with the AI, if configured)',
    "Mostra solo i brani di un formato: vale per gli elenchi, la tabella, l'esportazione, Verifica album online, la scansione e l'invio all'iPhone":
        'Shows only the tracks of one format: applies to the lists, the table, export, Check albums online, the scan and sending to the iPhone',
    'Rilegge la cartella aperta: i file nuovi, tolti o cambiati (gli altri dalla cache dei tag). Con Maiusc premuto rilegge tutti i file da zero.':
        'Reads the open folder again: new, removed or changed files (the others from the tag cache). With Shift held down it reads all files from scratch.',
    "Nell'app Musica dell'iPhone ({0}): ✔ stesso brano, ⟳ stesso brano con tag diversi, ≈ forse lo stesso (abbinato solo per i tag: da rivedere), vuoto = non c'è; la spunta: voglio il brano sull'iPhone":
        'In the iPhone Music app ({0}): ✔ same track, ⟳ same track with different tags, ≈ maybe the same (matched only by tags: to review), empty = not there; the check mark: I want the track on the iPhone',
    'La verifica è già in corso (barra di stato): aspetta la fine o premi Ferma.':
        'The check is already running (status bar): wait for the end or press Stop.',
    'Verifica album online: 0 di {0}':
        'Check albums online: 0 of {0}',
    'Verifica album online: {0} di {1}':
        'Check albums online: {0} of {1}',
    'Verifica album online: interruzione…':
        'Check albums online: stopping…',
    '{0} album: {1} completi, {2} incompleti, {3} non trovati':
        '{0} albums: {1} complete, {2} incomplete, {3} not found',
    'Verifica album online non riuscita: {0}':
        'Check albums online failed: {0}',
    'Verifica album online interrotta: {0}':
        'Check albums online stopped: {0}',
    'Verifica album online finita: {0}':
        'Check albums online finished: {0}',
    'Mostra il percorso completo dei file':
        'Show the full path of the files',
    'Colonna File della scheda PC e File della sorgente della scheda iPhone: il percorso completo invece del solo nome del file':
        'File column of the PC tab and Source file of the iPhone tab: the full path instead of the file name only',
    'Colonne dei file':
        'File columns',
    'Nessun tag nel file':
        'No tags in the file',
    'Tag letti da: {0}':
        'Tags read from: {0}',
    'Tag letti da: {0} (un campo vuoto si prende dal tipo seguente)':
        'Tags read from: {0} (an empty field is taken from the next type)',
    "WMA, WAV e AIFF: i tag si leggono soltanto e i brani non si inviano all'iPhone":
        'WMA, WAV and AIFF: the tags are read only and the tracks are not sent to the iPhone',
    'Mancano i numeri di traccia {0}. "Verifica album online" controlla l\'elenco completo nei cataloghi online.':
        'Track numbers {0} are missing. "Check albums online" checks the complete list in the online catalogs.',
    'ASF (WMA)':
        'ASF (WMA)',
    'RIFF INFO':
        'RIFF INFO',
    'MP4 (iTunes)':
        'MP4 (iTunes)',
    'Vorbis comment':
        'Vorbis comment',
    '{0}: i tag dei file {1} si leggono soltanto':
        '{0}: the tags of {1} files are read only',
    'I brani selezionati ({0}), anche con una sorgente':
        'The selected tracks ({0}), also with a source',
    "Al più {0} impronte da leggere dall'iPhone: circa {1} minuti; quelle lette si ricordano":
        'At most {0} fingerprints to read from the iPhone: about {1} minutes; the ones read are remembered',
    "Solo le impronte già lette: l'iPhone non è connesso":
        'Only the fingerprints already read: the iPhone is not connected',
    'Già lette tutte: veloce':
        'All already read: fast',
    "Impronta dell'audio, per i brani non trovati dal nome della cartella":
        'Audio fingerprint, for the tracks the folder name did not find',
    'Con una sorgente proposta (in rosso)':
        'With a proposed source (in red)',
    "Sorgente proposta, non ancora associata:\n{0}\nTutti i brani di questo album dell'iPhone sono in questa cartella del PC, con lo stesso titolo e la stessa durata. Tasto destro → Associa questa sorgente.":
        'Proposed source, not linked yet:\n{0}\nAll the tracks of this iPhone album are in this PC folder, with the same title and duration. Right click → Link this source.',
    "tutto l'album nella stessa cartella, stesso titolo e durata":
        'the whole album in the same folder, same title and duration',
    'Allinea i tag':
        'Align the tags',
    "Copiare i tag dell'iPhone su {0} file del PC?\n\nSul PC le modifiche restano in sospeso (i file non cambiano) e valgono per le copie inviate, esportate o importate.":
        'Copy the iPhone tags to {0} PC files?\n\nOn the PC the changes stay pending (the files do not change) and apply to the copies sent, exported or imported.',
    "Sull'iPhone non c'è niente da cambiare.":
        'Nothing to change on the iPhone.',
    "Scrivere sull'iPhone i tag del PC di {0} brani?\n":
        'Write the PC tags of {0} tracks on the iPhone?\n',
    "\n• {0} con Rimpiazza (artista o artista dell'album): perdono ascolti e playlist; alla fine ti dico in quali playlist rimetterli.":
        '\n• {0} with Replace (artist or album artist): they lose plays and playlists; at the end I tell you which playlists to put them back in.',
    'Associa questa sorgente, proposta in rosso ({0} brani)':
        'Link this source, proposed in red ({0} tracks)',
    'Allinea i tag ({0} brani ⟳)':
        'Align the tags ({0} tracks ⟳)',
    "Usa i tag dell'iPhone: aggiorna il PC (in sospeso)":
        'Use the iPhone tags: update the PC (pending)',
    "Usa i tag del PC: aggiorna l'iPhone":
        'Use the PC tags: update the iPhone',
    'Solo per i brani con la sorgente certa e tag diversi (⟳): quale parte vale':
        'Only for the tracks with a certain source and different tags (⟳): which side wins',
    'Cartella della sorgente':
        'Source folder',
    'Mostra il percorso completo delle cartelle':
        'Show the full path of the folders',
    'Colonna Cartella della scheda PC e Cartella della sorgente della scheda iPhone: il percorso completo invece del solo nome della cartella':
        'Folder column of the PC tab and Source folder of the iPhone tab: the full path instead of the folder name only',
    'Colonne delle cartelle':
        'Folder columns',
    'Cartella':
        'Folder',
    "I tag di {0} brani del PC diventano quelli dell'iPhone. Continuare?\n\n(Si annulla con Torna ai tag del file, nella scheda PC.)":
        'The tags of {0} PC tracks become those of the iPhone. Continue?\n\n(Undo with Back to the file tags, in the PC tab.)',
    "I tag di {0} brani dell'iPhone diventano quelli del PC. Continuare?":
        'The tags of {0} iPhone tracks become those of the PC. Continue?',
    '\n\nAttenzione: {0} hanno un artista diverso e vanno rimpiazzati: perdono ascolti e playlist.':
        '\n\nWarning: {0} have a different artist and must be replaced: they lose plays and playlists.',
    'Allinea i tag: modifica dei file del PC':
        'Align the tags: changing the PC files',
    "<b>Questi {0} file del PC verranno modificati</b>: si scrivono nel file i tag dell'iPhone. Non si può annullare.":
        '<b>These {0} PC files will be changed</b>: the iPhone tags are written into the file. It cannot be undone.',
    'Campo':
        'Field',
    'Ora sul PC':
        'Now on the PC',
    'Diventa':
        'Becomes',
    'Modifica {0} file':
        'Change {0} files',
    "\nI tag sono diversi da quelli dell'iPhone: il file resta la sorgente. Tasto destro → Allinea i tag per scegliere quali tenere.":
        '\nThe tags differ from the iPhone ones: the file stays the source. Right click → Align the tags to choose which to keep.',
    "Sul PC non c'è niente da cambiare.":
        'Nothing to change on the PC.',
    'Tag scritti in {0} file del PC':
        'Tags written in {0} PC files',
    "Usa i tag dell'iPhone: modifica i file del PC…":
        'Use the iPhone tags: change the PC files…',
    "{0}\nSull'iPhone questo brano ha tag diversi: Allinea i tag (scheda iPhone, tasto destro) sceglie quali tenere":
        '{0}\nOn the iPhone this track has different tags: Align the tags (iPhone tab, right click) chooses which to keep',
    "<b>Come funziona.</b> Qui vedi la musica dell'app <b>Musica</b> dell'iPhone, con i titoli, gli artisti e gli album che mostra l'app. La colonna <b>Sul PC</b> la confronta con il PC: ✔ la sorgente, stessi tag; ⟳ la sorgente, tag diversi; ≈ da rivedere (un brano con gli stessi tag nella cartella aperta, non certo); ✖ la sorgente non c'è più; vuoto = non trovato. <b>Sorgente</b>: il file da cui viene il brano (questo PC, un altro computer, nessuna, telefono); <b>Associa sorgenti</b> la ritrova, <b>Mostra</b> filtra.<br>Tasto destro su uno o più brani: <b>Salva su PC</b>, <b>Mostra nella scheda PC</b>, <b>Rimpiazza con la versione del PC</b> (per i ⟳), <b>Cambia tag</b>, <b>Associa sorgente</b>, <b>Togli sorgente</b>, <b>Elimina dall'iPhone</b>. Per mandare brani nuovi: tasto destro nella scheda PC → <b>Invia all'iPhone</b>. PC e iPhone non si allineano da soli: <b>Allinea i tag</b> sceglie la direzione (i file del PC cambiano solo dopo la tua conferma).<br><b>Attenzione:</b> {0}":
        '<b>How it works.</b> Here you see the music of the iPhone <b>Music</b> app, with the titles, artists and albums the app shows. The <b>On the PC</b> column compares it with the PC: ✔ the source, same tags; ⟳ the source, different tags; ≈ to review (a track with the same tags in the open folder, not certain); ✖ the source is gone; empty = not found. <b>Source</b>: the file the track comes from (this PC, another computer, none, phone); <b>Link sources</b> finds it, <b>Show</b> filters.<br>Right click on one or more tracks: <b>Save to PC</b>, <b>Show in the PC tab</b>, <b>Replace with the PC version</b> (for ⟳), <b>Change tags</b>, <b>Link source</b>, <b>Remove source</b>, <b>Delete from the iPhone</b>. To send new tracks: right click in the PC tab → <b>Send to iPhone</b>. PC and iPhone do not align by themselves: <b>Align the tags</b> chooses the direction (the PC files change only after you confirm).<br><b>Warning:</b> {0}',
    'Le cartelle nascoste con il tasto destro: qui le mostri di nuovo':
        'The folders hidden with the right click: show them again here',
    'Cartelle nascoste ({0})…':
        'Hidden folders ({0})…',
    'Nascoste {0} cartelle: le mostri di nuovo con Cartelle nascoste… in alto':
        'Hid {0} folders: show them again with Hidden folders… at the top',
    'Cartelle nascoste':
        'Hidden folders',
    'Spunta le cartelle da mostrare di nuovo nella scheda PC (i file non sono mai cambiati).':
        'Check the folders to show again in the PC tab (the files never changed).',
    'Mostra le spuntate':
        'Show the checked ones',
    '{0} brani caricati':
        '{0} tracks loaded',
    ' ({0} nelle cartelle nascoste)':
        ' ({0} in the hidden folders)',
    'Nascondi la cartella ({0})':
        'Hide the folder ({0})',
    'Non mostrare più i brani di questa cartella (e delle sue sottocartelle) nella scheda PC: i file non cambiano; Cartelle nascoste… in alto le mostra di nuovo':
        'Stop showing the tracks of this folder (and its subfolders) in the PC tab: the files do not change; Hidden folders… at the top shows them again',
    '{0} playlist create, {1} cancellate.':
        '{0} playlists created, {1} deleted.',
    "\n\nMa sull'iPhone le playlist create non ci sono. Se è attiva Sincronizza libreria (iCloud: Impostazioni, Musica), l'iPhone accetta le playlist da un computer senza crearle.":
        '\n\nBut the created playlists are not on the iPhone. If Sync Library (iCloud: Settings, Music) is on, the iPhone accepts playlists from a computer without creating them.',
    "\n\nNon risultano sull'iPhone: {0}":
        '\n\nNot found on the iPhone: {0}',
    'Saltate':
        'Skipped',
    'Non riuscite':
        'Failed',
    'Playlist per artista…':
        'Playlists by artist…',
    "Rifà le playlist dell'iPhone: una per artista dell'album (con più album) e una per compilation; cancella quelle messe da un computer. Prima mostra tutto; c'è anche una prova. I brani non cambiano.":
        'Rebuilds the iPhone playlists: one per album artist (with several albums) and one per compilation; deletes those put there by a computer. It shows everything first; there is also a test. The tracks do not change.',
    "lettura della musica e delle playlist dell'iPhone":
        'reading the iPhone music and playlists',
    'Playlist per artista':
        'Playlists by artist',
    'Creare sull\'iPhone la playlist di prova "{0}" ({1} brani)? Non si cancella niente.':
        'Create the test playlist "{0}" on the iPhone ({1} tracks)? Nothing is deleted.',
    "Creare {0} playlist e cancellare {1} playlist messe da un computer?\n\nLe playlist cancellate non si possono recuperare; i brani restano sull'iPhone.":
        'Create {0} playlists and delete {1} playlists put there by a computer?\n\nDeleted playlists cannot be recovered; the tracks stay on the iPhone.',
    "Playlist sull'iPhone":
        'Playlists on the iPhone',
    'Playlist per artista e per compilation':
        'Playlists by artist and by compilation',
    "<b>{0} playlist da creare</b> (quelle spuntate) e <b>{1} da cancellare</b>: tutte quelle messe da un computer (CopyTrans, iTunes, questo programma), comprese quelle fatte le volte prima.<br>Per artista: gli artisti dell'album con almeno {2} album e {3} brani. Per compilation: i volumi della stessa serie insieme, o un album solo con almeno {4} brani.<br>I brani non cambiano: cambiano solo le playlist. Prima si creano le nuove, poi si cancellano le vecchie.":
        '<b>{0} playlists to create</b> (the ticked ones) and <b>{1} to delete</b>: all those put there by a computer (CopyTrans, iTunes, this program), including those made the previous times.<br>By artist: the album artists with at least {2} albums and {3} tracks. By compilation: the volumes of the same series together, or a single album with at least {4} tracks.<br>The tracks do not change: only the playlists do. The new ones are created first, then the old ones are deleted.',
    "<br>{0} playlist fatte sull'iPhone restano: il computer non le può toccare (cancellale a mano, se vuoi).":
        '<br>{0} playlists made on the iPhone stay: a computer cannot touch them (delete them by hand, if you like).',
    '<br>{0} brani non messi da un computer (o senza file) non possono stare in queste playlist.':
        '<br>{0} tracks not put there by a computer (or without a file) cannot be in these playlists.',
    'Playlist':
        'Playlist',
    'Da creare ({0})':
        'To create ({0})',
    'Da cancellare: messe da un computer ({0})':
        'To delete: put there by a computer ({0})',
    "Restano: fatte sull'iPhone ({0})":
        'Staying: made on the iPhone ({0})',
    'Crea e cancella…':
        'Create and delete…',
    'Prova':
        'Test',
    'Crea solo "{0}", una copia della prima playlist spuntata, e non cancella niente: guarda sul telefono che ci sia, con i brani in ordine. La cancella la prossima volta, con le altre messe da un computer.':
        'Creates only "{0}", a copy of the first ticked playlist, and deletes nothing: check on the phone that it is there, with the tracks in order. It is deleted next time, with the others put there by a computer.',
    "nessuno dei suoi brani è più sull'iPhone":
        'none of its tracks is on the iPhone any more',
    'playlist: {0} di {1}':
        'playlists: {0} of {1}',
    '{0} playlist':
        '{0} playlists',
    'fatta sul telefono: il computer non la può cancellare':
        'made on the phone: a computer cannot delete it',
    "le playlist dell'app Musica non si leggono ({0})":
        'the Music app playlists cannot be read ({0})',
    'playlist senza brani':
        'playlist without tracks',
    'un brano senza sync_id non può stare in una playlist mandata da un computer':
        'a track without sync_id cannot be in a playlist sent by a computer',
    'nome della playlist':
        'playlist name',
    'una playlist fatta sul telefono non si cancella dal computer':
        'a playlist made on the phone cannot be deleted from the computer',
    'es. Musica buona; Musica FLAC; Raccolte':
        'e.g. Good music; FLAC music; Collections',
    "Quando un brano c'è in più copie sul PC, le associazioni (proposta in rosso, Associa sorgente, Associa sorgenti) scelgono la copia nella prima di queste cartelle, poi nella seconda… Nomi di cartella (valgono in qualsiasi punto del percorso) o percorsi interi, separati da punto e virgola.":
        'When a track is on the PC in several copies, the links (red proposal, Link source, Link sources) choose the copy in the first of these folders, then in the second… Folder names (valid anywhere in the path) or full paths, separated by semicolons.',
    'Cartelle preferite':
        'Preferred folders',
    'Salva i selezionati sul PC (iPhone → PC)…':
        'Save the selected ones to the PC (iPhone → PC)…',
    'Salva su PC (iPhone → PC)… ({0} brani)':
        'Save to PC (iPhone → PC)… ({0} tracks)',
    'Rimpiazza con la versione del PC (PC → iPhone): {0} brani associati ⟳':
        'Replace with the PC version (PC → iPhone): {0} linked tracks ⟳',
    "Usa i tag dell'iPhone (iPhone → PC): modifica i file del PC…":
        'Use the iPhone tags (iPhone → PC): change the PC files…',
    "Usa i tag del PC (PC → iPhone): aggiorna l'iPhone":
        'Use the PC tags (PC → iPhone): update the iPhone',
    'Applica (PC → iPhone)…':
        'Apply (PC → iPhone)…',
    "<b>In attesa per l'iPhone (PC → iPhone):</b> {0} da inviare, {1} da togliere, {2} da aggiornare":
        '<b>Pending for the iPhone (PC → iPhone):</b> {0} to send, {1} to remove, {2} to update',
    "Invia all'iPhone (PC → iPhone): {0} brani che non ci sono":
        'Send to iPhone (PC → iPhone): {0} tracks that are not there',
    "Rimpiazza sull'iPhone (PC → iPhone): {0} brani associati ⟳":
        'Replace on the iPhone (PC → iPhone): {0} linked tracks ⟳',
    "Aggiorna l'iPhone più tardi (PC → iPhone): {0} brani associati ⟳ in attesa":
        'Update the iPhone later (PC → iPhone): {0} linked tracks ⟳ pending',
    '{0} brani con tag diversi abbinati solo per i tag: non si aggiornano, prima associa la sorgente (scheda iPhone)':
        '{0} tracks with different tags matched only by tags: they are not updated, link the source first (iPhone tab)',
    'Sorgente proposta, non ancora associata ({0}):\n{1}\n{2}. Tasto destro → Associa questa sorgente.':
        'Proposed source, not linked yet ({0}):\n{1}\n{2}. Right-click → Link this source.',
    "es. Compilation; Artisti diversi":
        "e.g. Compilation; Different artists",
    '"AA.VV.", "Artisti vari", "Various Artists", "VA" e simili sono già un artista solo negli elenchi Artisti. Qui altri nomi che valgono come loro, separati da punto e virgola: valgono anche per le playlist delle compilation.':
        '"AA.VV.", "Artisti vari", "Various Artists", "VA" and similar are already a single artist in the Artists lists. Here, other names that count as them, separated by semicolons: they also count for the compilation playlists.',
    'Altri nomi per "Artisti vari"':
        'Other names for "Various Artists"',
    'meno di un minuto':
        'less than a minute',
    'circa un minuto':
        'about a minute',
    'circa {0} minuti':
        'about {0} minutes',
    '1 ora':
        '1 hour',
    '{0} ore':
        '{0} hours',
    'circa {0}':
        'about {0}',
    'circa {0} e {1} minuti':
        'about {0} and {1} minutes',
    'Brani: {0}. Tempo stimato: {1}.':
        'Tracks: {0}. Estimated time: {1}.',
    'Aggiorna dal PC':
        'Update from the PC',
    "I tag di {0} brani dell'iPhone diventano quelli del PC (PC → iPhone). Continuare?\n\n":
        'The tags of {0} iPhone tracks become those of the PC (PC → iPhone). Continue?\n\n',
    'Aggiorna dal PC (PC → iPhone): non si può, {0} brani su {1} non hanno la sorgente associata':
        'Update from the PC (PC → iPhone): not possible, {0} of {1} tracks have no linked source',
    "Rimuovi dall'iPhone: {0} brani":
        'Remove from the iPhone: {0} tracks',
    '{0} brani acquistati o scaricati sul telefono: un computer non li può togliere':
        '{0} tracks bought or downloaded on the phone: a computer cannot remove them',
    'Conferma':
        'Confirm',
    "Inviare {0} brani all'app Musica dell'iPhone (PC → iPhone) ({1})?\n\n":
        "Send {0} tracks to the iPhone's Music app (PC → iPhone) ({1})?\n\n",
    '\n\nVanno copie con i tag e la copertina modificati: i file del PC non cambiano.':
        '\n\nCopies go with the edited tags and cover: the files on the PC do not change.',
    "Rimpiazzare {0} brani dell'iPhone con la versione del PC (PC → iPhone)?\n\n":
        'Replace {0} iPhone tracks with the PC version (PC → iPhone)?\n\n',
    "\n\nPrima si invia la versione del PC, poi si toglie quella vecchia. I brani rimpiazzati perdono il conteggio degli ascolti e spariscono dalle playlist fatte sull'iPhone.":
        '\n\nFirst the PC version is sent, then the old one is removed. Replaced tracks lose their play count and disappear from the playlists made on the iPhone.',
    "Applicare all'iPhone le modifiche in attesa (PC → iPhone)?\n\n":
        'Apply the pending changes to the iPhone (PC → iPhone)?\n\n',
    "{0} brani sull'iPhone abbinati solo per i tag: per toglierli o aggiornarli prima associa la sorgente (scheda iPhone)":
        '{0} tracks on the iPhone matched only by tags: to remove or update them, first link the source (iPhone tab)',
    "Collega l'iPhone: la sua musica non è ancora stata letta":
        'Connect the iPhone: its music has not been read yet',
    "Ci sono modifiche in attesa per l'iPhone (PC → iPhone) non ancora applicate: {0} da inviare, {1} da togliere, {2} da aggiornare.\n\n":
        'There are pending changes for the iPhone (PC → iPhone) not applied yet: {0} to send, {1} to remove, {2} to update.\n\n',
    '\n\nApplicarle prima di uscire? Il programma si chiude alla fine.':
        '\n\nApply them before exiting? The program closes at the end.',
    'Applica ed esci':
        'Apply and exit',
    "\n\nL'iPhone non è collegato, quindi ora non si possono applicare. Se esci restano in attesa per la prossima volta; per applicarle ora collega l'iPhone e premi Applica.":
        '\n\nThe iPhone is not connected, so they cannot be applied now. If you exit they stay pending for next time; to apply them now, connect the iPhone and press Apply.',
    'Esci senza applicare':
        'Exit without applying',
    'Aggiorna dal PC (PC → iPhone): rimpiazza {0} brani con i file del PC':
        'Update from the PC (PC → iPhone): replace {0} tracks with the PC files',
    'Aggiorna TAG dal PC (PC → iPhone): {0} brani con tag diversi ⟳':
        'Update TAGS from the PC (PC → iPhone): {0} tracks with different tags ⟳',
    'Aggiorna TAG dal PC (PC → iPhone): nessun brano associato con tag diversi':
        'Update TAGS from the PC (PC → iPhone): no linked track with different tags',
    'Aggiorna TAG dal PC':
        'Update tags from the PC',
    "Aggiorna sull'iPhone (PC → iPhone): rimpiazza {0} brani con i file del PC":
        'Update on the iPhone (PC → iPhone): replace {0} tracks with the PC files',
    "Aggiorna TAG sull'iPhone (PC → iPhone): {0} brani con tag diversi ⟳":
        'Update TAGS on the iPhone (PC → iPhone): {0} tracks with different tags ⟳',
    'Album o artista scritti diversamente dal PC (Aa)':
        'Album or artist spelled differently from the PC (Aa)',
    'Allinea la grafia (PC → iPhone): {0} album scritti diversamente (Aa)':
        'Align the spelling (PC → iPhone): {0} albums spelled differently (Aa)',
    '; {0} non si possono, hanno brani senza sorgente associata':
        '; {0} cannot be aligned, they have tracks without a linked source',
    'Allineare la grafia di {0} album (PC → iPhone)?\n\nL\'iPhone tiene il nome che ha già per un album o un artista finché esiste, anche vuoto. Per dargli il nome del PC il programma toglie i loro {1} brani e li reinvia dal PC; per far cancellare all\'iPhone i nomi vecchi toglie insieme {2} brani di servizio di 3 secondi ("{3}"), inviati poco prima.\n\n':
        'Align the spelling of {0} albums (PC → iPhone)?\n\nThe iPhone keeps the name it already has for an album or an artist as long as it exists, even empty. To give it the PC name the program removes their {1} tracks and sends them again from the PC; to make the iPhone delete the old names it removes together {2} 3-second service tracks ("{3}"), sent just before.\n\n',
    "\n\nI brani reinviati perdono il conteggio degli ascolti e spariscono dalle playlist (Playlist per artista le rifà). Se l'iPhone non cancellasse i nomi vecchi, i brani tornano comunque, con il nome di prima.":
        '\n\nThe tracks sent again lose their play count and disappear from the playlists (Playlists by artist rebuilds them). If the iPhone did not delete the old names, the tracks come back anyway, with the previous name.',
    '\n\nSono nelle playlist:\n':
        '\n\nThey are in the playlists:\n',
    'Allinea la grafia':
        'Align the spelling',
    'reinviati con la grafia del PC':
        'sent again with the PC spelling',
    'eliminazione: ':
        'removal: ',
    "controllo dei nomi sull'iPhone":
        'checking the names on the iPhone',
    '{0} album e {1} artisti':
        '{0} albums and {1} artists',
    "l'iPhone non ha cancellato i nomi vecchi: i brani sono tornati con la grafia dell'iPhone (si può riprovare più tardi)":
        'the iPhone did not delete the old names: the tracks came back with the iPhone spelling (you can try again later)',
    "Album senza immagine sull'iPhone":
        'Albums without artwork on the iPhone',
    'Sistema le copertine (PC → iPhone): {0} album senza immagine':
        'Fix the artwork (PC → iPhone): {0} albums without artwork',
    '; {0} senza sorgente sul PC':
        '; {0} without a source on the PC',
    '; {0} senza copertina anche sul PC':
        '; {0} without a cover on the PC too',
    '{0} — {1}\n{2} brani: selezionali per cambiarli':
        '{0} — {1}\n{2} tracks: select them to change them',
    "{0} album sull'iPhone non hanno l'immagine dell'album, anche se i brani hanno la copertina (succede agli album messi da altri programmi). Rimpiazzando i loro brani con i file del PC, l'iPhone la sceglie.":
        '{0} albums on the iPhone have no album artwork, even though the tracks have a cover (it happens to albums put there by other programs). Replacing their tracks with the PC files makes the iPhone choose one.',
    'Sistema le copertine':
        'Fix the artwork',
    '{0} — {1}\n{2} brani: selezionali in tabella per modificarli':
        '{0} — {1}\n{2} tracks: select them in the table to edit them',
    "\n\nGrafia: {0} album hanno il nome dell'album o dell'artista scritto in modo diverso dal PC (maiuscole, zeri, accenti). L'iPhone tiene il nome che ha già, quindi questi album si tolgono interi e si reinviano dal PC: {1} brani, anche quelli dello stesso album non scelti, con qualche brano di servizio di 3 secondi che si toglie subito.":
        '\n\nSpelling: {0} albums have the album or artist name written differently from the PC (capitals, zeros, accents). The iPhone keeps the name it already has, so these albums are removed whole and sent again from the PC: {1} tracks, also the ones of the same album not chosen, with a few 3-second service tracks that are removed right away.',
    "\n\n{0} album con la grafia diversa hanno brani senza sorgente associata: non si possono reinviare interi e restano con la grafia dell'iPhone.":
        "\n\n{0} albums with a different spelling have tracks without a linked source: they cannot be sent again whole and keep the iPhone's spelling.",
    '• {0} brani da reinviare con il loro album intero, per la grafia (perdono ascolti e playlist)':
        '• {0} tracks to send again with their whole album, for the spelling (they lose plays and playlists)',
    'Ritrovati e associati {0} file spostati':
        'Found and linked {0} moved files',
    "{0} dei {1} brani da inviare ci sono già sull'iPhone in un altro formato (stesso artista, titolo e durata), o ci sono due volte in questo invio:\n\n":
        '{0} of the {1} tracks to send are already on the iPhone in another format (same artist, title and length), or are twice in this transfer:\n\n',
    "\n\nInviandoli, sull'iPhone avresti la stessa canzone due volte.":
        '\n\nSending them, you would have the same song twice on the iPhone.',
    'Brani già presenti in un altro formato':
        'Tracks already there in another format',
    'Invia senza questi ({0} brani)':
        'Send without these ({0} tracks)',
    'Invia anche questi ({0} brani)':
        'Send these too ({0} tracks)',
    "Niente da inviare: erano tutti già sull'iPhone in un altro formato":
        'Nothing to send: they were all already on the iPhone in another format',
    "Niente da applicare: i brani da inviare erano già sull'iPhone in un altro formato":
        'Nothing to apply: the tracks to send were already on the iPhone in another format',
    "c'è già sull'iPhone in {0}":
        'already on the iPhone in {0}',
    "nello stesso invio c'è anche in {0}: {1}":
        'also in this transfer in {0}: {1}',
    "Completa l'album (PC → iPhone): invia {0} brani che mancano ({1} album)":
        'Complete the album (PC → iPhone): send the {0} missing tracks ({1} albums)',
    "Completa l'album (PC → iPhone): sull'iPhone non manca niente (o i brani non hanno la sorgente)":
        'Complete the album (PC → iPhone): nothing is missing on the iPhone (or the tracks have no source)',
    "Elimina dall'iPhone: connetti l'iPhone (e attendi la fine dell'operazione in corso)":
        'Delete from the iPhone: connect the iPhone (and wait for the current operation to finish)',
    "Togliere dall'iPhone: connetti l'iPhone (e attendi la fine dell'operazione in corso)":
        'Remove from the iPhone: connect the iPhone (and wait for the current operation to finish)',
    "Nessuno dei brani selezionati è sull'iPhone con la sorgente associata":
        'None of the selected tracks is on the iPhone with a linked source',
    "Impronte dell'audio in sottofondo: {0} file (servono per ritrovare i file spostati o rinominati)":
        'Audio fingerprints in the background: {0} files (they help find moved or renamed files)',
    "Impronte dell'audio calcolate: {0} file":
        'Audio fingerprints computed: {0} files',
    "<b>{0}</b> brani dell'iPhone vengono da file di questo PC che non ci sono più (spostati o cancellati). <b>{1}</b> li ho ritrovati nella cartella aperta: colonna <i>Ritrovato sul PC</i>. Il programma non li toglie dall'iPhone da solo: scegli tu cosa fare con quelli spuntati.<br>Se il file è su un disco che ora non è collegato, collegalo e premi <i>Più tardi</i>.":
        "<b>{0}</b> iPhone tracks come from files of this PC that are no longer there (moved or deleted). <b>{1}</b> were found again in the open folder: column <i>Found on the PC</i>. The program does not remove them from the iPhone by itself: you choose what to do with the checked ones.<br>If the file is on a drive that is not connected now, connect it and press <i>Later</i>.",
    'Ritrovato sul PC':
        'Found on the PC',
    'Associa i file ritrovati ({0})':
        'Link the found files ({0})',
    'I brani spuntati con un file nella colonna Ritrovato sul PC: quel file diventa la loro sorgente (si scrive solo il registro della provenienza)':
        'The checked tracks with a file in the Found on the PC column: that file becomes their source (only the source register is written)',
    'stesso audio (impronta), spostato':
        'same audio (fingerprint), moved',
    'stesso nome, dimensione e audio (impronta), spostato':
        'same name, size and audio (fingerprint), moved',
    'stesso nome e stessa dimensione del file, spostato':
        'same file name and size, moved',
    'Campi da scrivere:':
        'Fields to write:',
    "Cambia tag: connetti l'iPhone (e attendi la fine dell'operazione in corso)":
        'Change tags: connect the iPhone (and wait for the current operation to finish)',
    '{0} ({1} file)':
        '{0} ({1} files)',
    "<b>Questi {0} file del PC verranno modificati</b>: si scrivono nel file i tag dell'iPhone dei campi scelti. Non si può annullare.":
        "<b>These {0} PC files will be modified</b>: the iPhone's tags of the chosen fields are written into the file. It cannot be undone.",
    'Copia da PC a iPhone':
        'Copy from PC to iPhone',
    "brani che sull'iPhone non ci sono":
        'tracks that are not on the iPhone',
    'da copiare da PC a iPhone':
        'to copy from PC to iPhone',
    'Ricopia da PC a iPhone':
        'Copy again from PC to iPhone',
    "il file sull'iPhone è sostituito da quello del PC: perde ascolti e playlist":
        "the file on the iPhone is replaced by the PC's: it loses plays and playlists",
    'da ricopiare da PC a iPhone':
        'to copy again from PC to iPhone',
    'Usa i tag da PC a iPhone':
        'Use the tags from PC to iPhone',
    "solo i tag: sull'iPhone diventano quelli del PC":
        "only the tags: on the iPhone they become the PC's",
    'con i tag da portare da PC a iPhone':
        'with tags to bring from PC to iPhone',
    "Cambia i tag sull'iPhone":
        'Change the tags on the iPhone',
    'i tag scritti con Cambia i tag nella scheda iPhone':
        'the tags written with Change the tags in the iPhone tab',
    "con i tag da cambiare sull'iPhone":
        'with tags to change on the iPhone',
    'i file del PC non cambiano':
        "the PC files don't change",
    "da eliminare dall'iPhone":
        'to delete from the iPhone',
    'tag diversi: {0}':
        'different tags: {0}',
    "Applica le azioni in attesa sull'iPhone":
        'Apply the pending actions on the iPhone',
    'Brano':
        'Track',
    'Dettaglio':
        'Detail',
    'Togli questa azione: non parte':
        "Remove this action: it won't run",
    'Togli il gruppo':
        'Remove the group',
    'Togli tutte le azioni di questo gruppo':
        'Remove all the actions of this group',
    "<b>Azioni in attesa per {0}: {1}</b>. La ✕ (o Canc sulle righe selezionate) toglie un'azione: non parte, il brano resta com'è e la rimetti dalle schede.":
        "<b>Pending actions for {0}: {1}</b>. The ✕ (or Delete on the selected rows) removes an action: it won't run, the track stays as it is and you can add it again from the tabs.",
    'Togli le selezionate':
        'Remove the selected',
    'Associa sorgenti: cartelle che non ci sono, saltate: {0}':
        "Link sources: folders that don't exist, skipped: {0}",
    'Scrivi la cartella dove cercare.':
        'Write the folder to search in.',
    'Toglie dalla coda le azioni delle righe selezionate (anche il tasto Canc)':
        'Removes the actions of the selected rows from the queue (the Delete key too)',
    "Tolto dalla coda 1 brano già sull'iPhone in un altro formato.":
        'Removed from the queue 1 track already on the iPhone in another format.',
    "Tolti dalla coda {0} brani già sull'iPhone in un altro formato.":
        'Removed from the queue {0} tracks already on the iPhone in another format.',
    '<b>Nessuna azione</b>: le hai tolte tutte.':
        '<b>No actions</b>: you removed them all.',
    "\n\nPer applicarle connetti l'iPhone (e aspetta la fine dell'operazione in corso).":
        '\n\nTo apply them connect the iPhone (and wait for the current operation to finish).',
    'Applica {0} azioni':
        'Apply {0} actions',
    'Applica 1 azione':
        'Apply 1 action',
    "<b>Come funziona.</b> Qui vedi la musica dell'app <b>Musica</b> dell'iPhone, con i titoli, gli artisti e gli album che mostra l'app. La colonna <b>Sul PC</b> la confronta con il PC: ✔ la sorgente, stessi tag; ⟳ la sorgente, tag diversi; ≈ da rivedere (un brano con gli stessi tag nella cartella aperta, non certo); ✖ la sorgente non c'è più; vuoto = non trovato. <b>Sorgente</b>: il file da cui viene il brano (questo PC, un altro computer, nessuna, telefono); <b>Associa sorgenti</b> la ritrova, <b>Mostra</b> filtra.<br>Tasto destro su uno o più brani: <b>Copia da iPhone a PC</b>, <b>Ricopia da PC a iPhone</b> e <b>Usa i tag da PC a iPhone</b> (per i ⟳), <b>Usa i tag da iPhone a PC</b>, <b>Cambia i tag</b>, <b>Associa al file sul PC</b>, <b>Elimina dall'iPhone</b>. Quello che cambia l'iPhone va in attesa (la barra blu in alto) e parte con <b>Applica</b>. Per copiare brani nuovi: scheda PC → <b>Copia da PC a iPhone</b>. PC e iPhone non si allineano da soli (i file del PC cambiano solo dopo la tua conferma).<br><b>Attenzione:</b> {0}":
        "<b>How it works.</b> Here you see the music of the iPhone's <b>Music</b> app, with the titles, artists and albums the app shows. The <b>On the PC</b> column compares it with the PC: ✔ the source, same tags; ⟳ the source, different tags; ≈ to review (a track with the same tags in the open folder, not certain); ✖ the source is gone; empty = not found. <b>Source</b>: the file the track comes from (this PC, another computer, none, phone); <b>Link sources</b> finds it again, <b>Show</b> filters.<br>Right click on one or more tracks: <b>Copy from iPhone to PC</b>, <b>Copy again from PC to iPhone</b> and <b>Use the tags from PC to iPhone</b> (for the ⟳), <b>Use the tags from iPhone to PC</b>, <b>Change the tags</b>, <b>Link to the file on the PC</b>, <b>Delete from the iPhone</b>. What changes the iPhone goes pending (the blue bar at the top) and runs with <b>Apply</b>. To copy new tracks: PC tab → <b>Copy from PC to iPhone</b>. PC and iPhone don't align by themselves (the PC files change only after your confirmation).<br><b>Warning:</b> {0}",
    '{0} brani. Artista e artista dell\'album non si cambiano qui: sull\'iPhone rinominerebbero l\'artista per tutti i suoi brani. Cambiali nella scheda PC, poi usa <i>Ricopia da PC a iPhone</i>. Anno o numero 0: lo svuota.<br>Una compilation vuole anche l\'artista dell\'album <i>Artisti vari</i>: se nell\'app Musica i brani non si raccolgono in un solo album, metti la spunta e "Artisti vari" nella scheda PC e usa <i>Ricopia da PC a iPhone</i>.':
        '{0} tracks. Artist and album artist are not changed here: on the iPhone they would rename the artist for all their tracks. Change them in the PC tab, then use <i>Copy again from PC to iPhone</i>. Year or number 0: clears it.<br>A compilation also needs the album artist <i>Various Artists</i>: if in the Music app the tracks don\'t gather in a single album, tick it and "Various Artists" in the PC tab and use <i>Copy again from PC to iPhone</i>.',
    'Gli stessi tag per i {0} brani con il file su questo PC, come modifiche in sospeso (i file non cambiano)':
        "The same tags for the {0} tracks with the file on this PC, as pending changes (the files don't change)",
    "Spenta, il PC resta com'è e la differenza si vede (⟳). Per scrivere i tag nei file del PC c'è Usa i tag da iPhone a PC.":
        'Off, the PC stays as it is and the difference shows (⟳). To write the tags into the PC files there is Use the tags from iPhone to PC.',
    'Metti in attesa':
        'Add to pending',
    "L'iPhone cambia con Applica (la barra blu in alto)":
        'The iPhone changes with Apply (the blue bar at the top)',
    'Cambia i tag':
        'Change the tags',
    'Usa i tag da iPhone a PC: modifica dei file del PC':
        'Use the tags from iPhone to PC: changing the PC files',
    "\nI tag sono diversi da quelli dell'iPhone: il file resta la sorgente. Tasto destro → Usa i tag da PC a iPhone o da iPhone a PC per scegliere quali tenere.":
        "\nThe tags differ from the iPhone's: the file stays the source. Right click → Use the tags from PC to iPhone or from iPhone to PC to choose which to keep.",
    'Copia i brani mancanti degli album da PC a iPhone: {0} ({1} album)':
        "Copy the albums' missing tracks from PC to iPhone: {0} ({1} albums)",
    'Copia i brani mancanti degli album da PC a iPhone: non manca niente (o i brani non hanno la sorgente)':
        "Copy the albums' missing tracks from PC to iPhone: nothing is missing (or the tracks have no source)",
    'Ricopia le copertine da PC a iPhone: {0} album senza immagine':
        'Copy the covers again from PC to iPhone: {0} albums without artwork',
    'Usa i tag da iPhone a PC':
        'Use the tags from iPhone to PC',
    'nessun brano ⟳ con la sorgente':
        'no ⟳ track with a source',
    'Copia {0} da iPhone a PC…':
        'Copy {0} from iPhone to PC…',
    'Mostra nella scheda PC ({0})':
        'Show in the PC tab ({0})',
    'Ricopia da PC a iPhone: {0}':
        'Copy again from PC to iPhone: {0}',
    'Usa i tag da PC a iPhone: {0}':
        'Use the tags from PC to iPhone: {0}',
    'Usa i tag da iPhone a PC: {0}…':
        'Use the tags from iPhone to PC: {0}…',
    'Cambia i tag: {0}…':
        'Change the tags: {0}…',
    'Associa al file sul PC…':
        'Link to the file on the PC…',
    'Associa al file sul PC: {0}…':
        'Link to the file on the PC: {0}…',
    'Associa le probabili ≈: {0}':
        'Link the probable ≈: {0}',
    'Associa la sorgente proposta in rosso: {0}':
        'Link the source proposed in red: {0}',
    'Togli la sorgente: {0}':
        'Remove the source: {0}',
    "Elimina {0} dall'iPhone":
        'Delete {0} from the iPhone',
    "Elimina dall'iPhone: nessun brano":
        'Delete from the iPhone: no tracks',
    '{0} acquistati o scaricati sul telefono: un computer non li può cambiare né togliere':
        '{0} bought or downloaded on the phone: a computer can neither change nor remove them',
    "\n\nI brani da ricopiare sono nelle playlist fatte sull'iPhone (alla fine te le ricordo):\n":
        "\n\nThe tracks to copy again are in playlists made on the iPhone (I'll remind you at the end):\n",
    "Connetti l'iPhone per applicare le azioni in attesa.":
        'Connect the iPhone to apply the pending actions.',
    "Niente da applicare: i brani da copiare erano già sull'iPhone in un altro formato":
        'Nothing to apply: the tracks to copy were already on the iPhone in another format',
    "fatti sull'iPhone":
        'done on the iPhone',
    '; sul PC gli stessi tag per {0}, in sospeso (i file non cambiano)':
        "; on the PC the same tags for {0}, pending (the files don't change)",
    'Nessun brano da eliminare: quelli scelti non sono stati messi da un computer':
        'No tracks to delete: the chosen ones were not put there by a computer',
    'In attesa: {0} (Applica)':
        'Pending: {0} (Apply)',
    'Copia da iPhone a PC':
        'Copy from iPhone to PC',
    'In attesa: da copiare da PC a iPhone (Applica)':
        'Pending: to copy from PC to iPhone (Apply)',
    "In attesa: da eliminare dall'iPhone (Applica)":
        'Pending: to delete from the iPhone (Apply)',
    'In attesa: i tag da portare da PC a iPhone (Applica)':
        'Pending: tags to bring from PC to iPhone (Apply)',
    'In attesa: da ricopiare da PC a iPhone (Applica)':
        'Pending: to copy again from PC to iPhone (Apply)',
    'Annulla tutto':
        'Cancel all',
    "Toglie tutte le azioni in attesa: sull'iPhone non cambia niente":
        'Removes all the pending actions: nothing changes on the iPhone',
    ' · {0} in attesa':
        ' · {0} pending',
    'Appena aggiunti: {0} brani ({1} album) {2}':
        'Just added: {0} tracks ({1} albums) {2}',
    'Appena aggiunti: {0} {1}':
        'Just added: {0} {1}',
    'Appena aggiunti: {0} {1}. I file del PC non cambiano.':
        "Just added: {0} {1}. The PC files don't change.",
    'Appena aggiunti: {0} {1}{2}':
        'Just added: {0} {1}{2}',
    "{0} per brani non aperti ora (o con l'iPhone non ancora letto): partono quando ci sono. ":
        '{0} for tracks not open now (or with the iPhone not read yet): they run when they are there. ',
    "<b>Azioni in attesa per l'iPhone: {0}.</b> {1}{2}Partono solo con Applica, a iPhone connesso.":
        '<b>Pending actions for the iPhone: {0}.</b> {1}{2}They run only with Apply, with the iPhone connected.',
    "<b>Nessuna azione in attesa.</b> Copia, Ricopia, Usa i tag, Cambia i tag ed Elimina mettono qui le azioni per l'iPhone.":
        '<b>No pending actions.</b> Copy, Copy again, Use the tags, Change the tags and Delete put the actions for the iPhone here.',
    'Applica {0} azioni…':
        'Apply {0} actions…',
    'Applica 1 azione…':
        'Apply 1 action…',
    "L'elenco si vede anche così; per applicarle connetti l'iPhone":
        'You can see the list anyway; to apply them connect the iPhone',
    "Togliere tutte le {0} azioni in attesa per l'iPhone? Sull'iPhone non cambia niente; le spunte tornano come sono sull'iPhone.":
        'Remove all the {0} pending actions for the iPhone? Nothing changes on the iPhone; the ticks go back to how they are on the iPhone.',
    "Tolte tutte le azioni in attesa: sull'iPhone non è cambiato niente.":
        'All the pending actions removed: nothing changed on the iPhone.',
    'Tolte {0} azioni dalla coda: non partono.':
        "{0} actions removed from the queue: they won't run.",
    "Nessuna azione da fare ora: quelle in attesa sono per brani non aperti o l'iPhone non è ancora stato letto.":
        'No actions to do now: the pending ones are for tracks not open or the iPhone has not been read yet.',
    'Copia 1 brano da PC a iPhone':
        'Copy 1 track from PC to iPhone',
    'Copia {0} brani ({1} album) da PC a iPhone':
        'Copy {0} tracks ({1} albums) from PC to iPhone',
    "Copia da PC a iPhone: sull'iPhone ci sono già tutti":
        'Copy from PC to iPhone: they are all on the iPhone already',
    "Elimina dall'iPhone: nessun brano con la sorgente":
        'Delete from the iPhone: no tracks with a source',
    '{0} già in attesa (Applica)':
        '{0} already pending (Apply)',
    "{0} sull'iPhone abbinati solo per i tag (≈): per toglierli o aggiornarli prima associa la sorgente (scheda iPhone)":
        '{0} on the iPhone matched only by tags (≈): to remove or update them first link the source (iPhone tab)',
    'Cambia i tag…':
        'Change the tags…',
    "Ci sono azioni in attesa per l'iPhone non ancora applicate: {0}.\n\n":
        'There are pending actions for the iPhone not applied yet: {0}.\n\n',
    "I brani spuntati vanno in attesa per Elimina dall'iPhone (partono con Applica); sul PC non cambia niente":
        'The ticked tracks go pending for Delete from the iPhone (they run with Apply); nothing changes on the PC',
    'Li ritrovi quando vuoi nella scheda iPhone con il filtro "File del PC non trovato" e il tasto destro.':
        'You find them whenever you want in the iPhone tab with the "PC file not found" filter and the right click.',
    "Anche sull'iPhone (va in attesa)":
        'Also on the iPhone (goes pending)',
    "Per i brani che sull'iPhone hanno la sorgente certa (registro): dopo il salvataggio i tag nuovi vanno in attesa per l'iPhone e partono con Applica. Spenta, l'iPhone resta com'è e la differenza si vede (⟳).":
        'For the tracks that have a certain source on the iPhone (registry): after saving, the new tags go pending for the iPhone and run with Apply. Off, the iPhone stays as it is and the difference shows (⟳).',
    "{0}\nSull'iPhone questo brano ha tag diversi: Usa i tag da PC a iPhone o da iPhone a PC (tasto destro) sceglie quali tenere":
        '{0}\nOn the iPhone this track has different tags: Use the tags from PC to iPhone or from iPhone to PC (right click) chooses which to keep',
    'ricopia':
        'ricopia',
    'elimina':
        'elimina',
    'il brano non ha un album con identificativo: usa Ricopia da PC a iPhone':
        'the track has no album with an identifier: use Copy again from PC to iPhone',
    "Non c'è un brano con lo stesso artista, album e titolo nella Libreria del PC. Se vuoi conservarli, salvali sul PC dalla scheda iPhone (tasto destro → Copia da iPhone a PC); a volte sono solo scritti in modo diverso.":
        'There is no track with the same artist, album and title in the PC Library. If you want to keep them, save them on the PC from the iPhone tab (right click → Copy from iPhone to PC); sometimes they are just written differently.',
    'save':
        'save',
    'replace':
        'replace',
    'edit':
        'edit',
    'cover':
        'cover',
    'refile':
        'refile',
    'link':
        'link',
    "Nell'album sbagliato sull'iPhone":
        'In the wrong album on the iPhone',
    "Rimetti nell'album giusto (Ricopia da PC a iPhone): {0}, {1} album":
        'Put back in the right album (Copy again from PC to iPhone): {0}, {1} albums',
    '\nNell\'app Musica sta in un album di "{0}", non del suo artista dell\'album: il pulsante Rimetti nell\'album giusto, nella barra sopra i brani':
        '\nIn the Music app it is in an album by "{0}", not by its album artist: the Put back in the right album button, in the bar above the tracks',
    'probable':
        'probable',
    'proposed':
        'proposed',
    'unlink':
        'unlink',
    'note':
        'note',
    'Copia da iPhone a PC…':
        'Copy from iPhone to PC…',
    'Rileggi':
        'Reload',
    "F5. Rilegge la musica dell'app Musica dall'iPhone connesso; senza iPhone rifà il confronto con il PC":
        "F5. Reloads the Music app's music from the connected iPhone; without iPhone redoes the comparison with the PC",
    'Come funziona: i segni delle colonne e dove sono le azioni':
        'How it works: the signs of the columns and where the actions are',
    'Scegli dei brani, o un artista o un album:':
        'Choose some tracks, or an artist or an album:',
    '1 brano scelto:':
        '1 track chosen:',
    '{0} brani scelti:':
        '{0} tracks chosen:',
    'Associa al file sul PC tutti i brani senza sorgente…':
        'Link to the file on the PC all the tracks without a source…',
    "Rifai le playlist per artista sull'iPhone…":
        'Redo the playlists by artist on the iPhone…',
    "{0} nell'app Musica · {1}":
        '{0} in the Music app · {1}',
    'all':
        'all',
    'Tutti i brani della cartella aperta (del formato scelto)':
        'All the tracks of the open folder (of the chosen format)',
    'absent':
        'absent',
    "Non sull'iPhone":
        'Not on the iPhone',
    "I brani che nell'app Musica dell'iPhone non ci sono (anche quelli in attesa di Copia da PC a iPhone)":
        "The tracks that are not in the iPhone's Music app (also those waiting for Copy from PC to iPhone)",
    '✔ Uguali':
        '✔ Same',
    "Sull'iPhone c'è questo brano, con la sorgente certa e gli stessi tag":
        'This track is on the iPhone, with a certain source and the same tags',
    '⟳ Tag diversi':
        '⟳ Different tags',
    "Sull'iPhone c'è questo brano, con la sorgente certa ma tag diversi: Usa i tag o Ricopia":
        'This track is on the iPhone, with a certain source but different tags: Use the tags or Copy again',
    '≈ Da rivedere':
        '≈ To review',
    "Sull'iPhone c'è un brano con gli stessi tag, ma non è collegato a questo file: associalo nella scheda iPhone":
        "On the iPhone there is a track with the same tags, but it isn't linked to this file: link it in the iPhone tab",
    'edited':
        'edited',
    '✎ Modificati':
        '✎ Edited',
    'Brani con modifiche dei tag in sospeso (i file non cambiano)':
        "Tracks with pending tag changes (the files don't change)",
    'stray':
        'stray',
    'costante':
        'constant',
    'variabile':
        'variable',
    'media':
        'average',
    'ALAC':
        'ALAC',
    'AAC':
        'AAC',
    'WMA Lossless':
        'WMA Lossless',
    'Vorbis':
        'Vorbis',
    'Opus':
        'Opus',
    'non compresso':
        'uncompressed',
    'senza perdita':
        'lossless',
    'Fuori cartella':
        'Outside the folder',
    "Brani di un album che stanno in una cartella diversa da quella con il resto dell'album (CD1, Disc 2… contano come una cartella sola): sull'iPhone finiscono nello stesso album":
        "Tracks of an album that sit in a different folder from the rest of the album (CD1, Disc 2… count as one folder): on the iPhone they end up in the same album",
    "{0}\nIl resto dell'album è in un'altra cartella:\n{1}\nSull'iPhone questi brani finiscono nello stesso album.":
        "{0}\nThe rest of the album is in another folder:\n{1}\nOn the iPhone these tracks end up in the same album.",
    'pending':
        'pending',
    '＋ In attesa':
        '＋ Pending',
    "Brani con un'azione per l'iPhone in attesa di Applica":
        'Tracks with an action for the iPhone waiting for Apply',
    'F5. Rilegge la cartella aperta: i file nuovi, tolti o cambiati (gli altri dalla cache dei tag). Con Maiusc premuto rilegge tutti i file da zero.':
        'F5. Reloads the open folder: new, removed or changed files (the others from the tag cache). With Shift held it reloads all the files from scratch.',
    'copy':
        'copy',
    'export':
        'export',
    "Chiude l'editor dei tag: si riapre con Cambia i tag o il tasto E":
        'Closes the tag editor: it opens again with Change the tags or the E key',
    'Esporta in una cartella…':
        'Export to a folder…',
    'Strumenti ▾':
        'Tools ▾',
    'Tutte le cartelle della musica di questo PC ({0})':
        'All the music folders of this PC ({0})',
    'La mia musica':
        'My music',
    'Mostra tutte le cartelle della musica di questo PC (Impostazioni → Cartelle della musica)':
        'Shows all the music folders of this PC (Settings → Music folders)',
    "Quali cartelle mostrare: tutte le cartelle della musica di questo PC (Impostazioni), una sola, o un'altra cartella qualsiasi":
        'Which folders to show: all the music folders of this PC (Settings), just one, or any other folder',
    'Cartelle:':
        'Folders:',
    "L'ultima cartella usata non è disponibile ({0}): apro le cartelle della musica":
        'The last folder used is not available ({0}): opening the music folders',
    'Benvenuto! Premi "Apri cartella" per vedere la tua musica, o "Importa cartella" per copiarla nella Libreria. Le cartelle della musica di questo PC si scelgono in Impostazioni.':
        'Welcome! Press "Open folder" to see your music, or "Import folder" to copy it into the Library. The music folders of this PC are chosen in Settings.',
    'le cartelle della musica ({0})':
        'the music folders ({0})',
    'Le cartelle della musica di questo PC non ci sono (dischi scollegati?): sceglile in Impostazioni → Cartelle della musica':
        'The music folders of this PC are not there (disconnected drives?): choose them in Settings → Music folders',
    'Tutte le cartelle della musica ({0})':
        'All the music folders ({0})',
    'Altra: {0}':
        'Other: {0}',
    "Apri un'altra cartella…":
        'Open another folder…',
    'Le cartelle della musica di questo PC: {0}':
        'The music folders of this PC: {0}',
    'I brani aperti nella scheda PC ({0})':
        'The tracks open in the PC tab ({0})',
    "La musica dell'app Musica dell'iPhone ({0} brani, {1}), confrontata con le cartelle della musica del PC":
        "The music of the iPhone's Music app ({0} tracks, {1}), compared with the PC's music folders",
    'Cartelle della musica':
        'Music folders',
    "La scheda PC le mostra insieme (La mia musica). Togliere una cartella dall'elenco non cancella niente.":
        'The PC tab shows them together (My music). Removing a folder from the list deletes nothing.',
    'Aggiungi una cartella…':
        'Add a folder…',
    'Togli':
        'Remove',
    'Giù':
        'Down',
    'Segna come Libreria':
        'Mark as Library',
    'La Libreria è dove vanno Importa cartella e Copia da iPhone a PC':
        'The Library is where Import folder and Copy from iPhone to PC go',
    '<b>Cartelle della musica su {0}</b>':
        '<b>Music folders on {0}</b>',
    "Toglie la cartella dall'elenco (non cancella niente). Togliendo la Libreria, diventa Libreria la prima cartella che resta; l'ultima cartella non si toglie.":
        'Removes the folder from the list (nothing is deleted). Removing the Library makes the first remaining folder the Library; the last folder cannot be removed.',
    'Aggiungi la cartella aperta':
        'Add the open folder',
    'I brani di queste cartelle e delle loro sottocartelle non si vedono nella scheda PC e non si usano per Associa sorgenti e i controlli. I file non cambiano.':
        'The tracks in these folders and their subfolders are not shown in the PC tab and are not used by Link sources and the checks. The files do not change.',
    'Escludi una cartella…':
        'Exclude a folder…',
    'La cartella torna a vedersi (i file non sono mai cambiati)':
        'The folder is shown again (the files never changed)',
    '<b>Cartelle escluse</b>':
        '<b>Excluded folders</b>',
    'Sottocartelle da non usare, con le loro sottocartelle (per esempio le suonerie dentro la cartella della musica). Sono le stesse di <i>Nascondi la cartella</i> (tasto destro nella scheda PC) e di <i>Cartelle nascoste…</i>.':
        'Subfolders not to use, with their subfolders (for example the ringtones inside the music folder). They are the same as <i>Hide the folder</i> (right click in the PC tab) and <i>Hidden folders…</i>.',
    'Una cartella da escludere':
        'A folder to exclude',
    'All\'avvio si apre {0}: è stata aperta con Apri cartella e non è tra le cartelle della musica. Per averla qui: "Aggiungi la cartella aperta".':
        'At startup {0} opens: it was opened with Open folder and is not among the music folders. To have it here: "Add the open folder".',
    "La scheda PC le mostra insieme (<i>La mia musica</i>, Ctrl+L) e <i>Associa sorgenti</i> cerca in tutte. L'ordine conta: tra due copie dello stesso brano vince quella più in alto (le <i>Cartelle preferite</i> di Generale, se ci sono, contano prima). Valgono solo su questo computer: con la cartella dati condivisa, ogni PC ha le sue.":
        'The PC tab shows them together (<i>My music</i>, Ctrl+L) and <i>Link sources</i> searches all of them. The order matters: between two copies of the same track the higher one wins (the <i>Preferred folders</i> of General, if any, count first). They apply only to this computer: with a shared data folder, each PC has its own.',
    'Altri computer (si vedono, non si usano qui):\n':
        'Other computers (shown, not used here):\n',
    'Altri computer: nessuno.':
        'Other computers: none.',
    'Una cartella della musica':
        'A music folder',
    "<b>Cosa succede dopo.</b> La verifica va in background: puoi continuare a usare il programma (qui e nella barra di stato si vede a che punto è, <i>Ferma</i> la interrompe). L'icona accanto a ogni album nell'elenco Album ne dice l'esito man mano. Alla fine i risultati compaiono qui sotto: per ogni album le tracce dell'edizione trovata e i tuoi file, le tracce mancanti in rosso; puoi scegliere un'altra edizione e <i>Correggere i tag</i> con quei dati e la copertina (restano in sospeso, per le copie: i file del PC non cambiano).":
        "<b>What happens next.</b> The check runs in the background: you can keep using the program (here and in the status bar you see how far it is, <i>Stop</i> interrupts it). The icon next to each album in the Album list tells its outcome as it goes. At the end the results appear below: for each album the tracks of the edition found and your files, the missing tracks in red; you can choose another edition and <i>Correct the tags</i> with that data and the cover (they stay pending, for the copies: the PC files don't change).",
    'Avvia la verifica':
        'Start the check',
    'Interrompe la verifica: i risultati già trovati restano':
        'Interrupts the check: the results already found stay',
    '<b>Verificare {0} album</b> (quelli scelti negli elenchi della scheda PC, o tutti).':
        '<b>Check {0} albums</b> (those chosen in the lists of the PC tab, or all).',
    "{0}  <span style='color: gray; font-weight: normal'>{1}</span>":
        "{0}  <span style='color: gray; font-weight: normal'>{1}</span>",
    "Confronta i tuoi brani tra loro (e con l'iPhone), senza cataloghi online: doppioni, artisti scritti in modi diversi, album divisi, tag mancanti.":
        'Compares your tracks with each other (and with the iPhone), without online catalogs: duplicates, artists written in different ways, split albums, missing tags.',
    'Confronta gli album con i cataloghi su internet: brani mancanti, tag giusti, copertina. In background.':
        'Compares the albums with the catalogs on the internet: missing tracks, right tags, cover. In the background.',
    'Qui compaiono i risultati di Controlla la musica.':
        'The results of Check the music appear here.',
    'Risultati del controllo':
        'Results of the scan',
    'Qui compaiono i risultati di Verifica album online, alla fine o quando la fermi.':
        'The results of Check albums online appear here, at the end or when you stop it.',
    'Risultati della verifica':
        'Results of the check',
    'Vedi':
        'See',
    'La linguetta Controlli, con la verifica e i suoi risultati':
        'The Checks tab, with the check and its results',
    'Controlli':
        'Checks',
    'F7: la linguetta Controlli. Confronta gli album scelti (o tutti) con i cataloghi online (Deezer, Apple Music, Discogs, MusicBrainz): brani mancanti, tag giusti, copertina. In background':
        'F7: the Checks tab. Compares the chosen albums (or all) with the online catalogs (Deezer, Apple Music, Discogs, MusicBrainz): missing tracks, right tags, cover. In the background',
    "F6: la linguetta Controlli. Cerca i problemi confrontando i tuoi brani tra loro (cartelle aperte o iPhone), senza cataloghi online: file non aggiornati, album con pochi brani, collezioni divise, artisti scritti in modi diversi, brani duplicati (con l'AI, se configurata)":
        'F6: the Checks tab. Looks for problems by comparing your tracks with each other (open folders or iPhone), without online catalogs: files not updated, albums with few tracks, split collections, artists written in different ways, duplicate tracks (with the AI, if configured)',
    'Cartelle della musica, AI della scansione, lingua, profili AI e chiavi':
        'Music folders, scan AI, language, AI profiles and keys',
    'La verifica è già in corso: aspetta la fine o premi Ferma.':
        'The check is already running: wait for the end or press Stop.',
    'In corso: 0 di {0} album':
        'Running: 0 of {0} albums',
    'In corso: {0} di {1} album':
        'Running: {0} of {1} albums',
    'Interruzione…':
        'Stopping…',
    'Avvia il controllo':
        'Start the scan',
    "Aspetta la fine dell'operazione in corso.":
        'Wait for the current operation to finish.',
    'Apri cartella…':
        'Open folder…',
    'Importa nella Libreria…':
        'Import into the Library…',
    'Esporta…':
        'Export…',
    'Strumenti':
        'Tools',
    'Mostra tutti':
        'Show all',
    'Torna al filtro Tutti':
        'Back to the All filter',
    'Filtro «{0}»: si vedono {1} di {2} brani':
        'Filter «{0}»: showing {1} of {2} tracks',
    'brano copiato da PC a iPhone':
        'track copied from PC to iPhone',
    'brani copiati da PC a iPhone':
        'tracks copied from PC to iPhone',
    'brano ricopiato da PC a iPhone':
        'track copied again from PC to iPhone',
    'brani ricopiati da PC a iPhone':
        'tracks copied again from PC to iPhone',
    'brano con i tag presi dal PC':
        'track with the tags taken from the PC',
    'brani con i tag presi dal PC':
        'tracks with the tags taken from the PC',
    "brano con i tag cambiati sull'iPhone":
        'track with the tags changed on the iPhone',
    "brani con i tag cambiati sull'iPhone":
        'tracks with the tags changed on the iPhone',
    "brano eliminato dall'iPhone":
        'track deleted from the iPhone',
    "brani eliminati dall'iPhone":
        'tracks deleted from the iPhone',
    "Fatto sull'iPhone:":
        'Done on the iPhone:',
    "Sull'iPhone non è cambiato niente.":
        'Nothing changed on the iPhone.',
    '1 azione non è riuscita: resta in attesa (barra blu, Applica) per riprovarla.':
        '1 action did not succeed: it stays pending (blue bar, Apply) to try it again.',
    '{0} azioni non sono riuscite: restano in attesa (barra blu, Applica) per riprovarle.':
        '{0} actions did not succeed: they stay pending (blue bar, Apply) to try them again.',
    'Motivi':
        'Reasons',
    'Operazione interrotta: le azioni non fatte restano in attesa.':
        'Operation interrupted: the actions not done stay pending.',
    'Applicata 1 azione':
        '1 action applied',
    'Applicate {0} azioni':
        '{0} actions applied',
    "{0} sull'iPhone; 1 non riuscita resta in attesa.":
        '{0} on the iPhone; 1 that did not succeed stays pending.',
    "{0} sull'iPhone; {1} non riuscite restano in attesa.":
        '{0} on the iPhone; {1} that did not succeed stay pending.',
    "{0} sull'iPhone.":
        '{0} on the iPhone.',
    "L'iPhone non mostra ancora {0}: lo rileggo tra {1} secondi":
        'The iPhone does not show {0} yet: reading it again in {1} seconds',
    "rilettura della musica dell'app Musica":
        "reading the Music app's music again",
    "Rilettura dell'iPhone":
        'Reading the iPhone again',
    'Copia negli appunti':
        'Copy to the clipboard',
    'Nome del file ({0})':
        'File name ({0})',
    'Percorso completo ({0})':
        'Full path ({0})',
    'Cartella ({0})':
        'Folder ({0})',
    "versione vecchia non tolta dall'iPhone (ora ci sono due copie: elimina quella vecchia): ":
        'old version not removed from the iPhone (now there are two copies: delete the old one): ',
    ' e altre {0}':
        ' and {0} more',
    '• {0} playlist rifatte con i brani ricopiati: {1}':
        '• {0} playlists rebuilt with the copied-again tracks: {1}',
    '\n\nI brani ricopiati non sono più nelle playlist fatte sul telefono, che il computer non può cambiare: rimettili a mano (app Musica, playlist, Modifica, Aggiungi musica). Quelle messe da un computer (anche le ♪ di Playlist per artista) si rifanno da sole:\n':
        "\n\nThe copied-again tracks are no longer in the playlists made on the phone, which the computer can't change: put them back by hand (Music app, playlist, Edit, Add Music). Those added by a computer (the ♪ ones of Playlists by artist too) are rebuilt automatically:\n",
    '\n\nI brani da ricopiare sono in playlist messe da un computer: si rifanno da sole, con i brani nuovi al loro posto:\n':
        '\n\nThe tracks to copy again are in playlists added by a computer: they are rebuilt automatically, with the new tracks in their place:\n',
    '\n\nI brani da ricopiare sono in playlist fatte sul telefono: il computer non le può cambiare, andranno sistemate a mano (alla fine te le ricordo):\n':
        "\n\nThe tracks to copy again are in playlists made on the phone: the computer can't change them, they will need fixing by hand (I'll remind you at the end):\n",
    'playlist con i brani nuovi: {0}':
        'playlists with the new tracks: {0}',
    "playlist non rifatta: i brani nuovi non risultano ancora sull'iPhone e mancano dalla playlist":
        "playlist not rebuilt: the new tracks aren't on the iPhone yet and are missing from the playlist",
    'non rifatte con i brani nuovi: ':
        'not rebuilt with the new tracks: ',
    'playlist':
        'playlist',
    'non rifatte con i brani nuovi (mancano dalle playlist): {0}':
        'not rebuilt with the new tracks (they are missing from the playlists): {0}',
    'non lette prima di ricopiare: non si rifanno da sole ({0})':
        "not read before copying again: they won't be rebuilt automatically ({0})",
    'Dal file associato sul PC':
        'From the linked file on the PC',
    'Il file associato sul PC non ha la copertina':
        'The linked file on the PC has no cover',
    "Nessun file associato sul PC: l'immagine che ha l'iPhone non si legge da qui":
        "No linked file on the PC: the iPhone's own image can't be read from here",
    'Brani di album diversi':
        'Tracks of different albums',
    "\nSull'iPhone l'album non ha l'immagine: il pulsante Ricopia le copertine da PC a iPhone, nella barra sopra i brani":
        '\nOn the iPhone the album has no image: the Copy the covers again from PC to iPhone button, in the bar above the tracks',
    "Non si cambia qui: sull'iPhone l'artista si rinominerebbe per tutti i suoi brani. Cambialo nella scheda PC, poi usa Ricopia da PC a iPhone.":
        'Not changed here: on the iPhone the artist would be renamed for all their tracks. Change it in the PC tab, then use Copy again from PC to iPhone.',
    "Non si cambia sull'iPhone: cambialo nella scheda PC, poi usa Ricopia da PC a iPhone.":
        'Not changed on the iPhone: change it in the PC tab, then use Copy again from PC to iPhone.',
    'Anche sul PC':
        'Also on the PC',
    "Si cambiano titolo (un brano alla volta), album, numeri, anno, genere e Compilation: vanno in attesa e l'iPhone cambia con Applica. Un campo vuoto non cambia; anno o numero 0 lo svuota. Artista e artista dell'album si cambiano nella scheda PC, poi Ricopia da PC a iPhone.":
        "You can change title (one track at a time), album, numbers, year, genre and Compilation: they wait in the queue and the iPhone changes with Apply. An empty field doesn't change; year or number 0 clears it. Artist and album artist are changed in the PC tab, then Copy again from PC to iPhone.",
    '{0} brani selezionati: i campi cambiati valgono per tutti':
        '{0} tracks selected: the changed fields apply to all of them',
    "Non messi sull'iPhone da un computer (acquistati, scaricati o di un altro programma): i tag si vedono ma non si cambiano":
        "Not put on the iPhone by a computer (bought, downloaded or from another program): the tags are shown but can't be changed",
    '{0} dei brani scelti non sono stati messi da un computer: i loro tag non cambiano':
        "{0} of the chosen tracks were not put there by a computer: their tags don't change",
    'Copiati negli appunti i nomi di {0} cartelle':
        'Copied the names of {0} folders to the clipboard',
    'Copiati negli appunti i percorsi di {0} cartelle':
        'Copied the paths of {0} folders to the clipboard',
    'Nome della cartella ({0})':
        'Folder name ({0})',
    'Percorso della cartella ({0})':
        'Folder path ({0})',
    'Invia come suoneria (PC → iPhone)':
        'Send as ringtone (PC → iPhone)',
    'i .m4r della cartella delle suonerie':
        'the .m4r files of the ringtones folder',
    'da inviare da PC a iPhone':
        'to send from PC to iPhone',
    "Elimina le suonerie dall'iPhone":
        'Delete the ringtones from the iPhone',
    'solo quelle messe da un computer; i file del PC non cambiano':
        'only those put there by a computer; the PC files do not change',
    '1 suoneria':
        '1 ringtone',
    '{0} suonerie':
        '{0} ringtones',
    'suoneria inviata da PC a iPhone':
        'ringtone sent from PC to iPhone',
    'suonerie inviate da PC a iPhone':
        'ringtones sent from PC to iPhone',
    "suoneria eliminata dall'iPhone":
        'ringtone deleted from the iPhone',
    "suonerie eliminate dall'iPhone":
        'ringtones deleted from the iPhone',
    "Connetti l'iPhone: il brano si legge dall'iPhone (sola lettura)":
        'Connect the iPhone: the track is read from the iPhone (read only)',
    'non letto':
        'not read',
    "Il brano non si legge dall'iPhone: {0}":
        'The track cannot be read from the iPhone: {0}',
    "Lettura del brano dall'iPhone":
        'Reading the track from the iPhone',
    'Suonerie':
        'Ringtones',
    'Crea una suoneria… (scegli un brano solo)':
        'Create a ringtone… (choose a single track)',
    'Crea una suoneria… (manca ffmpeg: Impostazioni → Suonerie)':
        'Create a ringtone… (ffmpeg missing: Settings → Ringtones)',
    'Crea una suoneria…':
        'Create a ringtone…',
    'Un pezzo del brano (al massimo 40 s) diventa un .m4r nuovo nella cartella delle suonerie: il brano non cambia':
        'A part of the track (40 s at most) becomes a new .m4r in the ringtones folder: the track does not change',
    'Crea una suoneria':
        'Create a ringtone',
    'Suoneria creata: {0} (scheda Suonerie)':
        'Ringtone created: {0} (Ringtones tab)',
    'Lettura del brano…':
        'Reading the track…',
    'start':
        'start',
    'end':
        'end',
    'new':
        'new',
    "Scegli il pezzo (al massimo {0} secondi): trascina sulla forma d'onda, sposta i bordi o scrivi inizio e fine. Il brano non cambia: la suoneria è un file nuovo nella cartella delle suonerie.":
        'Choose the part ({0} seconds at most): drag on the waveform, move the edges or type start and end. The track does not change: the ringtone is a new file in the ringtones folder.',
    "Dissolvenza all'inizio":
        'Fade in',
    'Dissolvenza alla fine':
        'Fade out',
    "Il nome che vedrai nell'elenco delle suonerie dell'iPhone (e del file sul PC)":
        'The name you will see in the iPhone ringtone list (and of the file on the PC)',
    "Mettila anche in attesa per l'iPhone (Invia come suoneria, parte con Applica)":
        'Also queue it for the iPhone (Send as ringtone, runs with Apply)',
    'Ascolta il pezzo':
        'Play the part',
    "L'ascolto c'è solo su Windows":
        'Playback is available on Windows only',
    'Cartella delle suonerie: {0}':
        'Ringtones folder: {0}',
    'Inizio':
        'Start',
    'Fine':
        'End',
    'Nome della suoneria':
        'Ringtone name',
    'Crea la suoneria':
        'Create the ringtone',
    'Il brano non si legge':
        'The track cannot be read',
    'Durata: {0} s (da {1} a {2})':
        'Length: {0} s (from {1} to {2})',
    'Scrivi il nome della suoneria.':
        'Type the name of the ringtone.',
    'messa da un computer':
        'put there by a computer',
    "fatta sull'iPhone":
        'made on the iPhone',
    'resto, non attiva':
        'leftover, not active',
    "Inviata da un computer: si toglie con Elimina dall'iPhone":
        'Sent by a computer: remove it with Delete from the iPhone',
    "Fatta sull'iPhone (GarageBand, app File): un computer non la può togliere, la puoi copiare sul PC":
        'Made on the iPhone (GarageBand, Files app): a computer cannot remove it, you can copy it to the PC',
    "Un file rimasto nella cartella delle suonerie dell'iPhone che nessun elenco registra: non è tra le suonerie che l'iPhone mostra. La puoi copiare sul PC":
        'A file left in the iPhone ringtones folder that no list records: it is not among the ringtones the iPhone shows. You can copy it to the PC',
    "<b>Le suonerie.</b> A sinistra i file <b>.m4r</b> della cartella delle suonerie del PC: li crei con <b>Crea una suoneria…</b> (tasto destro su un brano nella scheda PC o iPhone) o ce li metti tu. <b>Invia come suoneria (PC → iPhone)</b> li mette in attesa: partono con <b>Applica</b>, come la musica. A destra le suonerie dell'iPhone: <b>Copia da iPhone a PC</b> le salva nella cartella delle suonerie (file nuovi); <b>Elimina dall'iPhone</b> toglie quelle messe da un computer (in attesa fino ad Applica). Sull'iPhone le trovi in Impostazioni → Suoni e feedback aptico → Suoneria, in cima all'elenco.":
        '<b>Ringtones.</b> On the left the <b>.m4r</b> files of the PC ringtones folder: you create them with <b>Create a ringtone…</b> (right click on a track in the PC or iPhone tab) or put them there yourself. <b>Send as ringtone (PC → iPhone)</b> queues them: they run with <b>Apply</b>, like the music. On the right the iPhone ringtones: <b>Copy from iPhone to PC</b> saves them in the ringtones folder (new files); <b>Delete from the iPhone</b> removes those put there by a computer (queued until Apply). On the iPhone you find them in Settings → Sounds &amp; Haptics → Ringtone, at the top of the list.',
    'Scegli la cartella…':
        'Choose the folder…',
    'La cartella delle suonerie (anche in Impostazioni → Suonerie)':
        'The ringtones folder (also in Settings → Ringtones)',
    "Sull'iPhone":
        'On the iPhone',
    'Ascolta':
        'Play',
    'Rinomina…':
        'Rename…',
    'Sposta nel cestino…':
        'Move to the Recycle Bin…',
    'Sul PC: la cartella delle suonerie':
        'On the PC: the ringtones folder',
    "Leggi le suonerie dell'iPhone":
        'Read the iPhone ringtones',
    'Specie':
        'Kind',
    "File sull'iPhone":
        'File on the iPhone',
    'La cartella delle suonerie':
        'The ringtones folder',
    "Scegli prima la cartella delle suonerie: lì vanno le suonerie create e quelle copiate dall'iPhone.":
        'First choose the ringtones folder: the ringtones you create and those copied from the iPhone go there.',
    '<i>Cartella delle suonerie non ancora scelta</i>':
        '<i>Ringtones folder not chosen yet</i>',
    "<b>{0}</b> (non c'è ancora: si crea con la prima suoneria)":
        '<b>{0}</b> (it does not exist yet: it is created with the first ringtone)',
    '＋ in attesa (Applica)':
        '＋ queued (Apply)',
    'non si invia: {0}':
        'cannot be sent: {0}',
    'troppo lunga (max 40 s)':
        'too long (max 40 s)',
    "Connetti l'iPhone per leggerne le suonerie.":
        'Connect the iPhone to read its ringtones.',
    "lettura delle suonerie dell'iPhone":
        'reading the iPhone ringtones',
    "Suonerie dell'iPhone":
        'iPhone ringtones',
    "Suonerie dell'iPhone non ancora lette.":
        'iPhone ringtones not read yet.',
    '{0} suonerie su {1}':
        '{0} ringtones on {1}',
    'Appena aggiunte: {0} da inviare da PC a iPhone.':
        'Just added: {0} to send from PC to iPhone.',
    ' {0} non si possono inviare (non AAC o più lunghe di 40 s).':
        ' {0} cannot be sent (not AAC or longer than 40 s).',
    "Appena aggiunte: {0} da eliminare dall'iPhone. I file del PC non cambiano.":
        'Just added: {0} to delete from the iPhone. The PC files do not change.',
    'Nessuna suoneria da eliminare: quelle scelte non sono state messe da un computer':
        'No ringtone to delete: the chosen ones were not put there by a computer',
    'Rinomina':
        'Rename',
    'Il nuovo nome del file {0} (senza .m4r):':
        'The new name of the file {0} (without .m4r):',
    'Rinominato in {0}':
        'Renamed to {0}',
    'Sposta nel cestino':
        'Move to the Recycle Bin',
    'Spostare nel Cestino di Windows {0} file della cartella delle suonerie?':
        'Move {0} files of the ringtones folder to the Windows Recycle Bin?',
    "Si recuperano dal Cestino. Sull'iPhone non cambia niente.":
        'They can be restored from the Recycle Bin. Nothing changes on the iPhone.',
    "Connetti l'iPhone per copiarne le suonerie sul PC.":
        'Connect the iPhone to copy its ringtones to the PC.',
    'Copia delle suonerie da iPhone a PC':
        'Copying the ringtones from iPhone to PC',
    'Copiate da iPhone a PC: {0}, nella cartella {1}.':
        'Copied from iPhone to PC: {0}, in the folder {1}.',
    'Non copiate:':
        'Not copied:',
    'Copia {0} suonerie da iPhone a PC':
        'Copy {0} ringtones from iPhone to PC',
    'Copia la suoneria da iPhone a PC':
        'Copy the ringtone from iPhone to PC',
    "Elimina dall'iPhone ({0})":
        'Delete from the iPhone ({0})',
    "Elimina dall'iPhone: solo quelle messe da un computer":
        'Delete from the iPhone: only those put there by a computer',
    'non ancora scelta: la chiede la prima suoneria':
        'not chosen yet: the first ringtone asks for it',
    "Dove vanno le suonerie create con Crea una suoneria e quelle copiate dall'iPhone. Se sta dentro una cartella della musica, la scheda PC non la mostra.":
        'Where the ringtones made with Create a ringtone and those copied from the iPhone go. If it is inside a music folder, the PC tab does not show it.',
    'vuoto: ffmpeg del PATH':
        'empty: ffmpeg from the PATH',
    'Il file ffmpeg.exe, o la cartella che lo contiene. Vuoto: quello nel PATH.':
        'The ffmpeg.exe file, or the folder containing it. Empty: the one in the PATH.',
    "Crea una suoneria (tasto destro su un brano nella scheda PC o iPhone) usa <b>ffmpeg</b>, che il programma non contiene: installalo tu (per esempio <i>winget install ffmpeg</i>). Le suonerie si vedono e si inviano all'iPhone dalla scheda Suonerie.":
        'Create a ringtone (right click on a track in the PC or iPhone tab) uses <b>ffmpeg</b>, which the program does not include: install it yourself (for example <i>winget install ffmpeg</i>). The ringtones are shown and sent to the iPhone from the Ringtones tab.',
    'Cartella delle suonerie':
        'Ringtones folder',
    'ffmpeg':
        'ffmpeg',
    'ffmpeg (ffmpeg.exe);;Programmi (*.exe)':
        'ffmpeg (ffmpeg.exe);;Programs (*.exe)',
    '✔ trovato: {0}':
        '✔ found: {0}',
    '✖ non trovato: scegli il file ffmpeg.exe':
        '✖ not found: choose the ffmpeg.exe file',
    '✖ ffmpeg non è nel PATH: installalo o scegli il file ffmpeg.exe':
        '✖ ffmpeg is not in the PATH: install it or choose the ffmpeg.exe file',
    'computer':
        'computer',
    'iphone':
        'iphone',
    'resto':
        'resto',
    "il file non c'è più":
        'the file is no longer there',
    'il file {0}':
        'the file {0}',
    "dura più di 40 secondi: l'iPhone non la accetta":
        'it lasts more than 40 seconds: the iPhone does not accept it',
    "l'iPhone non l'ha tolta":
        'the iPhone did not remove it',
    "l'iPhone non l'ha ricevuta":
        'the iPhone did not receive it',
    "fatta sull'iPhone: un computer non la può togliere":
        'made on the iPhone: a computer cannot remove it',
    'suonerie':
        'ringtones',
    'Ringtone':
        'Ringtone',
    "l'iPhone non accetta suonerie da un computer":
        'the iPhone does not accept ringtones from a computer',
    'suoneria senza identificativo':
        'ringtone without an identifier',
    'una suoneria dura al massimo 40 secondi':
        'a ringtone lasts 40 seconds at most',
    'GUID della suoneria non valido':
        'invalid ringtone GUID',
    'nome della suoneria':
        'ringtone name',
    'una suoneria messa da un computer sta in iTunes_Control/Ringtones':
        'a ringtone put there by a computer is in iTunes_Control/Ringtones',
    "l'ancora delle suonerie dell'iPhone non si legge":
        'the iPhone ringtone anchor cannot be read',
    "nella cartella delle suonerie dell'iPhone c'è {0}: un'altra sincronizzazione non è finita, niente da fare":
        'the iPhone ringtones folder contains {0}: another sync has not finished, nothing done',
    'una suoneria va in iTunes_Control/Ringtones':
        'a ringtone goes in iTunes_Control/Ringtones',
    "l'iPhone ha interrotto la sincronizzazione delle suonerie (codice {0})":
        'the iPhone interrupted the ringtone sync (code {0})',
    'la suoneria caricata ha una dimensione diversa':
        'the uploaded ringtone has a different size',
    'Per creare una suoneria serve ffmpeg, che il programma non contiene: installalo (per esempio winget install ffmpeg) e, se non è nel PATH, scegli il file ffmpeg.exe in Impostazioni → Suonerie.':
        'Creating a ringtone needs ffmpeg, which the program does not include: install it (for example winget install ffmpeg) and, if it is not in the PATH, choose the ffmpeg.exe file in Settings → Ringtones.',
    'ffmpeg non è partito: {0}':
        'ffmpeg did not start: {0}',
    'ffmpeg non è riuscito: ':
        'ffmpeg failed: ',
    'codice {0}':
        'code {0}',
    '{0}: ffmpeg non ha letto audio':
        '{0}: ffmpeg read no audio',
    'aac':
        'aac',
    'ipod':
        'ipod',
    'wav':
        'wav',
    'Suoneria':
        'Ringtone',
    'Una suoneria dura al massimo {0} secondi.':
        'A ringtone lasts {0} seconds at most.',
    'non è AAC':
        'is not AAC',
    'non si legge ({0})':
        'cannot be read ({0})',
    'Si rinominano solo le suonerie della cartella delle suonerie.':
        'Only the ringtones of the ringtones folder can be renamed.',
    "C'è già un file {0}.":
        'There is already a file {0}.',
    'Doppioni: stessa canzone nello stesso album':
        'Duplicates: same song in the same album',
    'keep':
        'keep',
    'dedupe':
        'dedupe',
    '\nDoppione: {0} copie di questa canzone nello stesso album. {1}. Nella barra sopra i brani: Togli le copie in più, o Tieni questa copia':
        '\nDuplicate: {0} copies of this song in the same album. {1}. In the bar above the tracks: Remove the extra copies, or Keep this copy',
    '\nLa stessa canzone anche in: ':
        '\nThe same song also in: ',
    "Togli le copie in più (Elimina dall'iPhone): {0}; resta la migliore di ogni canzone":
        'Remove the extra copies (Delete from the iPhone): {0}; the best copy of each song stays',
    "Tieni questa copia, togli le altre (Elimina dall'iPhone): {0}":
        'Keep this copy, remove the others (Delete from the iPhone): {0}',
    "\n\n{0} da copiare ci sono già sull'iPhone nello stesso album: sostituiscono la copia vecchia (prima si copia il nuovo, poi si toglie il vecchio; le playlist messe da un computer si rifanno da sole)":
        '\n\n{0} to copy are already on the iPhone in the same album: they replace the old copy (first the new one is copied, then the old one is removed; playlists put there by a computer are rebuilt automatically)',
    '. Si tolgono anche altre {0} dello stesso album':
        '. Other {0} of the same album are removed too',
    "\n\n{0} da copiare ci sono già sull'iPhone nello stesso album, acquistati o scaricati sul telefono: un computer non li può togliere, resteranno due copie.":
        '\n\n{0} to copy are already on the iPhone in the same album, bought or downloaded on the phone: a computer cannot remove them, there will be two copies.',
    'anno':
        'year',
    'numero':
        'number',
    '{0} ~{1} kbit/s':
        '{0} ~{1} kbit/s',
    "senza file sull'iPhone":
        'no file on the iPhone',
    "titolo uguale a quello di altre canzoni dell'album":
        'same title as other songs of the album',
    'tag diversi dal file del PC':
        'tags different from the PC file',
    "nell'album sbagliato":
        'in the wrong album',
    "aggiunte tra graffe nel nome dell'album":
        'additions in braces in the album name',
    'senza ':
        'without ',
    'album senza immagine':
        'album without artwork',
    'tag uguali al file del PC':
        'tags equal to the PC file',
    'in {0} playlist':
        'in {0} playlists',
    'Da tenere: ':
        'To keep: ',
    'tag sbagliati (':
        'wrong tags (',
    'qualità più bassa ({0} contro {1})':
        'lower quality ({0} versus {1})',
    'tag meno completi (':
        'less complete tags (',
    "l'altra copia ha i tag uguali al file del PC":
        'the other copy has the same tags as the PC file',
    "l'altra copia è in più playlist":
        'the other copy is in more playlists',
    "l'altra copia è stata messa da un computer":
        'the other copy was put there by a computer',
    'stessa qualità, file più grande ({0} MB contro {1} MB)':
        'same quality, larger file ({0} MB versus {1} MB)',
    'a parità di tutto si preferisce {0} al FLAC':
        'everything else being equal, {0} is preferred to FLAC',
    'copia equivalente, se ne tiene una':
        'equivalent copy, one is kept',
    '; acquistata o scaricata sul telefono: un computer non la può togliere':
        '; bought or downloaded on the phone: a computer cannot remove it',
    'Da togliere: ':
        'To remove: ',
    "formato non supportato":
        "unsupported format",
    "percorso troppo lungo":
        "path too long",
    "numero o artista nel titolo":
        "number or artist in the title",
    "spazi in più":
        "extra spaces",
    "lettere accentate rovinate":
        "garbled accented letters",
    "nome scritto con maiuscole o accenti diversi":
        "name written with different capitals or accents",
    "nome dell'album diverso tra i brani":
        "album name different between tracks",
    "artista dell'album diverso tra i brani":
        "album artist different between tracks",
    "artista dell'album da completare":
        "album artist to fill in",
    "spunta Compilation":
        "Compilation flag",
    "album che l'iPhone unisce":
        "albums the iPhone merges",
    "stesso numero di traccia, titoli diversi":
        "same track number, different titles",
    "numeri di traccia o di disco sbagliati":
        "wrong track or disc numbers",
    "totali diversi tra i brani":
        "totals different between tracks",
    "• {0}, {1}: {2} → vale «{3}»":
        "• {0}, {1}: {2} → «{3}» wins",
    "Due correzioni scelte vogliono valori diversi nello stesso campo:\n{0}\nSe vuoi l'altro valore: Annulla, togli la casella della riga che non vuoi (nei risultati) e premi di nuovo Applica le correzioni scelte.":
        "Two chosen fixes want different values in the same field:\n{0}\nIf you want the other value: Cancel, clear the box of the row you do not want (in the results) and press Apply the chosen fixes again.",
    "Album con pochi brani o numeri sbagliati":
        "Albums with few tracks or wrong numbers",
    "Album divisi o incoerenti":
        "Split or inconsistent albums",
    "Tag mancanti o scritti male":
        "Missing or badly written tags",
    "Formati non supportati":
        "Unsupported formats",
    "Nomi scritti in modi diversi":
        "Names written in different ways",
    "Artisti Vari":
        "Various Artists",
    "File: vecchi tag e formati":
        "Files: old tags and formats",
    "MP3 con un vecchio tag ID3v1 diverso o un tag APE; file che non sono MP3, FLAC o M4A; sull'iPhone, brani con tag diversi da quelli del PC":
        "MP3s with a different old ID3v1 tag or an APE tag; files that are not MP3, FLAC or M4A; on the iPhone, tracks with tags different from the PC",
    "numeri di traccia mancanti, meno brani del totale dichiarato, album di 1-2 brani, numeri di disco mancanti, totali diversi tra i brani":
        "missing track numbers, fewer tracks than the declared total, albums of 1-2 tracks, missing disc numbers, totals different between tracks",
    "una cartella con album diversi, lo stesso album scritto in modi diversi o con \"CD 1\" nel nome, artista dell'album diverso o mancante, spunta Compilation, album che l'iPhone unirebbe":
        "a folder with different albums, the same album written in different ways or with \"CD 1\" in the name, album artist different or missing, Compilation flag, albums the iPhone would merge",
    "lo stesso artista con maiuscole, accenti o spazi diversi (\"Queen\" e \"queen\"), \"The Beatles\" e \"Beatles\", \"AC/DC\" e \"ACDC\": una grafia sola in tutta la musica":
        "the same artist with different capitals, accents or spaces (\"Queen\" and \"queen\"), \"The Beatles\" and \"Beatles\", \"AC/DC\" and \"ACDC\": one spelling in all the music",
    "brani senza titolo, album o artista o con un segnaposto (\"Unknown Artist\", \"Track 01\"), numero o artista nel titolo, spazi in più, lettere accentate rovinate":
        "tracks without title, album or artist or with a placeholder (\"Unknown Artist\", \"Track 01\"), number or artist in the title, extra spaces, garbled accented letters",
    "file danneggiati, bloccati, disponibili solo online o con il percorso troppo lungo":
        "damaged, locked or online-only files, or with a path that is too long",
    "Titolo, album o artista mancano o sono un segnaposto (\"Unknown Artist\", \"Album sconosciuto\", \"Track 01\"): sull'iPhone i brani finiscono in \"Album sconosciuto\" / \"Artista sconosciuto\" e la collezione appare divisa.":
        "Title, album or artist are missing or are a placeholder (\"Unknown Artist\", \"Album sconosciuto\", \"Track 01\"): on the iPhone the tracks end up in \"Unknown album\" / \"Unknown artist\" and the collection looks split.",
    ". Di solito l'\"Artista album\" manca o è scritto in modo diverso: per una compilation va messo \"{0}\" su tutti i brani. Un \"CD 1\"/\"Disc 2\" nel nome passa nel campo N. disco.":
        ". Usually the \"Album artist\" is missing or written differently: for a compilation put \"{0}\" on all the tracks. A \"CD 1\"/\"Disc 2\" in the name goes into the Disc no. field.",
    "Lo stesso album compare come: {0}. La punteggiatura o un \"CD 1\"/\"Disc 2\" nel nome lo dividono; il numero del disco va nel campo N. disco.":
        "The same album appears as: {0}. Punctuation or a \"CD 1\"/\"Disc 2\" in the name splits it; the disc number goes into the Disc no. field.",
    "Le varianti dividono la collezione dell'artista negli elenchi e sull'iPhone. Vince la grafia con le iniziali maiuscole, la più usata.":
        "The variants split the artist's collection in the lists and on the iPhone. The spelling with capital initials wins, the most used.",
    "Le varianti dividono la collezione dell'artista negli elenchi e sull'iPhone ({0}). Vince la grafia con le iniziali maiuscole, la più usata.":
        "The variants split the artist's collection in the lists and on the iPhone ({0}). The spelling with capital initials wins, the most used.",
    "Applica la correzione (se c'è) ricava i tag dai nomi di file e cartelle: controlla la colonna Diventa. Altrimenti Mostra i brani, poi Cambia i tag (tasto E) e scrivi titolo, album e artista al posto di quelli vuoti o segnaposto (\"Unknown Artist\", \"Track 01\").":
        "Apply the fix (if there is one) takes the tags from the names of files and folders: check the Becomes column. Otherwise Show the tracks, then Change the tags (E key) and write title, album and artist instead of the empty or placeholder ones (\"Unknown Artist\", \"Track 01\").",
    "Se è un singolo, o vuoi solo questi brani: tasto destro sull'album → Va bene così, e non sarà più segnalato. Se sono brani di un album più grande finiti a parte, Mostra i brani e con Cambia i tag (tasto E) scrivi album e artista dell'album uguali a quelli degli altri brani; per sapere com'è l'album intero: tasto destro → Controlla online.":
        "If it is a single, or you want only these tracks: right click on the album → Fine as it is, and it will not be reported again. If they are tracks of a bigger album that ended up apart, Show the tracks and with Change the tags (E key) write album and album artist equal to those of the other tracks; to know the whole album: right click → Check online.",
    "Se è una compilation: Applica la correzione (se c'è), oppure Mostra i brani e Cambia i tag (tasto E) con artista dell'album \"{0}\" su tutti. Se sono album diversi che si chiamano allo stesso modo: tasto destro sull'album → Va bene così.":
        "If it is a compilation: Apply the fix (if there is one), or Show the tracks and Change the tags (E key) with album artist \"{0}\" on all. If they are different albums with the same name: right click on the album → Fine as it is.",
    "Applica la correzione scrive ovunque la grafia scelta (anche negli album fuori dalla selezione: compaiono nei risultati). Per sceglierne un'altra: Mostra i brani, Cambia i tag (tasto E) e scrivila su tutti, poi Controlla di nuovo questi album.":
        "Apply the fix writes the chosen spelling everywhere (also in albums outside the selection: they appear in the results). To choose another one: Show the tracks, Change the tags (E key) and write it on all, then Check these albums again.",
    "Converti questi file in MP3 (320 kbps) o in FLAC con un programma di conversione (per esempio foobar2000 o fre:ac), controllando che copi anche i tag. Metti i file convertiti nella stessa cartella, sposta gli originali fuori dalle cartelle della musica con Esplora file (il programma non cancella i file del PC) e premi Rileggi (F5). Se non ti servono sull'iPhone: tasto destro sull'album → Va bene così.":
        "Convert these files to MP3 (320 kbps) or FLAC with a conversion program (for example foobar2000 or fre:ac), making sure it copies the tags too. Put the converted files in the same folder, move the originals out of the music folders with File Explorer (the program does not delete PC files) and press Reload (F5). If you do not need them on the iPhone: right click on the album → Fine as it is.",
    "Accorcia il percorso: in Esplora file rinomina con un nome più corto la cartella dell'artista o dell'album (o spostala più vicino alla cartella della musica), poi premi Rileggi (F5). Per arrivare alla cartella: tasto destro sul problema → Apri la cartella in Esplora risorse.":
        "Shorten the path: in File Explorer rename the artist or album folder with a shorter name (or move it closer to the music folder), then press Reload (F5). To reach the folder: right click on the problem → Open the folder in File Explorer.",
    "Applica la correzione lascia nel titolo solo il titolo. Se il numero o il nome fa parte del titolo vero (per esempio \"1999 - …\"), togli la casella di quella riga prima di applicare.":
        "Apply the fix leaves only the title in the title. If the number or the name is part of the real title (for example \"1999 - …\"), clear the box of that row before applying.",
    "Applica la correzione: cambiano solo gli spazi in più, nessun rischio.":
        "Apply the fix: only the extra spaces change, no risk.",
    "Con la correzione (lettere rovinate come \"Ã©\"): controlla la colonna Diventa e Applica. Con il carattere \"�\" la lettera è persa: Mostra i brani, Cambia i tag (tasto E) e riscrivi a mano titolo, artista o album; oppure tasto destro sull'album → Controlla online, per prendere i tag dal catalogo.":
        "With the fix (garbled letters like \"Ã©\"): check the Becomes column and Apply. With the character \"�\" the letter is lost: Show the tracks, Change the tags (E key) and rewrite title, artist or album by hand; or right click on the album → Check online, to take the tags from the catalog.",
    "Applica la correzione scrive ovunque la grafia scelta (anche negli album fuori dalla selezione: compaiono nei risultati). Con \"Accenti diversi\" controlla prima quale accento è giusto. Per un'altra grafia: Mostra i brani, Cambia i tag (tasto E) e scrivila su tutti, poi Controlla di nuovo questi album.":
        "Apply the fix writes the chosen spelling everywhere (also in albums outside the selection: they appear in the results). With \"Different accents\" first check which accent is right. For another spelling: Show the tracks, Change the tags (E key) and write it on all, then Check these albums again.",
    "Applica la correzione scrive il nome più usato su tutti i brani dell'album. Per un'altra grafia: Mostra i brani, Cambia i tag (tasto E) e scrivi il nome dell'album su tutti i brani.":
        "Apply the fix writes the most used name on all the tracks of the album. For another spelling: Show the tracks, Change the tags (E key) and write the album name on all the tracks.",
    "Applica la correzione scrive lo stesso artista dell'album su tutti i brani. Per un'altra grafia: Mostra i brani, seleziona tutti i brani dell'album e in Cambia i tag (tasto E) scrivi l'artista dell'album.":
        "Apply the fix writes the same album artist on all the tracks. For another spelling: Show the tracks, select all the tracks of the album and in Change the tags (E key) write the album artist.",
    "Applica la correzione. Se è davvero una compilation di un solo artista: tasto destro sull'album → Va bene così.":
        "Apply the fix. If it really is a compilation of a single artist: right click on the album → Fine as it is.",
    "Applica la correzione. Se l'album è davvero una compilation ma la correzione spegne la spunta, scrivi \"{0}\" come artista dell'album (Mostra i brani, Cambia i tag, tasto E) e Controlla di nuovo questi album.":
        "Apply the fix. If the album really is a compilation but the fix clears the flag, write \"{0}\" as album artist (Show the tracks, Change the tags, E key) and Check these albums again.",
    "Se sono lo stesso album: Applica la correzione. Se sono album diversi: non applicare; Mostra i brani, Cambia i tag (tasto E) e dai a uno dei due un nome che resti diverso anche senza gli zeri (per esempio con l'anno: \"Raccolta 1 (1998)\").":
        "If they are the same album: Apply the fix. If they are different albums: do not apply; Show the tracks, Change the tags (E key) and give one of the two a name that stays different even without the zeros (for example with the year: \"Raccolta 1 (1998)\").",
    "Mostra i brani e guarda le cartelle. Se sono due album diversi con lo stesso nome (due \"Greatest Hits\", due edizioni), dai a uno dei due un nome diverso con Cambia i tag (tasto E), per esempio con l'anno o l'edizione: \"Greatest Hits (1981)\". Se è lo stesso album con i numeri sbagliati, correggi N. traccia (e N. disco) dei brani sbagliati. Poi Controlla di nuovo questi album.":
        "Show the tracks and look at the folders. If they are two different albums with the same name (two \"Greatest Hits\", two editions), give one of them a different name with Change the tags (E key), for example with the year or the edition: \"Greatest Hits (1981)\". If it is the same album with wrong numbers, correct Track no. (and Disc no.) of the wrong tracks. Then Check these albums again.",
    "Mostra i brani e correggi con Cambia i tag (tasto E): il N. disco dei brani che non l'hanno (lo dicono di solito la cartella o il nome del file, \"CD2\"), oppure il numero o il totale sbagliato. I numeri giusti dell'edizione: tasto destro sull'album → Controlla online.":
        "Show the tracks and correct with Change the tags (E key): the Disc no. of the tracks that lack it (usually the folder or the file name says it, \"CD2\"), or the wrong number or total. The right numbers of the edition: right click on the album → Check online.",
    "Applica la correzione scrive su tutti i brani il totale più frequente. Se è sbagliato proprio quello: Mostra i brani e scrivi il totale giusto con Cambia i tag (tasto E) su tutti.":
        "Apply the fix writes the most frequent total on all the tracks. If that very one is wrong: Show the tracks and write the right total with Change the tags (E key) on all.",
    "Converti i file in MP3 o FLAC con un programma di conversione, poi Rileggi (F5).":
        "Convert the files to MP3 or FLAC with a conversion program, then Reload (F5).",
    "Applica la correzione (se c'è); altrimenti Mostra i brani e scrivi lo stesso nome su tutti con Cambia i tag (tasto E).":
        "Apply the fix (if there is one); otherwise Show the tracks and write the same name on all with Change the tags (E key).",
    "{0} in un formato non supportato ({1})":
        "{0} in an unsupported format ({1})",
    "Il programma lavora con MP3, FLAC e M4A. Gli altri formati non si inviano all'iPhone come si deve: l'app Musica non suona OGG, Opus e WMA, e in WAV e AIFF i tag (titolo, artista, album) non arrivano.":
        "The program works with MP3, FLAC and M4A. The other formats do not go to the iPhone properly: the Music app does not play OGG, Opus and WMA, and in WAV and AIFF the tags (title, artist, album) do not arrive.",
    "{0} con il percorso troppo lungo":
        "{0} with a path that is too long",
    "Il percorso completo (cartelle + nome del file) supera i {0} caratteri, il limite di Windows: molti programmi non aprono questi file, e copiarli o inviarli può non riuscire.":
        "The full path (folders + file name) is over {0} characters, the Windows limit: many programs do not open these files, and copying or sending them may fail.",
    "{0} con il percorso vicino al limite":
        "{0} with a path close to the limit",
    "Il percorso completo supera i {0} caratteri: un nome di cartella un po' più lungo lo porta oltre il limite di Windows ({1}).":
        "The full path is over {0} characters: a slightly longer folder name takes it over the Windows limit ({1}).",
    "{0} con il numero o l'artista nel titolo":
        "{0} with the number or the artist in the title",
    "Il titolo comincia con il numero di traccia (\"05 - Titolo\") o con il nome dell'artista (\"Artista - Titolo\"): sull'iPhone si vede due volte. La correzione lascia solo il titolo.":
        "The title starts with the track number (\"05 - Title\") or with the artist's name (\"Artist - Title\"): on the iPhone it shows twice. The fix leaves only the title.",
    "Togli numero e artista dal titolo":
        "Remove number and artist from the title",
    "{0} con spazi in più nei tag":
        "{0} with extra spaces in the tags",
    "Titolo, artista, artista dell'album o album hanno spazi all'inizio, alla fine o doppi (o una lettera accentata salvata in un modo diverso dal solito, che a schermo non si vede). Il programma li considera uguali agli altri, ma l'iPhone tiene la grafia del primo brano che riceve: meglio che sia pulita.":
        "Title, artist, album artist or album have spaces at the start, at the end or doubled (or an accented letter stored in an unusual way, invisible on screen). The program considers them equal to the others, but the iPhone keeps the spelling of the first track it receives: better if it is clean.",
    "Togli gli spazi in più":
        "Remove the extra spaces",
    "{0} con lettere accentate rovinate":
        "{0} with garbled accented letters",
    "Testi come \"PerchÃ©\" invece di \"Perché\": il tag è stato scritto con una codifica e letto con un'altra. Sull'iPhone diventano un artista o un album in più. La correzione rimette le lettere giuste.":
        "Texts like \"PerchÃ©\" instead of \"Perché\": the tag was written with one encoding and read with another. On the iPhone they become one more artist or album. The fix puts back the right letters.",
    "Rimetti le lettere accentate":
        "Put back the accented letters",
    "{0} con il carattere \"{1}\" nei tag":
        "{0} with the character \"{1}\" in the tags",
    "Al posto di qualche lettera (di solito accentata) c'è \"{0}\": la lettera giusta è persa e il programma non la può indovinare.":
        "Instead of some letter (usually accented) there is \"{0}\": the right letter is lost and the program cannot guess it.",
    "Lo stesso nome compare come {0}. Il programma li mostra insieme, ma l'iPhone tiene la grafia del primo brano che riceve e non la cambia più: meglio una grafia sola. Vince quella con le iniziali maiuscole, la più usata.":
        "The same name appears as {0}. The program shows them together, but the iPhone keeps the spelling of the first track it receives and never changes it: better a single spelling. The one with capital initials wins, the most used.",
    "\"{0}\" scritto anche come {1}":
        "\"{0}\" also written as {1}",
    "Accenti diversi: {0}":
        "Different accents: {0}",
    " Attenzione: le grafie hanno accenti diversi e il programma non sa quale è giusto: ha scelto \"{0}\". Controlla prima di applicare.":
        " Warning: the spellings have different accents and the program does not know which is right: it chose \"{0}\". Check before applying.",
    "{0}: il nome dell'album scritto anche come {1}":
        "{0}: the album name also written as {1}",
    "I brani dello stesso album hanno il nome scritto con maiuscole, accenti o spazi diversi. L'iPhone tiene la grafia del primo brano che riceve: meglio una sola. Vince la più usata nell'album.":
        "The tracks of the same album have the name written with different capitals, accents or spaces. The iPhone keeps the spelling of the first track it receives: better a single one. The most used in the album wins.",
    "Album \"{0}\" su tutti i brani":
        "Album \"{0}\" on all the tracks",
    "scritto in modi diversi: ":
        "written in different ways: ",
    "vuoto su {0}":
        "empty on {0}",
    "{0}: artista dell'album {1}":
        "{0}: album artist {1}",
    "L'artista dell'album deve essere identico su tutti i brani dell'album, anche nelle maiuscole: con grafie diverse (per esempio \"AA.VV.\" e \"Artisti Vari\") l'iPhone divide l'album in due. Vince la grafia con le iniziali maiuscole; i brani senza artista dell'album lo ricevono.":
        "The album artist must be identical on all the tracks of the album, capitals included: with different spellings (for example \"AA.VV.\" and \"Artisti Vari\") the iPhone splits the album in two. The spelling with capital initials wins; the tracks without album artist get it.",
    "Artista dell'album \"{0}\" su tutti i brani":
        "Album artist \"{0}\" on all the tracks",
    "{0}: \"artisti vari\" ma i brani sono tutti di {1}":
        "{0}: \"various artists\" but the tracks are all by {1}",
    "L'artista dell'album dice che è una compilation, ma tutti i brani sono dello stesso artista: sull'iPhone l'album finisce tra le compilation invece che sotto l'artista. La correzione mette \"{0}\" come artista dell'album e toglie la spunta Compilation.":
        "The album artist says it is a compilation, but all the tracks are by the same artist: on the iPhone the album ends up among the compilations instead of under the artist. The fix sets \"{0}\" as album artist and clears the Compilation flag.",
    "{0}: senza artista dell'album":
        "{0}: without album artist",
    "Nessun brano ha l'artista dell'album e sono tutti dello stesso artista: la correzione lo scrive anche come artista dell'album, così l'album resta intero anche se un brano un giorno avrà un ospite.":
        "No track has the album artist and they are all by the same artist: the fix writes it as album artist too, so the album stays whole even if one day a track has a guest.",
    "Artista dell'album \"{0}\"":
        "Album artist \"{0}\"",
    "l'artista dell'album è \"{0}\": è una compilation":
        "the album artist is \"{0}\": it is a compilation",
    "i brani sono tutti dello stesso artista: non è una compilation":
        "the tracks are all by the same artist: it is not a compilation",
    "vale quello che ha la maggior parte dei brani":
        "the value of most tracks wins",
    "{0}: la spunta Compilation c'è su {1} brani su {2}":
        "{0}: the Compilation flag is on {1} tracks out of {2}",
    "{0}: manca la spunta Compilation":
        "{0}: the Compilation flag is missing",
    "{0}: spunta Compilation su un album di un solo artista":
        "{0}: Compilation flag on an album by a single artist",
    "La correzione la accende su tutti i brani ({0}).":
        "The fix turns it on on all the tracks ({0}).",
    "Compilation accesa su tutti i brani":
        "Compilation on on all the tracks",
    "La correzione la spegne su tutti i brani ({0}).":
        "The fix turns it off on all the tracks ({0}).",
    "Compilation spenta su tutti i brani":
        "Compilation off on all the tracks",
    "Sull'iPhone la spunta Compilation decide se l'album sta tra le compilation; diversa tra i brani, l'album può dividersi. {0}":
        "On the iPhone the Compilation flag decides whether the album is among the compilations; different between the tracks, the album can split. {0}",
    "\"{0}\": {1} album che sull'iPhone diventano uno":
        "\"{0}\": {1} albums that become one on the iPhone",
    "Sul PC sono album diversi ({0}), ma l'iPhone non conta gli zeri davanti ai numeri (\"01\" = \"1\") e li mette in un album solo, con il nome arrivato per primo. Se sono lo stesso album, la correzione scrive \"{1}\" su tutti.":
        "On the PC they are different albums ({0}), but the iPhone ignores leading zeros in numbers (\"01\" = \"1\") and puts them in a single album, with the name that arrived first. If they are the same album, the fix writes \"{1}\" on all.",
    "{0}: numeri di traccia o di disco sbagliati":
        "{0}: wrong track or disc numbers",
    "{0}: totale delle tracce o dei dischi diverso tra i brani":
        "{0}: total of tracks or discs different between tracks",
    "Il totale delle tracce (o il numero di dischi) cambia da un brano all'altro dello stesso disco: la correzione scrive su tutti il valore più frequente.":
        "The total of tracks (or the number of discs) changes from one track to another of the same disc: the fix writes the most frequent value on all.",
    "Lo stesso totale su tutti i brani":
        "The same total on all the tracks",
    "L'album ha più dischi, ma {0} non ha il numero del disco: sull'iPhone finiscono nel disco 1, mescolati.":
        "The album has several discs, but {0} has no disc number: on the iPhone they end up in disc 1, mixed.",
    "{0} (traccia {1} di {2})":
        "{0} (track {1} of {2})",
    "{0} (disco {1} di {2})":
        "{0} (disc {1} of {2})",
    "Numero più alto del totale: {0}.":
        "Number higher than the total: {0}.",
    " I brani sono in {0} cartelle: è probabile che siano due album con lo stesso nome.":
        " The tracks are in {0} folders: probably they are two albums with the same name.",
    "{0}: {1} numeri di traccia usati da brani diversi":
        "{0}: {1} track numbers used by different tracks",
    "Nello stesso album lo stesso numero di traccia (e disco) ha titoli diversi: {0}.{1} Sull'iPhone diventano un album solo con i brani mescolati.":
        "In the same album the same track (and disc) number has different titles: {0}.{1} On the iPhone they become a single album with the tracks mixed.",
    "Per applicarle connetti l'iPhone (e aspetta la fine dell'operazione in corso).":
        "To apply them connect the iPhone (and wait for the end of the running operation).",
    "Non c'è niente da applicare: le azioni sono state tolte tutte.":
        "There is nothing to apply: all the actions have been removed.",
    "Applica è spento. {0}":
        "Apply is off. {0}",
    "<b><u style='background-color: rgba(255, 210, 0, 90)'>{0}</u></b>":
        "<b><u style='background-color: rgba(255, 210, 0, 90)'>{0}</u></b>",
    "<span style='color: {0}; white-space: pre'>{1}</span>":
        "<span style='color: {0}; white-space: pre'>{1}</span>",
    "Aspetta la fine di \"{0}\" (barra di stato, in basso): il pulsante si accende da solo.":
        "Wait for the end of \"{0}\" (status bar, at the bottom): the button turns on by itself.",
    "Connetti l'iPhone (scheda iPhone, pulsante Connetti iPhone): il pulsante si accende da solo.":
        "Connect the iPhone (iPhone tab, Connect iPhone button): the button turns on by itself.",
    "TagScanner non trovato. Se l'hai installato in un posto diverso dal solito, scegli il file Tagscan.exe in Impostazioni → Generale → TagScanner.":
        "TagScanner not found. If you installed it somewhere unusual, choose the Tagscan.exe file in Settings → General → TagScanner.",
    "TagScanner aperto su {0}: quando hai finito di cambiare i tag, premi Rileggi (F5)":
        "TagScanner opened on {0}: when you have finished changing the tags, press Reload (F5)",
    "La cartella non c'è su questo PC (disco scollegato o file spostati)":
        "The folder is not on this PC (disconnected disk or moved files)",
    "Apri in TagScanner (non trovato: Impostazioni → Generale)":
        "Open in TagScanner (not found: Settings → General)",
    "Apri in TagScanner":
        "Open in TagScanner",
    "Apre TagScanner sulla cartella {0}. TagScanner cambia i file direttamente, fuori da questo programma: quando hai finito, Rileggi (F5) mostra i tag nuovi.":
        "Opens TagScanner on the folder {0}. TagScanner changes the files directly, outside this program: when you have finished, Reload (F5) shows the new tags.",
    "vuoto: cercato in Programmi":
        "empty: searched in Program Files",
    "Il file Tagscan.exe, o la cartella che lo contiene. Vuoto: si cerca in Programmi (cartella TagScanner). Serve per Apri in TagScanner, nel tasto destro su brani e album.":
        "The Tagscan.exe file, or the folder that contains it. Empty: it is searched in Program Files (TagScanner folder). Used by Open in TagScanner, in the right click on tracks and albums.",
    "TagScanner":
        "TagScanner",
    "TagScanner (Tagscan.exe);;Programmi (*.exe)":
        "TagScanner (Tagscan.exe);;Programs (*.exe)",
    "✖ non trovato: scegli il file Tagscan.exe":
        "✖ not found: choose the Tagscan.exe file",
    "✖ TagScanner non è in Programmi: installalo o scegli il file Tagscan.exe":
        "✖ TagScanner is not in Program Files: install it or choose the Tagscan.exe file",
    "Se c'è la correzione (numeri presi dai nomi dei file): controlla la colonna Diventa e Applica. Altrimenti Mostra i brani e guarda le cartelle. Se sono due album diversi con lo stesso nome (due \"Greatest Hits\", due edizioni), dai a uno dei due un nome diverso con Cambia i tag (tasto E), per esempio con l'anno o l'edizione: \"Greatest Hits (1981)\". Se è lo stesso album con i numeri sbagliati, correggi N. traccia (e N. disco) dei brani sbagliati. Poi Controlla di nuovo questi album.":
        "If there is the fix (numbers taken from the file names): check the Becomes column and Apply. Otherwise Show the tracks and look at the folders. If they are two different albums with the same name (two \"Greatest Hits\", two editions), give one of them a different name with Change the tags (E key), for example with the year or the edition: \"Greatest Hits (1981)\". If it is the same album with wrong numbers, correct Track no. (and Disc no.) of the wrong tracks. Then Check these albums again.",
    "Nello stesso album lo stesso numero di traccia (e disco) ha titoli diversi: {0}.{1} Sull'iPhone l'album ha i brani mescolati, e i brani che mancano non si possono contare.":
        "In the same album the same track (and disc) number has different titles: {0}.{1} On the iPhone the album has the tracks mixed, and the missing tracks cannot be counted.",
    " I nomi dei file hanno invece un numero diverso per ogni brano (\"05 - …\"): la correzione scrive quello come numero di traccia.":
        " The file names instead have a different number for each track (\"05 - …\"): the fix writes that as the track number.",
    "Numero di traccia dal nome del file":
        "Track number from the file name",
    "<br><span style='color: gray'>{0} album non trovati nei cataloghi online: non sono problemi, l'elenco è nel rapporto (Apri il rapporto).</span>":
        "<br><span style='color: gray'>{0} albums not found in the online catalogs: they are not problems, the list is in the report (Open the report).</span>",
    "Verifica online: {0} album non trovati nei cataloghi (non sono problemi)":
        "Online check: {0} albums not found in the catalogs (they are not problems)",
    "copia dell'album in qualità peggiore":
        "lower-quality copy of the album",
    "album presente due volte":
        "album present twice",
    "Sposta nel cestino questa copia ({0} file)…":
        "Move this copy to the recycle bin ({0} files)…",
    "Sposta nel cestino la copia in {0} ({1} file)…":
        "Move the copy in {0} to the recycle bin ({1} files)…",
    "Mostra l'elenco dei file e chiede conferma; si recuperano dal Cestino di Windows":
        "Shows the list of files and asks for confirmation; they can be recovered from the Windows Recycle Bin",
    "I file non ci sono più su questo PC.":
        "The files are no longer on this PC.",
    "Spostare nel Cestino di Windows {0} file di questa copia dell'album?":
        "Move {0} files of this copy of the album to the Windows Recycle Bin?",
    "\n\nSi recuperano dal Cestino. Sull'iPhone non cambia niente.":
        "\n\nThey can be recovered from the Recycle Bin. Nothing changes on the iPhone.",
    "{0} file nel Cestino. Rileggo la cartella: poi Controlla di nuovo questi album per aggiornare i risultati.":
        "{0} files in the Recycle Bin. Reloading the folder: then Check these albums again to update the results.",
    "L'album compare come: {0}. Senza artista dell'album, sull'iPhone ogni cantante forma un album a parte: la correzione mette \"{1}\" e la spunta Compilation. Con la Verifica online, se il catalogo trova l'album di un artista preciso, questo problema sparisce e la correzione online propone quell'artista.":
        "The album appears as: {0}. Without album artist, on the iPhone each singer forms a separate album: the fix sets \"{1}\" and the Compilation flag. With the online check, if the catalog finds the album of a specific artist, this problem disappears and the online fix proposes that artist.",
    "Se non ti servono i brani che ci sono solo in questa copia (il dettaglio li nomina): tasto destro sul problema → Sposta nel cestino questa copia, controlla l'elenco dei file e conferma (si recuperano dal Cestino di Windows). Oppure spostala a mano fuori dalle cartelle della musica con Esplora file. Se la vuoi tenere: tasto destro sull'album → Va bene così.":
        "If you do not need the tracks that are only in this copy (the detail names them): right click on the problem → Move this copy to the recycle bin, check the list of files and confirm (they can be recovered from the Windows Recycle Bin). Or move it by hand out of the music folders with File Explorer. If you want to keep it: right click on the album → Fine as it is.",
    "Tasto destro sul problema → Sposta nel cestino la copia in … (scegli quale togliere), controlla l'elenco dei file e conferma (si recuperano dal Cestino di Windows). Se le vuoi tenere tutte e due: tasto destro sull'album → Va bene così.":
        "Right click on the problem → Move the copy in … to the recycle bin (choose which one to remove), check the list of files and confirm (they can be recovered from the Windows Recycle Bin). If you want to keep both: right click on the album → Fine as it is.",
    "MP3 {0} kbps":
        "MP3 {0} kbps",
    "Dell'album ci sono due copie: questa ({0}, in {1}) e una migliore ({2}, in {3}). Questa è un doppione: sull'iPhone basta la migliore.":
        "There are two copies of the album: this one ({0}, in {1}) and a better one ({2}, in {3}). This one is a duplicate: on the iPhone the better one is enough.",
    " Attenzione: {0} ci sono solo in questa copia ({1}{2}): togliendola li perdi.":
        " Warning: {0} are only in this copy ({1}{2}): removing it you lose them.",
    "{0}: copia in {1}, c'è anche in {2}":
        "{0}: copy in {1}, also available in {2}",
    "{0}: l'album c'è due volte ({1})":
        "{0}: the album is there twice ({1})",
    "Due copie con la stessa qualità: in {0} e in {1}. Ne basta una.":
        "Two copies with the same quality: in {0} and in {1}. One is enough.",
    " Le cartelle e gli anni sono diversi: forse sono album diversi con lo stesso nome.":
        " The folders and the years are different: maybe they are different albums with the same name.",
    " Non verificato online: se non hai fatto la Verifica online, tasto destro → Controlla online per esserne sicuro.":
        " Not checked online: if you did not run the online check, right click → Check online to be sure.",
    "numero più alto del totale":
        "number higher than the total",
    " e {0} informazioni (in grigio: album incompleti, dettagli che sull'iPhone non cambiano niente; le loro correzioni partono spente)":
        " and {0} pieces of information (in grey: incomplete albums, details that change nothing on the iPhone; their fixes start off)",
    "{0} informazioni":
        "{0} pieces of information",
    "Informazione: sull'iPhone non crea confusione. La correzione, se c'è, parte spenta: accendila se vuoi":
        "Information: it causes no confusion on the iPhone. The fix, if there is one, starts off: turn it on if you want",
    "informazione":
        "information",
    "Niente di urgente: sull'iPhone non cambia niente. Per correggere: Mostra i brani e scrivi il numero o il totale giusto con Cambia i tag (tasto E).":
        "Nothing urgent: nothing changes on the iPhone. To correct it: Show the tracks and write the right number or total with Change the tags (E key).",
    "{0}: brani senza numero del disco":
        "{0}: tracks without disc number",
    "{0}: numero più alto del totale":
        "{0}: number higher than the total",
    "Numero più alto del totale: {0}. Sull'iPhone si vede solo \"traccia 9 di 8\".":
        "Number higher than the total: {0}. On the iPhone you only see \"track 9 of 8\".",
    "{0}: {1} sull'iPhone con tag diversi da quelli del PC":
        "{0}: {1} on the iPhone with tags different from the PC",
    "Il brano è nell'app Musica dell'iPhone, ma titolo, artista, album, anno, genere o numeri non sono quelli del PC (per esempio dopo una modifica sul PC, anche con le correzioni dei Controlli). Nella scheda PC, la colonna iPhone mostra le differenze.":
        "The track is in the iPhone Music app, but title, artist, album, year, genre or numbers are not those of the PC (for example after a change on the PC, also with the fixes of the Checks). In the PC tab, the iPhone column shows the differences.",
    "Solo un'informazione: sull'iPhone non crea confusione. Se vuoi, Cosa fare dice come sistemarla":
        "Only information: it causes no confusion on the iPhone. If you want, What to do says how to fix it",
    "{0} — {1}: {2} sull'iPhone con tag diversi da quelli del PC":
        "{0} — {1}: {2} on the iPhone with tags different from the PC",
    "(Tutte le compilation: {0})":
        "(All the compilations: {0})",
    "Gli album con la spunta Compilation o con \"artisti vari\" come artista dell'album":
        "The albums with the Compilation flag or with \"various artists\" as album artist",
    "(Tutti gli album delle compilation":
        "(All the albums of the compilations",
    "associati {0} file ritrovati":
        "linked {0} found files",
    "{0} brani ora senza sorgente":
        "{0} tracks now without source",
    "Sorgenti sparite: ":
        "Missing sources: ",
    "<b>{0}</b> brani dell'iPhone, in <b>{1}</b> album, vengono da file di questo PC che non ci sono più (spostati o cancellati). Per <b>{2}</b> album c'è nella libreria lo stesso album (stesso artista dell'album e titolo): è già scelto nella colonna <i>Cosa fare</i>. Per ogni album scegli la copia da associare, togli l'associazione, eliminalo dall'iPhone (solo se sul PC l'album non c'è più) o lascia per più tardi; poi <i>Applica le scelte</i>.<br>Se i file sono su un disco che ora non è collegato, collegalo e premi <i>Più tardi</i>.":
        "<b>{0}</b> iPhone tracks, in <b>{1}</b> albums, come from files of this PC that are no longer there (moved or deleted). For <b>{2}</b> albums the same album is in the library (same album artist and title): it is already chosen in the <i>What to do</i> column. For each album choose the copy to link, remove the link, delete it from the iPhone (only if the album is no longer on the PC) or leave it for later; then <i>Apply the choices</i>.<br>If the files are on a disk that is not connected now, connect it and press <i>Later</i>.",
    "Album sull'iPhone":
        "Album on the iPhone",
    "Cartella di prima":
        "Previous folder",
    "Cosa fare":
        "What to do",
    "Ritrovato":
        "Found",
    "Tutti: lo stesso album nella libreria":
        "All: the same album in the library",
    "Per ogni album che c'è nella libreria, la prima copia proposta; gli altri più tardi":
        "For each album that is in the library, the first proposed copy; the others later",
    "Tutti: togli l'associazione":
        "All: remove the link",
    "Restano sull'iPhone, senza sorgente sul PC":
        "They stay on the iPhone, without a source on the PC",
    "Tutti: più tardi":
        "All: later",
    "Applica le scelte":
        "Apply the choices",
    "Per tutti gli album:":
        "For all the albums:",
    "Associare scrive solo il registro della provenienza: i file non cambiano. \"Elimina dall'iPhone\" va in attesa e parte con Applica (barra blu); sul PC non cambia niente. Li ritrovi quando vuoi nella scheda iPhone con il filtro \"File del PC non trovato\".":
        "Linking writes only the provenance register: the files do not change. \"Delete from the iPhone\" goes in the queue and starts with Apply (blue bar); nothing changes on the PC. You find them whenever you want in the iPhone tab with the \"PC file not found\" filter.",
    "Associa all'album in {0} ({1} di {2} brani)":
        "Link to the album in {0} ({1} of {2} tracks)",
    "Togli l'associazione (resta sull'iPhone senza sorgente)":
        "Remove the link (stays on the iPhone without a source)",
    "Elimina dall'iPhone (in attesa)":
        "Delete from the iPhone (queued)",
    "{0} ritrovati":
        "{0} found",
    ", {0} no (restano così)":
        ", {0} not (they stay as they are)",
    "sul PC l'album non c'è più":
        "the album is no longer on the PC",
}
