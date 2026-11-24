# TODO

## Le proposte dubbie di "Associa sorgenti"

Sui dati veri restano 44 proposte non spuntate (regole senza un candidato chiaro). Controllare cosa ne dice l'AI
della scansione e se i candidati sono giusti (versioni dal vivo, remaster). In attesa: l'utente non ha ancora fatto
*Associa sorgenti* con la build nuova.

## Invio di M4A in Apple Lossless (ALAC) — solo se servirà

Oggi si inviano MP3, FLAC e AAC. ALAC vuole il suo formato di inserimento (rustunes `protocol/alac.rs`: tra
l'altro `gapless_heuristic_info`, `analysis_inhibit_flags`). Per ora non serve: i 20 M4A della musica dell'utente
sono tutti AAC.

## Da provare con l'iPhone attaccato (solo brani PROVA, poi tolti)

Fatto e provato senza telefono (test e finestre di prova); da confermare sul telefono vero:
- **Compilation in Cambia tag**: `update_track` con `is_compilation` (rustunes lo accetta ma non l'ha verificato):
  il brano cambia spunta? L'album nell'app Musica si raccoglie? Se no, la finestra lo spiega già (Rimpiazza).
- **Brani fantasma**: la lettura delle cartelle F00… (`iphone._music_files`) e il brano `F05/W0084007.mp3` segnato
  *senza file* (lo elimina l'utente).
- **Applica** (passo 5): invio, eliminazione e aggiornamento in una volta, poi le spunte in attesa che spariscono.
- **Modifica dei tag dal PC** su un brano collegato: Cambia tag per titolo e album, Rimpiazza per l'artista, il
  promemoria delle playlist.
- **Playlist per artista** (`insert_playlist`, `delete_playlist`: rustunes li ha provati su un telefono, ma solo
  con playlist di 1-42 brani): prima **Prova** ("♪ PROVA", una playlist vera di decine o centinaia di brani, in
  ordine?), poi il piano completo. Controllare che le playlist di CopyTrans abbiano un `sync_id` (se risultano tutte
  "fatte sull'iPhone", il computer non le può cancellare) e il messaggio finale se Sincronizza libreria è attiva.
- **Album e artisti che l'iPhone tiene con il nome vecchio** (prove del 24/11/2026 con l'album "PROVA Raccolta 01"
  di "PROVA ARTISTA", script nella cartella temporanea della sessione):
  - l'iPhone riconosce album e artisti per nome (maiuscole e "01"/"1" non contano) e tiene la grafia che ha già;
  - togliere tutti i brani non basta: album e artista restano nel database, vuoti (nell'app non si vedono). Non
    li toglie né il riavvio, né una sessione che toglie 3 o 19 brani. `delete_album` e `delete_artist` l'iPhone
    li ignora (rustunes, docs/05);
  - reinviare con un nome scritto diversamente e un identificativo nuovo riusa la riga vuota con il nome vecchio;
    lo stesso con *Cambia tag* (`update_track` con album e `album_pid` nuovi): la riga prende il nuovo
    identificativo, il nome resta.
  - un brano scritto "PROVA Raccolta 1" di "PROVA Artista", inviato nello stesso album mentre ha ancora i suoi
    brani: il nome resta. Per album e artisti dell'album vince la prima grafia (per gli artisti dei brani rustunes
    ha visto vincere l'ultima). Un album non si rinomina sul posto: nessun comando lo fa (`update_album` è ignorato
    come `delete_album`).
  - **La pulizia si provoca**: una sessione che toglie 100 brani ha cancellato tutti gli album e gli artisti vuoti
    (anche quelli rimasti dalle sessioni prima), come in rustunes (docs/05, "Group collection in a 100-target
    session"; la regola esatta non è nota: rustunes ha visto pulire anche con 16 brani e non pulire con 90). Dopo,
    l'album reinviato come "PROVA Raccolta 1" di "PROVA Artista" ha preso il nome nuovo.
  - ***Allinea la grafia (PC → iPhone)*** è fatto (`phone_actions.align_spelling`, scheda iPhone: tasto destro
    sui brani o su artisti e album, filtro *Mostra → Album o artista scritti diversamente dal PC*) e **provato sul
    telefono** il 24/11/2026: "PROVA Raccolta 1" di "PROVA Artista" è diventato "PROVA Raccolta 01" di "PROVA
    ARTISTA" (album e artista dell'album insieme), 97 brani di servizio inviati e tolti, nessuno rimasto, 17 s in
    tutto; la sessione ha cancellato anche le altre righe vuote. L'utente ha visto il nome nuovo nell'app. Restano
    da provare dalla finestra (build nuova) e su un album vero. Sull'iPhone restano vuoti (invisibili) "PROVA
    Raccolta 01" e "PROVA ARTISTA".
- **App Musica che non si aggiorna da sola**: dopo ogni scrittura il programma manda l'avviso di fine
  sincronizzazione di iTunes (`com.apple.itunes-mobdev.syncDidFinish`, `iphone.post_sync_finished`). Con l'app
  Musica aperta: se si aggiorna da sola, togliere dal messaggio finale l'invito a chiuderla e riaprirla; se no,
  provare anche `syncWillStart` all'inizio della sessione.

## Copertine degli album (24/11/2026)

Sull'iPhone 59 album su 234 non avevano l'immagine dell'album: tutti messi da altri programmi (i brani hanno la
copertina, all'album manca la riga `best_artwork_token`); i 90 album con brani inviati da qui ce l'hanno tutti.
Due album veri rimpiazzati dal PC: l'immagine c'è, confermato nell'app. Fatto *Sistema le
copertine (PC → iPhone)*. Restano:
- 8 album senza sorgente sul PC: prima *Associa sorgenti*;
- 2 album con la copertina in scala di grigi: rustunes dice che l'iPhone ne fa una miniatura vuota; controllare
  nell'app e, se è così, convertire in colore la copertina della copia inviata;
- le copertine in un'immagine a parte nella cartella (`folder.jpg`, `cover.jpg`) non si usano ancora; sui dati veri
  nessun album senza immagine ne aveva bisogno.

## Da provare con l'AI locale (Ollama acceso)

- *Controlla la musica* → **Brani duplicati**: le 368 coppie dubbie (versioni live, remix…) sulla collezione vera;
  controllare qualche risposta.
- **Artisti scritti in modi diversi**: i 22 gruppi dubbi, con e senza MusicBrainz.
- In inglese, i motivi dell'AI devono arrivare in inglese.

## Da provare sui dati veri (le novità del 22/11/2026)

Fatto e provato con i test (risposte finte, nessuna rete tranne una prova di Deezer e Apple Music); da guardare sulla
musica vera:
- **Tutti i tipi di tag** (ID3v2 → APEv2 → ID3v1, WMA/WAV/AIFF in sola lettura): l'MP3 d'esempio che nella scheda
  PC era senza tag è stato cancellato. Trovarne un altro che TagScanner legge e il programma no, e vedere cosa dice
  *Tag letti da* nell'editor. Alla prima apertura gli MP3 della cache con un campo vuoto si rileggono.
- **Associa sorgenti** con il nome della cartella: quanti brani trova senza impronta sulla Libreria vera, e se i
  *molto probabile* sono giusti. Provare anche *Tutta la Libreria* e i brani selezionati che hanno già una sorgente.
- **Sul PC** nella scheda iPhone: ✔/⟳ per le sorgenti fuori dalla cartella aperta (quanto ci mette con migliaia di
  brani su un disco esterno), ≈ e il filtro *Da rivedere*, ✖, *Associa le probabili*.
- **Sorgenti proposte in rosso** (album intero in una cartella): quante ne trova sulla Libreria vera, se sono giuste,
  *Associa questa sorgente*. **Allinea i tag** nei due versi, con l'iPhone attaccato (solo brani PROVA).
- **Verifica album online**: Deezer e Apple Music sulla Libreria vera (album italiani: il negozio Apple è quello di
  Windows), l'ordine dei servizi, *Ferma*, la finestra dei risultati non modale. Discogs con `DISCOGS_TOKEN`
  impostata. L'AI per le edizioni dubbie con Ollama acceso.

## Versione per macOS (da valutare)

Analisi del 24/11/2026, solo leggendo il codice: su un Mac non è ancora stato provato niente.

**Cosa va già bene.** PySide6, pymobiledevice3, mutagen, keyring (sul Mac usa il Portachiavi) e la cartella dati
`~/.myEasyMP3toIPhone` funzionano anche su macOS. Il protocollo verso l'iPhone (ATC, AFC) è lo stesso. Sul Mac il
servizio che parla con l'iPhone (usbmuxd) fa parte del sistema: non c'è da installare il driver di Apple come su
Windows. Le parti scritte solo per Windows sono poche:
- `albumcheck.store_country`: legge il paese da Windows con `ctypes.windll`, e sul Mac oggi risponde sempre `US`.
  Serve `QLocale` o `locale`.
- `gui/file_actions.open_in_explorer`: Esplora risorse. Sul Mac va `open -R`.
- I testi che nominano Windows: Gestione credenziali, `%USERPROFILE%`, variabili di Windows, Esplora risorse,
  "Dispositivi Apple". Vanno resi neutri o scelti secondo il sistema.
- Le variabili d'ambiente: un programma aperto dal Finder non vede quelle di `.zshrc`, quindi sul Mac vale soprattutto
  il file `myEasyMP3toIPhone.env` della cartella dati. Da spiegare nel README.
- Percorsi: i limiti di Windows (230 caratteri, nomi riservati) sul Mac non servono ma non fanno danni. I percorsi del
  registro della provenienza scritti da un PC Windows sono già "di un altro computer".

**Cosa costa.**
1. **Un Mac.** PyInstaller non costruisce per macOS da Windows: build e prove si fanno su un Mac (Apple Silicon;
   per i Mac Intel serve una seconda build o una build universale). In alternativa una macchina macOS di GitHub
   Actions per la sola build, ma le prove con l'iPhone vogliono un Mac vero.
2. **La build e la distribuzione.** Un `.app` (PyInstaller `--windowed`, icona `.icns`) in un `.dmg`.
   `vscode_deploy.py` è condiviso e pensato per Windows (zip, cartella di installazione): per il Mac serve uno script
   a parte (non si cambia qui).
3. **La firma di Apple (facoltativa).** Senza l'Apple Developer Program (99 $ all'anno) il programma non è firmato né
   notarizzato. Per uso personale basta aprirlo la prima volta con tasto destro → Apri (o `xattr -dr
   com.apple.quarantine`). Per distribuirlo ad altri la firma serve.
4. **Il rischio più grosso: il Finder.** Sul Mac, quando colleghi l'iPhone, il Finder (AMPDevicesAgent) apre da solo
   una sessione di sincronizzazione. Va provato se occupa il canale ATC e blocca gli invii del programma, e se
   "Gestisci manualmente musica" va attivato anche dal Finder. Se il Finder può sincronizzare da solo, l'avviso "non
   premere Sincronizza" vale anche lì.
5. **Le prove.** Tutte quelle con l'iPhone attaccato (sezione sopra), di nuovo sul Mac.

**Stima.**
- Codice: 1-2 giorni.
- Build e pacchetto `.app`/`.dmg`: 1-2 giorni.
- Prove con l'iPhone su Mac: 1 giorno, di più se il Finder dà problemi.
- Spese: nessuna se c'è già un Mac e il programma serve solo a te; altrimenti il Mac e i 99 $ all'anno per la firma.
- Da decidere prima: per chi è la versione Mac (solo tu o anche altri) e se c'è un Mac per le prove.
