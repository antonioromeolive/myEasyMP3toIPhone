# TODO

## Le proposte dubbie di "Associa sorgenti"

Sui dati veri restano 44 proposte non spuntate (regole senza un candidato chiaro). Controllare cosa ne dice l'AI
della scansione e se i candidati sono giusti (versioni dal vivo, remaster). In attesa: l'utente non ha ancora fatto
*Associa sorgenti* con la build nuova.

## Invio di M4A in Apple Lossless (ALAC) — solo se servirà

Oggi si inviano MP3, FLAC e AAC. ALAC vuole il suo formato di inserimento (rustunes `protocol/alac.rs`: tra
l'altro `gapless_heuristic_info`, `analysis_inhibit_flags`). Per ora non serve: i 20 M4A della musica dell'utente
sono tutti AAC.

## Trovati nelle prove del 26/11/2026

- **Ricerca vuota per una scelta dimenticata** (schede PC e iPhone): un artista scelto prima negli elenchi resta
  attivo e la ricerca dice "0 di N brani" senza dire perché. Dire "0 brani di <artista>: cerca in
  tutti" con un clic che toglie la scelta (o una ricerca nuova la toglie da sola: da decidere). Proposta
  dell'utente: dopo Applica, o tornando sulla scheda, mostrare "(Tutti)" o selezionare i brani appena toccati.
- **Compilation dalla scheda iPhone non riunisce un album diviso**: "PROVA Raccolta Due" (3 artisti, senza artista
  dell'album) inviata così diventa 3 album sull'iPhone (un album e un artista dell'album per cantante); *Cambia i tag →
  Compilation* mette `compilation` vero ma gli album restano 3, anche riaprendo l'app. Per riunirli serve lo stesso
  artista dell'album, cioè Ricopia. Correggere il suggerimento della casella (oggi fa credere che la spunta riunisca)
  e, se i brani scelti sono in album diversi dell'iPhone, proporre Ricopia con "Artisti Vari".
- **"Anche sull'iPhone" che non fa niente in silenzio** (editor della scheda PC): con la sola spunta Compilation, già
  presente sull'iPhone, `queue_files(…, UPDATE)` non trova differenze e non mette niente in attesa senza dirlo.
  Dire "Anche sull'iPhone: niente da fare, sull'iPhone hanno già questi tag" (o quanti sono andati in attesa e
  perché gli altri no). Nella finestra di Applica, un *Usa i tag* che cambia artista o artista dell'album diventa
  Ricopia (`plan_updates`): dirlo già nella riga, non solo al momento di applicare.
- **Album doppio "AA.VV." / "Artisti Vari"** (letto nel database dell'iPhone il 26/11/2026): "100 Greatest Male
  Voices" ha **due righe `album` con lo stesso `sync_id` 3526**: una con artista dell'album "Artisti Vari" (93 brani),
  una con "AA.VV." (7 brani). I 7 brani hanno come artista dell'album del brano "Artisti Vari": solo la riga dell'album
  dice "AA.VV.". Il programma legge l'artista dal brano e raggruppa per `sync_id`, quindi vede un album da 100; l'app
  Musica usa la riga dell'album e ne mostra due. Brani vecchi (pid bassi), origine non chiara. Da fare: un controllo
  (in *Controlla la musica* dell'iPhone) per album con lo stesso `sync_id` in più righe, o con l'artista della riga
  diverso da quello dei suoi brani, che proponga Ricopia di quei brani; provare la Ricopia sui 7.
  **Fatto** (filtro *Nell'album sbagliato sull'iPhone*, pulsante *Rimetti nell'album giusto*): sui dati veri 26 brani
  in 3 album. **Da provare sul telefono**: con le due righe che hanno lo stesso `sync_id` non è certo che l'iPhone
  rimetta i 7 brani nella riga giusta.
- **L'elenco Compilation dell'app Musica** segue `album.all_compilations`, non la spunta dei brani: *Cambia i tag →
  Compilation* (`update_track`) cambia `item.is_compilation` ma non l'album ("PROVA Album Uno": brani 1, album 0, non
  compare tra le Compilation). Un invio o una Ricopia con Compilation e artista dell'album lo fa ricalcolare
  ("PROVA Raccolta Due" riunita: `all_compilations` 1). Quindi Compilation dalla scheda iPhone dovrebbe diventare
  una Ricopia (o dirlo).
- Prova 3 del 26/11/2026: "PROVA Raccolta Due" (3 album, uno per cantante) con artista dell'album e Compilation
  cambiati nella scheda PC, *Anche sull'iPhone* → Applica (Usa i tag diventato Ricopia): un album solo. Restano 3 righe
  `album` vuote (una per cantante), invisibili nell'app.
- **Riquadro dei tag tagliato** (scheda iPhone): la casella "Anche sul PC: …" su una riga sola allargava il riquadro;
  corretto (casella corta, spiegazione in una riga che va a capo; lo stesso per "Anche sull'iPhone" nella scheda PC).

## Suonerie verso l'iPhone — per ora non interessa

Oggi un `.m4a` è sempre musica; le suonerie dell'utente stanno in `…\Suonerie` (cartelle escluse). Se servirà:
le suonerie dell'iPhone sono `.m4r` (AAC, al massimo ~40 s) in `/iTunes_Control/Ringtones`, registrate in
`/iTunes_Control/iTunes/Ringtones.plist` (come iTunes/Finder, iMazing). Prima provare a mano con pymobiledevice3 (AFC)
se le versioni recenti di iOS le accettano ancora così; poi un'azione "Invia come suoneria (PC → iPhone)" che va in
attesa e parte con **Applica**, come tutte le scritture sull'iPhone.

**Crea una suoneria da un brano** (idea dell'utente):
- **Da dove parte:** tasto destro su un brano nella scheda PC o nella scheda iPhone → *Crea una suoneria…* (dall'iPhone
  il brano si legge, in sola lettura).
- **La finestra:** forma d'onda o cursore, inizio e fine (al massimo ~40 s), ascolto del pezzo (QtMultimedia),
  dissolvenza facoltativa. Il risultato è un `.m4r` (AAC) nuovo nella cartella delle suonerie: il brano non cambia.
- **Scheda Suonerie** (nuova, accanto a PC e iPhone): le suonerie della **cartella delle suonerie** (quelle create
  qui e quelle già presenti), e quelle sull'iPhone. Da qui *Invia come suoneria (PC → iPhone)*, in attesa fino ad
  **Applica**.
- **Impostazioni → Suonerie:** la cartella delle suonerie (dove si salvano i nuovi `.m4r`) e il **percorso di
  ffmpeg**, che l'utente installa da sé: **ffmpeg non si distribuisce con il programma**. Senza ffmpeg la voce del
  menu spiega cosa manca. Una cartella delle suonerie dentro una cartella della musica va esclusa dalla scheda PC.
- Regole del progetto: nuova impostazione → "Quale valore vince" del README.

## `$NOME` in tutti i campi di percorso (Impostazioni)

Il campo del percorso di ffmpeg accetta `$NOME` (una variabile d'ambiente), espanso all'avvio; lo stesso per **tutti** i
percorsi delle Impostazioni: cartelle della musica, Libreria, cartelle escluse, cartella delle suonerie. Oggi
`config._expanded` espande già `%NOME%`, `$NOME` e `~` per Libreria e cartelle della musica, ma solo se scritti a mano
in `settings.json`: le Impostazioni le scelgono con la finestra delle cartelle e non lasciano scrivere; le cartelle
escluse (`hidden_folders`) non si espandono. Serve: un campo di testo accanto a ogni scelta, si salva il `$NOME`, le
Impostazioni e *Informazioni* mostrano anche il valore espanso; una variabile che manca lo dice. Un nome nuovo (per
esempio per ffmpeg) si chiede all'utente e va nella tabella delle variabili, `environment.VARIABLES` e il
`.TEMPLATE.env`; README "Quale valore vince".

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
  - La correzione della grafia (`phone_actions.align_spelling`) è fatta e ora è dentro ogni aggiornamento dal PC
    (`IPhonePanel.split_for_spelling`: niente comando a parte, su richiesta dell'utente); **provata sul
    telefono** il 24/11/2026 come comando a parte: "PROVA Raccolta 1" di "PROVA Artista" è diventato "PROVA Raccolta 01" di "PROVA
    ARTISTA" (album e artista dell'album insieme), 97 brani di servizio inviati e tolti, nessuno rimasto, 17 s in
    tutto; la sessione ha cancellato anche le altre righe vuote. L'utente ha visto il nome nuovo nell'app. Restano
    da provare dalla finestra (build nuova) e su un album vero. Sull'iPhone restano vuoti (invisibili) "PROVA
    Raccolta 01" e "PROVA ARTISTA".
- **Prove del 26/11/2026** (brani finti in `C:\temp\PROVA-myEasyMP3toIPhone`, album "PROVA Album Uno" di "PROVA
  Artista"): *Copia da PC a iPhone* di 3 brani + **Applica**: ok; con l'app Musica aperta l'album nuovo è comparso da
  solo, senza chiuderla. *Cambia i tag* con Compilation sui 3 brani: ok (nel database dell'iPhone `compilation`
  vero, colonna Sul PC ⟳, 3 azioni applicate); nell'app Musica nessun cambiamento visibile, nemmeno riaprendola: con un
  solo artista e l'artista dell'album scritto l'album resta sotto quell'artista. Da provare con "PROVA Raccolta Due"
  (artisti diversi, senza artista dell'album).
- **App Musica che non si aggiorna da sola**: dopo ogni scrittura il programma manda l'avviso di fine
  sincronizzazione di iTunes (`com.apple.itunes-mobdev.syncDidFinish`, `iphone.post_sync_finished`). Con l'app
  Musica aperta: se si aggiorna da sola, togliere dal messaggio finale l'invito a chiuderla e riaprirla; se no,
  provare anche `syncWillStart` all'inizio della sessione.

## Copertine degli album (24/11/2026)

Sull'iPhone 59 album su 234 non avevano l'immagine dell'album: tutti messi da altri programmi (i brani hanno la
copertina, all'album manca la riga `best_artwork_token`); i 90 album con brani inviati da qui ce l'hanno tutti.
Due album veri rimpiazzati dal PC: l'immagine c'è, confermato nell'app. Fatto *Sistema le
copertine (PC → iPhone)*. Restano:
- 7 album senza sorgente sul PC (non c'erano più): l'utente li ha salvati dall'iPhone sul PC, ora associati e con
  la copertina nei file; manca *Sistema le copertine* su quei 56 brani;
- i 2 album con la copertina in scala di grigi si vedono nell'app (controllato dall'utente il 24/11/2026): il
  problema delle miniature vuote che rustunes descrive qui non c'è, niente da fare;
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

## Cartella dati su OneDrive, più PC uno alla volta (bassa probabilità)

Analisi del 26/11/2026, solo leggendo il codice. Programma installato su ogni PC; cartella dati con
`MYEASYMP3TOIPHONE_HOME=%OneDrive%\myEasyMP3toIPhone` (variabile di Windows su ogni PC: `%OneDrive%` si espande).

**Va già.** Il registro della provenienza ha una copia sull'iPhone e si unisce a ogni connessione (ripara anche una
copia OneDrive vecchia); cartelle della musica per computer; elenco e impronte dell'iPhone, Cartelle preferite (nomi),
profili AI e le azioni in attesa per brano dell'iPhone valgono ovunque. Le chiavi sono nella Gestione credenziali di
ogni PC: da riscrivere su ognuno, o `$NOME`.

**Il nodo: un brano ha una sola sorgente** (`provenance.Link`: un PC, un file). Su PC-B un brano di PC-A è "PC-A":
niente ✔/⟳, Ricopia, Usa i tag; *Associa sorgenti* non lo propone; associarlo a mano toglie la sorgente a PC-A (vince
la riga più recente). Strade: con gli stessi percorsi sui due PC basta "PC-B ha la stessa musica di PC-A"; con percorsi
diversi servono collegamenti per computer, quello di PC-B ricavato con l'impronta (solo se è la stessa copia del file;
per rip diversi restano le regole, confermate). Cambia il formato del registro anche sull'iPhone: oggi una versione
vecchia ignora un registro di altro formato e riscrive il suo sull'iPhone, perdendo le righe nuove.

**Dati legati ai percorsi di un PC.** `modifiche_tag.json` e le voci per file di `iphone_in_attesa.json` (una Ricopia
in attesa con un file di PC-A fallirebbe da PC-B): serve il nome del PC. `hidden_folders`, `last_*`, posizione della
finestra: da dividere per computer. `library_dir`: un PC senza le sue cartelle userebbe la Libreria dell'altro.
`cache_tag.json` (15 MB, mai pulita, riscritta tutta a ogni salvataggio): meglio una per PC fuori da OneDrive.

**OneDrive.** Il lucchetto `myEasyMP3toIPhone.instance.lock` (`setStaleLockTime(0)`): un lucchetto rimasto da un altro
PC non si riconosce come vecchio, PC-B non parte (da provare); può invece dire "aperto su PC-A". Ritardo e copie in
conflitto (`settings-PCB.json`) se si cambia PC troppo in fretta. `os.replace` può fallire mentre OneDrive tiene il file
(il registro non lo gestisce): riprovare. Cartella dati "Sempre su questo dispositivo"; log a rotazione e `Backup\`
meglio sul PC; il `.env` con chiavi in chiaro viaggerebbe.

**Versioni diverse.** Nessun controllo per dati di formato più nuovo: una versione vecchia potrebbe riscrivere vuoti i
file che non sa leggere. Serve "dati di una versione più nuova: aggiorna il programma".

**Ordine.** 1) controllo delle versioni, avviso "aperto su PC-A", salvataggi che riprovano; 2) cache, log e backup
fuori da OneDrive, impostazioni dei percorsi per computer; 3) azioni in attesa e modifiche dei tag con il PC;
4) collegamenti per computer nel registro (il pezzo grosso). Da sapere prima: stessi percorsi sui due PC? Copie
identiche dei file o rip diversi?
