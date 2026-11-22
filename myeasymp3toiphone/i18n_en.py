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
    "stesso audio (la più simile di {0} copie)":
        "same audio (the most similar of {0} copies)",
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
    "consigliato — ":
        "recommended — ",
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
    ": annullamento…":
        ": cancelling…",
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
    "l'iPhone ha un'ancora diversa da quella del suo database ({0} invece di {1}): rileggi la musica dell'iPhone e riprova":
        "the iPhone has an anchor different from its database's ({0} instead of {1}): read the iPhone music again and retry",
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
    "\"The Beatles\" e \"Beatles\", maiuscole, \"AC/DC\" e \"ACDC\"":
        "\"The Beatles\" and \"Beatles\", capitals, \"AC/DC\" and \"ACDC\"",
    "brani senza titolo, album o artista":
        "tracks without title, album or artist",
    "file danneggiati, bloccati o disponibili solo online":
        "damaged, locked or online-only files",
    "lo stesso brano in più file: stesso audio anche con tag diversi, oppure stessa durata, titolo e artista in file diversi (un MP3 e un FLAC); l'AI guarda solo le coppie sospette":
        "the same track in several files: same audio even with different tags, or same duration, title and artist in different files (an MP3 and a FLAC); the AI looks only at the suspicious pairs",
    "1 brano":
        "1 track",
    "controllo file: {0}":
        "checking files: {0}",
    " Sul PC il file resta com'è (sola lettura); le copie inviate all'iPhone ne sono ripulite automaticamente.":
        " On the PC the file stays as it is (read-only); the copies sent to the iPhone are cleaned automatically.",
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
    "{0} — {1}: {2} su almeno {3}":
        "{0} — {1}: {2} of at least {3}",
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
    "{0}: {1} in duetto":
        "{0}: {1} in duets",
    "L'app Musica non gestisce più artisti per brano: i duetti dividono la collezione dell'artista. Artista (e artista dell'album) diventano \"{0}\", gli ospiti vanno nel titolo (feat. …).\n":
        "The Music app does not handle several artists per track: duets split the artist's collection. Artist (and album artist) become \"{0}\", the guests go in the title (feat. …).\n",
    "Artista \"{0}\", ospiti nel titolo":
        "Artist \"{0}\", guests in the title",
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
    "A{0} | album artist: {1} | album: {2} | anni: {3} | brani: {4} | numeri: {5} | totale dichiarato: {6} | cartella: {7} | generi: {8}":
        "A{0} | album artist: {1} | album: {2} | anni: {3} | brani: {4} | numeri: {5} | totale dichiarato: {6} | cartella: {7} | generi: {8}",
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
}
