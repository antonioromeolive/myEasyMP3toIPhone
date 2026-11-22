# myEasyMP3toIPhone

Programma per Windows per organizzare la musica, modificarne i tag, controllare che gli album siano completi,
trovare i problemi della libreria (anche con l'AI) e trasferire la musica da e verso l'iPhone.

- [Installazione](#installazione)
- [Funzioni](#funzioni)
- [Controlla la musica](#controlla-la-musica)
- [L'iPhone](#liphone)
- [L'AI: profili e chiavi](#lai-profili-e-chiavi)
- [Il file delle variabili (myEasyMP3toIPhone.env)](#il-file-delle-variabili-myeasymp3toiphoneenv)
- [La cartella dati](#la-cartella-dati)
- [Quale valore vince](#quale-valore-vince)
- [Sviluppo e build](#sviluppo-e-build)

## Installazione

Dallo zip della distribuzione (`myEasyMP3toIPhone-<versione>-windows-x64.zip`):

1. Scompatta in una cartella scrivibile, per esempio `%LOCALAPPDATA%\Programs\myEasyMP3toIPhone` (non in *Programmi*).
2. Doppio clic su **Create shortcuts.cmd**: mette *myEasyMP3toIPhone* nel menu Start e, se vuoi, sul desktop.
3. Avvia *myEasyMP3toIPhone*. La prima volta Windows può dire "PC protetto da Windows" (il programma non è firmato):
   *Ulteriori informazioni* → *Esegui comunque*.

Per l'iPhone serve l'app gratuita **Dispositivi Apple** dal Microsoft Store (oppure iTunes): installa il driver USB.

**Aggiornare:** chiudi il programma, cancella la cartella, scompatta la nuova versione al suo posto, esegui di nuovo
*Create shortcuts.cmd*. Le impostazioni restano. **Disinstallare:** *Remove shortcuts.cmd*, poi cancella la cartella
(e `%USERPROFILE%\.myEasyMP3toIPhone` per togliere anche le impostazioni).

## Funzioni

> **I file sul PC sono in sola lettura.** Il programma non modifica, sposta o cancella mai i file delle cartelle che
> apri (compresa la Libreria). Le modifiche dei tag, fatte a mano, dalla scansione o da *Verifica album*, restano **in
> sospeso** nella cartella dati e valgono per le **copie**: quelle inviate all'iPhone, esportate o importate. Le
> operazioni sull'iPhone non toccano mai i file del PC; quelle sul PC si riflettono sull'iPhone al prossimo invio.

Due schede: **PC** (i brani della cartella aperta) e **iPhone** (la musica dell'app *Musica* dell'iPhone, vedi
[L'iPhone](#liphone)).

| Pulsante | Cosa fa |
|---|---|
| **Libreria** | mostra la Libreria musicale (la cartella si sceglie in *Impostazioni*; predefinita `Musica\myEasyMP3toIPhone`) |
| **Apri cartella** | mostra i brani di una cartella qualsiasi, in sola lettura (da riga di comando: `myEasyMP3toIPhone --open <cartella>`) |
| **Importa cartella** | copia una cartella nella Libreria in `Artista / Album (Anno) / NN - Titolo.ext`, con le modifiche in sospeso applicate alle copie |
| **Esporta** | copia i brani selezionati (o quelli dell'artista o dell'album scelti negli elenchi) in una cartella, con la stessa struttura e le modifiche in sospeso |
| **Verifica album** | controlla su [MusicBrainz](https://musicbrainz.org) che gli album siano completi, elenca i brani mancanti, propone i tag corretti e la copertina (in sospeso, per le copie) |
| **Controlla la musica** | cerca i problemi della cartella aperta o della musica sull'iPhone, con i controlli che scegli (vedi sotto) |
| **Impostazioni** | cartella della Libreria, AI della scansione, **lingua dell'interfaccia** (italiano o inglese), profili AI |
| **Informazioni** | versione, cartella dati, variabili d'ambiente e da dove viene ciascuna, dove sono le chiavi |

**Elenchi Artisti e Album (i filtri).** Sopra la tabella dei brani due elenchi affiancati, ognuno ordinabile cliccando
sull'intestazione:

- **Artisti** (artista, numero di album, numero di brani): sceglierne uno (o più, con Ctrl/Maiusc) filtra l'elenco
  Album sui suoi album e la tabella sui suoi brani;
- **Album** (album, artista, anno, brani; l'icona dice l'esito di *Verifica album*): sceglierne uno (o più) mostra
  solo quei brani;
- la riga **(Tutti …)**, sempre in cima, toglie il filtro; scegliere un artista (o "(Tutti)") azzera l'album scelto
  prima; la casella *Cerca* filtra ancora dentro la scelta;
- **Formato** (accanto a *Cerca*): solo MP3, FLAC, M4A o OGG/Opus, con il numero di brani di ciascuno. Vale per gli
  elenchi, la tabella, *Esporta*, *Verifica album*, *Controlla la musica* e l'invio all'app Musica.

La tabella dei brani si ordina cliccando sull'intestazione di una colonna (Artista, Album, Titolo, Anno…); finché non
la clicchi i brani sono in ordine di artista, album, disco e traccia. *Esporta*, *Verifica album* e *Invia all'app Musica*
senza brani selezionati in tabella usano l'artista o l'album scelti negli elenchi.

Artisti e album che differiscono solo per maiuscole, accenti o spazi ("Queen" e "queen") sono un gruppo solo, mostrato
con la grafia più usata (a parità, quella con le maiuscole). I tag dei file non cambiano: la scansione segnala la
variante, perché l'iPhone la considera un artista diverso.

**Colonna iPhone.** Per ogni brano: **✔** nell'app *Musica* dell'iPhone c'è lo stesso brano, con gli stessi tag;
**⟳** c'è lo stesso brano, ma con tag diversi; vuoto,
non c'è. "Lo stesso brano" vuol dire stesso titolo e stesso album, senza badare a maiuscole, accenti e spazi, e un
artista in comune; un brano con modifiche in sospeso si ritrova anche con i tag del file. Si basa sulla musica
dell'iPhone letta all'ultima connessione e salvata nella cartella dati, quindi si vede anche a iPhone disconnesso (il
suggerimento sull'intestazione dice di quando è l'elenco).

**Spunte e modifiche in attesa.** Nella colonna *iPhone* la spunta vuol dire "voglio questo brano sull'iPhone".
Mettere o togliere una spunta non fa niente subito: il brano resta **in attesa**, con un segno e un colore diversi da
quelli delle cose fatte e la riga appena colorata:

| Segno | Vuol dire |
|---|---|
| ✔ verde | c'è, uguale |
| ⟳ arancio | c'è, con tag diversi |
| **＋ blu** | in attesa: da inviare |
| **－ rosso** | in attesa: da togliere dall'iPhone |
| **⟳ blu** | in attesa: da aggiornare (anche quando cambi i tag a iPhone disconnesso, o con il tasto destro → *Aggiorna più tardi*) |

- Una spunta cambiata su una riga selezionata vale per tutte le righe selezionate. Anche **artisti e album** negli
  elenchi in alto hanno la spunta, a tre stati (tutti i brani sull'iPhone, alcuni, nessuno), in corsivo blu se
  dentro c'è qualcosa in attesa: cliccarla mette o toglie tutti i loro brani.
- **Togliere** una spunta vale solo per i brani che sull'iPhone vengono da quel file (colonna *Sorgente* della scheda
  iPhone): un brano abbinato solo per i tag non si toglie mai così (la sua spunta non si può togliere).
- Quando c'è qualcosa in attesa compare una barra in fondo: *In attesa per l'iPhone: N da inviare, N da togliere,
  N da aggiornare* con **Annulla le modifiche** e **Applica…** (a iPhone connesso). *Applica* mostra il riepilogo,
  chiede conferma e fa tutto insieme: invio, eliminazione, aggiornamento (con *Cambia tag* o *Rimpiazza*, come per
  una modifica dei tag; alla fine ricorda le playlist dei brani rimpiazzati).
- Le modifiche in attesa restano nella cartella dati (`iphone_in_attesa.json`) anche chiudendo il programma; quelle
  già fatte si tolgono da sole a ogni lettura dell'iPhone. *Applica* fa quelle dei brani della cartella aperta.

**Tag.** A destra si modificano titolo, artista, artista album, album, numero di traccia e di disco, anno, genere,
la spunta **Compilation** e la copertina (MP3, M4A, FLAC, OGG, Opus; copertina per MP3, M4A, FLAC). Con più brani
selezionati, solo i campi modificati valgono per tutti; la spunta mostra un quadratino pieno a metà quando i brani
sono diversi.

**Compilation.** Un album di più artisti: l'*artista* è quello di ogni brano, l'*artista album* è "Artisti vari", e
in più c'è la spunta **Compilation** (nei file: TCMP negli MP3, COMPILATION nei FLAC e Ogg, cpil negli M4A). L'app
Musica dell'iPhone tiene insieme l'album solo con tutte e tre le cose; senza la spunta lo divide in un album per
artista. La scansione, quando propone "Artisti vari", propone anche la spunta. *Numera in ordine* assegna 1, 2, 3… nell'ordine della tabella. *Salva modifiche* **non
scrive nel file**: salva le modifiche in sospeso (`modifiche_tag.json` e `copertine\` nella cartella dati). In tabella
i brani modificati hanno il titolo in corsivo blu, e il suggerimento elenca le modifiche (*campo: prima → dopo*).
*Torna ai tag del file* le annulla.

**Le copie** (invio all'iPhone, esportazione, importazione) ricevono i tag con le modifiche e la copertina nuova; per
gli MP3 la copia è in **ID3 v2.3** (con i frame convertiti: l'anno va in TYER), la versione letta da Windows,
autoradio e app, e senza i vecchi tag ID3v1 e APE, che alcuni lettori leggono al posto di quello giusto.

**Copie e aggiornamenti.** Importando o esportando, un file già presente nella destinazione si confronta per
**dimensione e data**: identico → saltato; la sorgente è più recente → la destinazione si **aggiorna**; la destinazione è
più recente → resta com'è (il riepilogo lo dice). Un brano con modifiche in sospeso si copia sempre di nuovo. La sola
dimensione non basterebbe: cambiare i tag spesso non la cambia.

**Cartelle grandi.** La prima lettura usa più file in parallelo; i tag letti restano in `cache_tag.json` nella
cartella dati, e le volte successive si rileggono solo i file cambiati (dimensione o data diverse). Dimensione e data
vengono dall'elenco della cartella, senza aprire i file uno per uno: riaprire una cartella già letta è veloce anche su
un disco esterno o di rete. Durante la lettura
gli elenchi sono vuoti: la barra di stato mostra l'avanzamento. Il programma si apre **una volta sola**: una seconda
copia lo dice e si chiude.

**File illeggibili.** Un file che non si riesce a leggere (danneggiato, bloccato, disponibile solo online in
OneDrive…) compare in rosso, con il motivo nel suggerimento, e non interrompe la lettura della cartella.

## Controlla la musica

*Controlla la musica* (F6, la "scansione") analizza la cartella aperta, oppure la musica dell'app *Musica* dell'iPhone confrontata con la
Libreria (si può fare anche a iPhone disconnesso, con l'ultimo elenco letto). Nella finestra scegli **quali controlli
fare** (le caselle della tabella qui sotto, ognuna con una riga di spiegazione; le scelte si ricordano). Prima
applica delle regole locali, veloci e gratuite; poi, se scegli di usarla, l'AI. Il rapporto resta in
`.myEasyMP3toIPhone\scansioni\`. Ogni problema può avere una **correzione**: si applica dalla finestra dei risultati, dopo
una conferma, come **modifiche in sospeso** (i file sul PC non cambiano; vanno sulle copie inviate all'iPhone); *Mostra
i brani* li seleziona nella scheda PC. I problemi trovati sull'iPhone non hanno correzioni automatiche: si correggono i
brani sul PC e poi si usa *Rimpiazza*, o si cambiano dalla scheda iPhone (tasto destro).

| Sintomo | Cosa cerca | Correzione |
|---|---|---|
| **File che non si aggiornano** | sull'iPhone, brani con tag diversi da quelli del PC (o delle modifiche in sospeso); MP3 con un vecchio tag ID3v1 diverso o con un tag APE (solo informazione: le copie inviate ne sono ripulite) | sull'iPhone nessuna (la colonna *iPhone* della scheda PC mostra le differenze) |
| **Album con pochi brani** | numeri di traccia mancanti, meno brani del totale dichiarato, album di 1-2 brani; sull'iPhone, album con meno brani che sul PC | (Verifica album trova i titoli mancanti) |
| **Collezioni divise su più album** | una cartella con brani in album diversi; lo stesso album scritto in modi diversi o con "CD 1"/"Disc 2" nel nome; una compilation senza *Artista album* | unifica album e artista album ("Artisti vari" e la spunta *Compilation* per le compilation), sposta il numero del disco in *N. disco* |
| **Artisti scritti in modi diversi** | **certo**: le stesse parole a parte maiuscole, accenti, punteggiatura, "The" e ordine ("Battiato Franco" = "Franco Battiato", "AC/DC" = "ACDC"); **dubbio**: solo il cognome ("Battiato"), le iniziali ("F. Battiato"), un errore di battitura: decide l'AI (con album e anni) e, se lo chiedi, MusicBrainz (nomi e alias dell'artista), solo per questi gruppi; senza nessuno dei due restano "forse lo stesso artista", da controllare. **Duetti** ("A & B", "A feat. B", "A, B"): se A c'è anche da solo, artista e artista album diventano A e gli ospiti vanno nel titolo, "Titolo (feat. B)" (l'app Musica non gestisce più artisti); un nome come "Simon & Garfunkel" resta com'è | scrive ovunque la forma **più usata** (quella con più brani); per l'iPhone poi *Rimpiazza* (o *Applica*) |
| **Solo sull'iPhone** | brani dell'app Musica senza un brano uguale (artista, album, titolo) nella Libreria del PC | nessuna: salvali sul PC dalla scheda iPhone (tasto destro → *Salva su PC*) |
| **Brani duplicati** | **lo stesso brano**, non per forza lo stesso file: nello stesso album una copia "Titolo (2)" o lo stesso numero e titolo due volte; ovunque, i file con lo **stesso audio** (impronta, anche con tag e nomi diversi) e i file con stesso artista e titolo e durata entro 2 secondi ma audio diverso (un MP3 e un FLAC, due codifiche). Se titolo o album nominano versioni diverse (live, remix, demo…) la coppia è dubbia e la guarda l'AI, se è accesa: solo quelle coppie, mai tutti i brani; senza AI resta "da controllare". Un problema per artista, una riga per brano. Può essere giusto (l'album e una raccolta): decidi tu | nessuna automatica: quale copia tenere lo decidi tu (*Mostra i brani*) |
| Tag mancanti, file illeggibili | brani senza titolo/album/artista, file danneggiati | ricava i tag mancanti dai nomi di cartelle e file |

**Con l'AI** l'AI riceve una tabella compatta degli album (artista album, album, anni, numero di brani, numeri presenti,
totale dichiarato, nome della cartella, generi) e i problemi trovati dalle regole. Scarta quelli che non sono problemi
(per esempio album diversi con lo stesso nome, "Greatest Hits"), ne aggiunge altri e propone le correzioni. Non riceve
né i file né i percorsi completi. Con un'AI nel cloud questi dati escono dal computer; con Ollama no.

**L'AI predefinita è Ollama sul tuo computer.** Al primo avvio, se non hai profili AI, il programma crea il profilo
**"Ollama locale"** (`http://localhost:11434`) con un modello già installato: il primo tra le famiglie gemma4, qwen3,
gemma3, llama3, mistral, gpt-oss, escludendo i modelli `:cloud` (girano su ollama.com) e quelli di embedding; senza
modelli installati usa `llama3.1:8b` (da scaricare con `ollama pull llama3.1:8b`). Lo sceglie come *AI della
scansione*. Per cambiarla: *Impostazioni → Generale → AI della scansione*, oppure *(nessuna: solo le regole)*. Le
tue scelte non vengono mai cambiate.

In console: `myEasyMP3toIPhone-cli --scan <cartella> [--ai "<profilo>"]`.

## L'iPhone

**Basta attaccare l'iPhone con il cavo:** il programma lo rileva da solo (controlla ogni 3 secondi) e si connette. La
prima volta l'iPhone chiede **"Autorizzare questo computer?"**: tocca *Autorizza* e inserisci il codice. La scheda
**iPhone** e la barra di stato dicono a che punto è; se la connessione automatica non riesce (iPhone bloccato,
autorizzazione negata) lo dice lì, e *Connetti iPhone* riprova. Senza il driver Apple la scheda dice di installare
*Dispositivi Apple*. Il pulsante dice cosa fa: **verde "Connetti iPhone"** quando non è connesso, **rosso
"Disconnetti iPhone"** quando lo è; il titolo della scheda diventa **"iPhone ●"** in verde, così lo si vede anche
dalla scheda PC. Dopo *Disconnetti* il programma non si riconnette da solo finché non premi *Connetti iPhone* o stacchi
e riattacchi il cavo. Staccando il cavo l'iPhone risulta disconnesso.

**La musica dell'app Musica.** Connesso l'iPhone, la scheda **iPhone** mostra i brani dell'app *Musica* con i
titoli, gli artisti e gli album che mostra l'app: il programma ne copia sul PC il database (`MediaLibrary.sqlitedb`)
e lo legge, perché sul telefono i file hanno nomi casuali (`F12/ABCD.mp3`). Sono solo i brani con un file
sull'iPhone, non quelli in streaming da Apple Music. *Cerca* filtra per titolo, artista o album.

- **Sul PC:** ✔ nella cartella aperta nella scheda PC c'è lo stesso brano, con gli stessi tag; ⟳ c'è, con tag
  diversi; vuoto, non c'è. Lo stesso confronto della colonna *iPhone* della scheda PC.

**Il suggerimento di ✔ e ⟳** (colonna *iPhone* della scheda PC, *Sul PC* della scheda iPhone) è una tabella: in
cima il brano abbinato (il brano dell'iPhone, o il file del PC con il percorso) e come è stato abbinato, *certo*
dal registro della provenienza o *probabile* solo per artista, album e titolo; sotto, tutti i tag confrontati, sul PC
e sull'iPhone affiancati, con i valori diversi evidenziati. Artisti e album che differiscono solo per maiuscole o
accenti non sono evidenziati: sull'iPhone sono lo stesso gruppo.
- **Tasto destro** su uno o più brani: **Salva su PC…** copia i file in una cartella a scelta (proposta: la Libreria),
  ordinati in `Artista/Album (Anno)/NN - Titolo` con i nomi che mostra l'app; crea solo file nuovi, un file già
  presente sul PC non viene mai sostituito. **Mostra nella scheda PC** seleziona i brani corrispondenti del PC.
- L'elenco letto resta in `iphone_musica.json` nella cartella dati: scheda iPhone, colonna *iPhone* e scansione
  funzionano anche a telefono disconnesso (*Aggiorna elenco* lo rilegge).

### Scrivere nell'app Musica

Il programma scrive nella musica dell'app Musica con lo stesso servizio di sincronizzazione di Apple che usano iTunes e
CopyTrans Manager (*AirTrafficControl*), senza iTunes e senza sincronizzare tutto: ogni volta manda solo le modifiche
("Delta"), mai una sostituzione completa.

| Dove | Tasto destro | Cosa fa |
|---|---|---|
| Scheda **PC** | **Invia all'iPhone** | i brani selezionati che non sono sull'iPhone: una copia con i tag e la copertina modificati (i file del PC non cambiano) |
| Scheda **PC** | **Rimpiazza sull'iPhone** | i brani selezionati che sull'iPhone hanno tag diversi (⟳): vedi *Rimpiazza* qui sotto |
| Scheda **iPhone** | **Rimpiazza con la versione del PC** | lo stesso, partendo dai brani dell'iPhone |
| Scheda **iPhone** | **Cambia tag…** | titolo (un brano alla volta), album, genere, anno, numero di traccia e di disco, la spunta **Compilation** (a tre stati con brani diversi); un campo vuoto non cambia, 0 svuota anno o numero |
| Scheda **iPhone** | **Elimina dall'iPhone…** | toglie i brani dall'app Musica; l'iPhone cancella i loro file da solo, entro qualche minuto |

- Alla fine di ogni scrittura il programma manda all'iPhone l'avviso di fine sincronizzazione, come iTunes (una prova:
  non è documentato).
- **L'app Musica potrebbe non aggiornarsi da sola** se è aperta durante l'invio: chiudila del tutto (scorri via la sua scheda)
  e riaprila; i brani si trovano nella tua libreria (*Libreria → Artisti* o *Brani*), non cercando in Apple Music.
- **Formati:** MP3, FLAC (l'iPhone li suona così come sono) e M4A in AAC. Gli M4A in Apple Lossless non ancora.
- **Copertine:** quella modificata, o altrimenti quella del file, se è JPEG o PNG.
- **Album e artisti:** un brano va nell'album e nell'artista già presenti sull'iPhone con lo stesso nome (senza badare
  a maiuscole, accenti e spazi), con la grafia dell'iPhone: niente doppioni. Per lo stesso motivo la colonna *iPhone*
  confronta artisti e album senza badare a maiuscole e accenti ("Artisti vari" e "Artisti Vari" sono uguali).
- **Compilation:** si invia la spunta, con l'artista dell'album ("Artisti vari" se manca): l'album resta intero
  nell'app Musica.
- **Rimpiazza** prima invia la versione del PC, poi toglie quella vecchia, solo se l'invio è riuscito. Il brano
  rimpiazzato perde il conteggio degli ascolti e la presenza nelle playlist fatte sull'iPhone: prima di confermare e
  alla fine il programma dice in quali playlist era ciascun brano, così lo rimetti a mano (le playlist smart si
  aggiornano da sole).
- **Una modifica da una parte si propone anche dall'altra**, per i brani che hanno la sorgente su questo PC (colonna
  *Sorgente*), e si chiede ogni volta:
  - cambiando i tag nella scheda **PC** (editor dei tag, correzioni della scansione, *Verifica album*, *Torna ai tag
    del file*), se i brani collegati sull'iPhone ora sono diversi: *Aggiornarli anche lì?* Titolo, album, genere,
    anno, numeri e compilation con *Cambia tag* (restano ascolti e playlist); artista, artista dell'album, una
    copertina nuova o un campo da svuotare con *Rimpiazza*. Senza iPhone connesso lo dice la barra di stato e i brani
    restano ⟳;
  - con **Cambia tag** nella scheda **iPhone**, se i brani vengono da file di questo PC: *Salvare le stesse modifiche
    anche per quei file?* Sul PC vanno in sospeso, come ogni modifica (i file non cambiano), anche per i file fuori
    dalla cartella aperta.
- **Artista e artista dell'album** non si cambiano con *Cambia tag*: sull'iPhone cambiarli rinominerebbe l'artista per
  tutti i suoi brani. Si cambiano nella scheda PC, poi *Rimpiazza*.
- La spunta **Compilation** di *Cambia tag* cambia solo il brano. Una compilation vuole anche l'artista dell'album
  *Artisti vari*: se nell'app Musica i brani non si raccolgono in un solo album, metti spunta e "Artisti vari"
  nella scheda PC e usa *Rimpiazza*, che manda brano e album insieme.
- Si possono aggiornare ed eliminare solo i brani messi sull'iPhone da un computer (iTunes, CopyTrans, questo
  programma), non quelli acquistati o scaricati sul telefono.
- Serve l'iPhone connesso e sbloccato, con la gestione manuale della musica attiva (in *Dispositivi Apple* o in
  iTunes, con l'iPhone attaccato: *Gestisci manualmente musica e video*) e senza *Sincronizza libreria* di Apple Music. Se manca qualcosa il programma
  lo dice e non scrive niente.

**Da dove viene un brano.** Il programma tiene un **registro della provenienza**: per ogni brano dell'iPhone
(il suo identificativo fisso, `sync_id`), il computer e il file da cui viene, con dimensione, data, le modifiche in
sospeso al momento dell'invio e l'**impronta dell'audio**, e come è nata l'associazione (*inviato*, *impronta*,
*regole*, *ai*, *a mano*, *salvato*). Ogni invio lo registra; un'eliminazione toglie la riga. Il registro sta nella
cartella dati (`registro_iphone.json`) e sull'iPhone (`myEasyMP3toIPhone/registro.json`, un file che l'iPhone non
legge): così ogni computer con il programma vede anche le righe degli altri. Alla connessione le due copie si
uniscono (per lo stesso brano vince la più recente) e le righe dei brani che non sono più sull'iPhone si tolgono.
Nella scheda iPhone la colonna **Sorgente** dice da quale file viene ogni brano:

| Sorgente | Significato |
|---|---|
| *questo PC* | un file di questo computer (il suggerimento dice quale, e come è nata l'associazione) |
| il nome di un altro computer | un file di quel computer |
| *nessuna* | messo da un computer, ma non si sa da quale file: un brano *solo sull'iPhone* |
| *file non trovato* | un file di questo computer che non c'è più (spostato o cancellato): il brano **non** viene tolto dall'iPhone |
| *telefono* | acquistato o scaricato sull'iPhone: non si gestisce da un computer |
| *senza file* | un brano "fantasma": è nell'elenco dell'app Musica ma il suo file sull'iPhone non c'è (non si può ascoltare); toglilo con *Elimina dall'iPhone* |

Il menu **Mostra** filtra l'elenco per sorgente (per esempio solo i brani *senza sorgente*). Quando un brano ha la
sorgente, il confronto delle colonne *Sul PC* e *iPhone* usa quel file esatto: un doppione sul PC con gli stessi tag
non prende il suo posto. **Salva su PC** associa ogni brano salvato al suo file nuovo (verificato con l'impronta),
anche quando un file con lo stesso audio c'era già. Tasto destro:

- **Associa sorgente…** (un brano): una tabella dei file della cartella aperta che possono essere la sua sorgente
  (titolo, artista, album, durata, **percorso**, perché), **il più probabile per primo e già selezionato**: basta
  *Associa*. Ordine: prima i file con lo **stesso audio** (impronta; cercati tra tutti i file con durata entro 2
  secondi, anche con un titolo diverso, come nelle compilation), poi titolo, artista e durata simili; se i primi due
  si somigliano troppo **sceglie l'AI** della scansione (se è accesa) e la colonna *Perché* ne riporta il motivo.
  *Scegli un altro file…* prende un file qualsiasi. Se il brano ha già una sorgente, la finestra la mostra e prima di
  sostituirla chiede. Nel registro resta come è nata l'associazione: *impronta*, *regole* o *ai* se si accetta la
  prima proposta, *a mano* se si sceglie un altro file. L'impronta dell'iPhone si legge dal telefono se è connesso
  (o dalla memoria, se è già stata letta).
- **Associa sorgente da una cartella…** (più brani, per esempio un album intero): si sceglie la cartella del PC da cui
  vengono (proposta: quella dove stanno le sorgenti già note dei brani degli stessi album); per ogni brano si cerca il
  file nella cartella e nelle sottocartelle (stesso audio, oppure titolo, artista e durata molto simili) e un
  riepilogo, da confermare, mostra brano → file. I brani **non trovati** sono in rosso e, se lasci la spunta, dopo si
  associano uno alla volta con la finestra di *Associa sorgente* (*Salta* passa al prossimo).
- **Togli sorgente**: il brano torna *senza sorgente*.

**Sorgenti sparite.** Il programma non cancella mai i file del PC: li cancelli tu (per esempio un doppione). Quando
apri una cartella o leggi l'iPhone, i brani dell'iPhone il cui file sul PC non c'è più (*file non trovato*) si
segnalano con un avviso, una volta per sessione, che li elenca e per quelli spuntati offre: **Cerca un'altra
sorgente** (la finestra di *Associa sorgente*, uno alla volta, con per prima la copia con lo stesso audio),
**Lascia senza sorgente** o **Elimina dall'iPhone** (con conferma). Un file su un disco che ora non è collegato non
conta come sparito. Il contrario non succede mai: eliminare un brano dall'iPhone non cambia niente sul PC, e i
doppioni del PC e quelli dell'iPhone si gestiscono in modo del tutto separato.

**Brani fantasma.** A ogni lettura dell'iPhone il programma guarda anche quali file ci sono nelle cartelle della musica
del telefono (una lettura per cartella, non per brano): un brano dell'elenco il cui file non c'è è un *fantasma*.
La colonna *Sorgente* dice *senza file*, la barra di stato li conta, *Mostra → Senza file sull'iPhone* li elenca e
*Controlla la musica* dell'iPhone li segnala tra i file illeggibili. Non si tolgono da soli: tasto destro →
*Elimina dall'iPhone*.

L'**impronta** riassume l'audio e non cambia quando cambiano i tag: per gli MP3 i primi 64 KB dopo il tag ID3, per i
FLAC l'impronta dell'audio che il file porta nella sua intestazione, per gli M4A l'inizio del blocco audio. Così un
brano dell'iPhone si riconosce anche se titolo, album o artista sono diversi da quelli del PC (le compilation, i
brani "sciolti"): su 40 brani messi sull'iPhone da CopyTrans, 40 sono stati ritrovati così sul PC.

**Associa sorgenti** (scheda iPhone) ritrova il file del PC di ogni brano dell'iPhone senza sorgente (messo
da CopyTrans, da un altro computer…) e lo scrive nel registro. Confronta con la cartella aperta nella scheda PC, in
tre livelli:

1. **impronta dell'audio**: stesso audio = stesso brano, qualunque siano titolo, album, artista. Con più copie sul PC
   sceglie quella con i tag più simili. Si associa senza chiedere;
2. **regole**: durata entro 2 secondi e titolo e artista quasi uguali, con un solo candidato chiaramente migliore
   (per esempio un'altra codifica dello stesso brano). Proposto già spuntato;
3. **AI**, per i dubbi veri (per esempio una versione dal vivo e una in studio): riceve per ogni brano dell'iPhone
   al più 5 candidati del PC con titolo, artista, album, durata e **cartella**, e dice quale è la stessa
   registrazione, o nessuno, con la sicurezza e il motivo. Usa il profilo AI della scansione (*Impostazioni →
   Generale*); proposto spuntato solo se l'AI è sicura. Senza AI, i dubbi si mostrano da controllare.

Prima di scrivere mostra tutto: quanti brani sono associati con l'impronta, le proposte con il motivo (da spuntare o
togliere) e quanti brani non hanno un file sul PC: questi restano *solo sull'iPhone* e il programma non li tocca mai
da solo. La prima volta legge l'impronta di ogni brano dall'iPhone, circa un quarto di secondo l'uno (un quarto d'ora
per 3.500 brani); si può annullare e riprendere, quelle già lette si ricordano (`impronte_iphone.json`). Le impronte
dei file del PC si ricordano nella cache dei tag. Né i brani dell'iPhone né i file del PC cambiano.

**Sicurezza.** Prima di scrivere il programma copia il database dell'app Musica e controlla l'identità della libreria
(quella già sul telefono, mai una nuova) e l'"ancora" della sincronizzazione, che l'iPhone deve confermare. Il file
delle operazioni viene firmato, scritto e riletto; solo allora l'iPhone lo applica. Se qualcosa non torna prima di
quel momento, il telefono resta com'era. A ogni sessione l'iPhone chiede anche copertine di brani già presenti: il
programma risponde che non le ha, come fa rustunes, e quei brani restano come sono.

> **Non premere mai "Sincronizza" in iTunes o in Dispositivi Apple** con la musica messa da questo programma o da
> CopyTrans: iTunes la toglierebbe dall'iPhone per sostituirla con la sua libreria, senza chiedere conferma.

Il protocollo non è documentato da Apple: il programma segue la ricostruzione di
[rustunes](https://github.com/fbiba/rustunes) (licenza MIT, vedi `THIRD_PARTY_NOTICES.md`), provata su iOS 26.7 e 27.0
- 27.2.1. Un aggiornamento di iOS può cambiarlo: in quel caso il programma si ferma con un errore invece di scrivere.

**iTunes non serve.** Il programma parla con l'iPhone da solo; basta il driver USB di Apple, che installa l'app
gratuita *Dispositivi Apple* (o iTunes, se c'è già). Il vecchio invio tramite iTunes è stato tolto: con un iPhone
caricato da un altro programma poteva far cancellare la musica del telefono.

## L'AI: profili e chiavi

*Impostazioni → Profili AI*, lo stesso meccanismo di myCalibreTools. Tipi: **Ollama**, **Azure OpenAI**, **OpenAI**,
**Anthropic (Claude)**. *Prova la connessione* manda una richiesta vera e piccola. *Importa da myCalibreTools…* copia i
suoi profili e le sue chiavi (dalla Gestione credenziali, senza mostrarle).

- **Chiave API:** scritta nel campo va nella **Gestione credenziali di Windows** (voci `myEasyMP3toIPhone`), mai in un file;
  senza credential store va in `secrets.json` nella cartella dati. Oppure scrivi **`$NOME`**: la chiave si legge dalla
  variabile d'ambiente `NOME` (dal [file delle variabili](#il-file-delle-variabili-myeasymp3toiphoneenv) o dal sistema) e
  si salva solo il nome. Con `$NOME` senza valore si usa la chiave salvata prima per quel profilo, se c'è.
- **Server/endpoint:** un indirizzo privato scritto nel campo va nella Gestione credenziali; nel file resta
  `(nel credential store)`. Anche qui si può scrivere `$NOME`. Gli indirizzi pubblici (localhost:11434, api.openai.com,
  api.anthropic.com) restano nel file.
- Un valore che inizia davvero con `$` si scrive `$$`.
- **Anthropic:** modello predefinito `claude-opus-5-5`; la temperatura non si invia (i modelli attuali non la
  accettano); la risposta usa l'output strutturato dell'API; sui modelli che lo prevedono è attivo il **fallback lato
  server**: se il modello rifiuta la richiesta, l'API la ripete su un altro modello nella stessa chiamata.
- Una chiave non si vede mai: mascherata nel campo, e *Informazioni* / `--env` dicono solo **dove** è salvata.

## Il file delle variabili (myEasyMP3toIPhone.env)

Un solo file con tutte le variabili d'ambiente che il programma legge:
**`%USERPROFILE%\.myEasyMP3toIPhone\myEasyMP3toIPhone.env`**. Si legge a ogni avvio, comunque il programma sia avviato
(menu Start, collegamento, console): non serve impostare niente in Windows. Al primo avvio viene creato copiando il
modello `myEasyMP3toIPhone.TEMPLATE.env` (distribuito con il programma, nella cartella `_internal\myeasymp3toiphone`), con una
spiegazione in testa e tutte le variabili **vuote**.

### Cosa vuol dire ogni riga

| Riga | Valore usato |
|---|---|
| `NOME=valore` | `valore`, **anche se il sistema ha un altro valore per NOME** |
| `NOME=$ALTRA` | il valore di `ALTRA`: da questo file se qui ne ha uno, altrimenti dal sistema |
| `NOME=` | il valore di `NOME` nel sistema; nessuno se il sistema non ne ha |
| `NOME=$NOME` | come `NOME=` (il valore del sistema), senza avviso |
| `NOME=$$testo` | il testo letterale `$testo` |

Esempio: le tue chiavi sono già nelle variabili di Windows con altri nomi.

```ini
ANTHROPIC_API_KEY=$MIA_CHIAVE_CLAUDE      # usa la variabile di sistema MIA_CHIAVE_CLAUDE
OPENAI_API_KEY=                           # usa OPENAI_API_KEY del sistema, se c'è
OLLAMA_API_BASE=http://192.168.1.20:11434 # vince su quella del sistema
```

(Nel file vero niente commenti in fondo alla riga: qui sono solo per spiegare. Vedi le regole sotto.)

### Regole

- UTF-8, con o senza BOM (il Blocco note può aggiungerlo). Righe vuote e righe che iniziano con `#` si ignorano.
- Una riga è `NOME=valore`, con `NOME` fatto di lettere, cifre e `_` (non inizia con una cifra). Gli spazi intorno al
  valore e una coppia di virgolette uguali intorno si tolgono.
- **Niente commenti in fondo alla riga**: una chiave può contenere `#`. `export NOME=valore` non è valido.
- `$ALTRA` vale solo per il valore **intero**: un `$` dentro un valore è un carattere normale.
- Se un nome compare due volte vale l'ultima riga.
- Tutti i valori si calcolano sulle variabili del sistema **com'erano prima** di leggere il file, poi si impostano
  insieme: l'ordine delle righe non conta. `$ALTRA` può puntare a un'altra riga che a sua volta è `$...`.
- Un valore del sistema si usa così com'è: anche se inizia con `$` non è un riferimento.
- Un ciclo (`A=$B`, `B=$A`) o un riferimento a una variabile senza valore: un avviso nel log, con il solo nome a
  sinistra dell'`=`, e la riga non si usa (resta il valore del sistema, se c'è).
- `MYEASYMP3TOIPHONE_HOME` **non** si può impostare qui (dice dov'è questo file): una riga con un valore viene ignorata con
  un avviso. Si imposta nelle variabili di Windows.
- Gli avvisi nominano numeri di riga o variabili, **mai** quello che è scritto dopo l'`=`: potrebbe essere una chiave.

### Il file si aggiorna da solo

A ogni avvio vengono aggiunti in fondo, **vuoti** e sotto un commento, i nomi del modello e quelli che le tue
Impostazioni nominano (`$NOME` nella chiave o nel server di un profilo) che il file non elenca ancora. Una riga
commentata (`# NOME=...`) conta come elencata. Le righe esistenti non si toccano mai e il programma non scrive mai un
valore. Il nuovo file è leggibile solo dal proprietario.

### Le variabili

| Variabile | A cosa serve | Senza valore |
|---|---|---|
I nomi delle variabili AI sono **gli stessi di myCalibreTools**: se le hai già impostate in Windows per quel programma,
myEasyMP3toIPhone le usa così come sono (lascia vuote le righe del file). Le due variabili proprie del programma seguono lo
stesso schema di nomi: `MYCALIBRETOOLS_HOME` → `MYEASYMP3TOIPHONE_HOME`, `CALIBRE_DEDUP_LOG_LEVEL` →
`MYEASYMP3TOIPHONE_LOG_LEVEL`.

| Variabile | A cosa serve | Senza valore |
|---|---|---|
| `MYEASYMP3TOIPHONE_LOG_LEVEL` | il livello del log: `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` (`DEBUG` con `--debug`) |
| `OLLAMA_API_BASE`, `OLLAMA_API_KEY` | server e chiave dei profili Ollama (come in myCalibreTools) | `http://localhost:11434`, nessuna chiave |
| `OLLAMA_FALLBACK_API_BASE` | un secondo server Ollama (per esempio `https://ollama.com`), per i profili che lo nominano | — |
| `AZURE_FOUNDRY_EP`, `AZURE_FOUNDRY_KEY` | endpoint e chiave dei profili Azure OpenAI / Azure AI Foundry (come in myCalibreTools) | — |
| `OPENAI_API_KEY` | la chiave dei profili OpenAI (nome standard: myCalibreTools non ha profili OpenAI) | — |
| `ANTHROPIC_API_KEY` | la chiave dei profili Anthropic (nome standard: myCalibreTools non ha profili Anthropic) | — |
| `MYCALIBRETOOLS_HOME` | dove cercare i profili di myCalibreTools per *Importa da myCalibreTools* | `%USERPROFILE%\.myCalibreTools` |
| `MYEASYMP3TOIPHONE_HOME` | **solo nel sistema**: un'altra cartella dati (percorso completo) | `%USERPROFILE%\.myEasyMP3toIPhone` |

**Un profilo AI nuovo** (*Impostazioni → Profili AI → Aggiungi*, o cambiando il tipo di un profilo appena aggiunto)
nomina da solo le variabili del suo tipo **che hanno un valore**: per esempio un profilo Azure diventa
`$AZURE_FOUNDRY_EP` / `$AZURE_FOUNDRY_KEY`. Senza valore restano l'indirizzo predefinito e il campo chiave vuoto. I
profili già salvati e quelli importati da myCalibreTools non cambiano: tengono i `$NOME` che hanno.

**Sicurezza:** le chiavi scritte nel file sono in chiaro. Tienilo privato, non condividerlo e non metterlo in git. Se
la cartella dati è sincronizzata (OneDrive…), le chiavi vengono sincronizzate con lei. L'alternativa è scrivere la
chiave nelle Impostazioni (Gestione credenziali di Windows).

## La cartella dati

`%USERPROFILE%\.myEasyMP3toIPhone` (o `MYEASYMP3TOIPHONE_HOME`): tutto quello che il programma conserva, mai nella cartella del
programma. La musica invece sta nella Libreria.

| File | Contenuto |
|---|---|
| `myEasyMP3toIPhone.env` | le variabili d'ambiente (sopra) |
| `settings.json` | cartella della Libreria, ultime cartelle usate, AI della scansione e controlli tolti, lingua, posizione della finestra |
| `ai_profiles.json` | i profili AI (senza chiavi e senza indirizzi privati: quelli sono nella Gestione credenziali) |
| `secrets.json` | solo senza credential store: le chiavi |
| `scansioni\scansione_<data>.txt` | il rapporto di ogni scansione |
| `iphone_musica.json` | la musica dell'app Musica dell'iPhone all'ultima connessione (tag, durata, file sul telefono), per la scheda iPhone, la colonna *iPhone* e la scansione a telefono disconnesso |
| `iphone_in_attesa.json` | le modifiche all'iPhone in attesa (spunte della colonna *iPhone*): da inviare, togliere o aggiornare, per percorso del file del PC |
| `registro_iphone.json` | il registro della provenienza: per ogni brano dell'iPhone, il computer e il file da cui viene (vedi *Da dove viene un brano*); una copia sta sull'iPhone |
| `impronte_iphone.json` | le impronte dell'audio dei file dell'iPhone già lette, per non rileggerle |
| `itunes_aggiunti.json` | della versione 0.1.1 (invio tramite iTunes): non più usato, si può cancellare |
| `iphone_files.json`, `iphone_inviati.json` | delle versioni precedenti (invio alle app come VLC): non più usati, si possono cancellare |
| `cache_tag.json` | i tag già letti di ogni file (con dimensione e data), per riaprire in fretta le cartelle grandi; si può cancellare |
| `modifiche_tag.json`, `copertine\` | le modifiche dei tag in sospeso, per percorso del file, e le copertine nuove: i file sul PC non cambiano |
| `crash.log`, `myEasyMP3toIPhone.output.log` | solo se qualcosa va storto: la traccia di un arresto improvviso e quello che il programma avrebbe scritto su una console (la finestra non ne ha) |
| `myEasyMP3toIPhone.log` | cosa è successo, comprese le richieste all'AI (a rotazione: 5 MB, 3 file vecchi) |
| `myEasyMP3toIPhone.home.txt` | versione e formato dei dati dell'ultimo programma avviato su questa cartella |
| `Backup\` | le copie di questa cartella fatte prima che una nuova versione ne cambi il formato; il programma non le cancella mai |

Al primo avvio le impostazioni della prima versione (CopiaStiMP3, nel registro di Windows) vengono copiate in
`settings.json`.

**Dal nome precedente (myCopiaStiMP3).** Al primo avvio con il nome nuovo, dopo la copia di sicurezza (vedi sotto):
la cartella `%USERPROFILE%\.myCopiaStiMP3` diventa `%USERPROFILE%\.myEasyMP3toIPhone` (se la versione vecchia è ancora
aperta, si usa quella vecchia e si riprova al prossimo avvio); `myCopiaStiMP3.env` diventa `myEasyMP3toIPhone.env`, con
le variabili `MYCOPIASTIMP3_…` rinominate `MYEASYMP3TOIPHONE_…`; le chiavi salvate nella Gestione credenziali passano
dalle voci `myCopiaStiMP3` a `myEasyMP3toIPhone`; la Libreria resta dov'è (`Musica\myCopiaStiMP3`, ora scritta in
`settings.json`). Una variabile di sistema `MYCOPIASTIMP3_HOME` non vale più: va rinominata `MYEASYMP3TOIPHONE_HOME`.

### Tornare a una versione precedente

Quando una nuova versione cambia il formato dei dati, prima di toccare qualsiasi file copia la cartella dati in
`Backup\myEasyMP3toIPhone-home-for-<versione>-<data>.zip`, dove `<versione>` è **la versione da usare con quella copia**.
Per tornare indietro: installa quella versione (gli zip delle versioni sono in `MY_VSCODE_ZIP_DIR\myEasyMP3toIPhone`),
chiudi il programma, svuota la cartella dati tranne `Backup` e scompatta lì la copia. Se la copia non si può fare, il
programma si ferma senza cambiare niente. Per tornare a una versione con il nome precedente (myCopiaStiMP3, zip in
`MY_VSCODE_ZIP_DIR\myCopiaStiMP3`), scompatta la copia in `%USERPROFILE%\.myCopiaStiMP3` e rinomina
`myEasyMP3toIPhone.home.txt` in `myCopiaStiMP3.home.txt`.

## Quale valore vince

Letto dal codice: **aggiornare questa sezione nello stesso commit di una nuova impostazione, opzione o variabile, o di
un ordine di precedenza cambiato.**

### La cartella dati

1. `MYEASYMP3TOIPHONE_HOME` nelle variabili **del sistema**, se è un percorso completo (`~\` all'inizio e `%NOME%` /
   `$NOME` dentro si espandono). Un valore che non è un percorso completo si ignora, con un avviso nel log.
2. Altrimenti `%USERPROFILE%\.myEasyMP3toIPhone`.

Il file delle variabili non può sceglierla: sta dentro la cartella dati.

### Le variabili d'ambiente

1. Una riga con un valore nel file delle variabili (anche `$ALTRA` risolta) **vince** sul sistema.
2. Una riga vuota, `NOME=$NOME`, una riga non valida, un ciclo o un riferimento senza valore: vale il sistema.
3. Senza nessuno dei due: il comportamento "senza valore" della tabella delle variabili.

Il programma legge le variabili all'avvio: dopo un cambio va riavviato (anche VS Code, per un programma avviato da lì).
*Informazioni* mostra per ogni variabile il valore usato e *(file)* o *(sistema)*; per le chiavi e le password (nomi
con KEY, PASSWORD, SECRET, TOKEN, CREDENTIAL, o nominate dalla chiave di un profilo) solo *impostata*. `--env` mostra
solo `impostata (file)`, `impostata (sistema)` o `N/A`, mai un valore.

### La chiave API di un profilo

1. La variabile nominata con `$NOME`, se ha un valore.
2. Altrimenti la chiave salvata nelle Impostazioni per quel profilo (Gestione credenziali di Windows, o `secrets.json`
   senza credential store).
3. Altrimenti nessuna chiave: Ollama locale non ne chiede, gli altri tipi danno errore.

Un profilo nuovo parte con `$OLLAMA_API_KEY`, `$AZURE_FOUNDRY_KEY`, `$OPENAI_API_KEY` o `$ANTHROPIC_API_KEY` secondo il
tipo, solo se quella variabile ha un valore quando lo aggiungi; altrimenti con il campo vuoto.

### Il server di un profilo

`$NOME` → il valore della variabile (nessun server se è vuota); un indirizzo privato scritto → quello salvato nella
Gestione credenziali; un indirizzo pubblico → quello scritto nel file. OpenAI e Anthropic usano sempre il loro
indirizzo. Un profilo nuovo Ollama o Azure parte con `$OLLAMA_API_BASE` o `$AZURE_FOUNDRY_EP` se quella variabile ha un
valore, altrimenti con `http://localhost:11434` o un endpoint di esempio da completare. Il profilo "Ollama locale"
creato al primo avvio usa sempre `http://localhost:11434`, anche se `OLLAMA_API_BASE` ha un valore: la scansione
predefinita resta su questo computer.

### L'invio all'app Musica

- L'invio diretto (tasto destro → *Invia all'iPhone*) non ha impostazioni: l'identità della libreria e l'ancora
  vengono sempre dall'iPhone (`iTunesPrefs` e il database dell'app Musica); il nome del computer che l'iPhone registra
  è quello di Windows.
- Il vecchio invio tramite iTunes è stato tolto, con le sue impostazioni `itunes_dir` e `itunes_sync`: in un
  `settings.json` vecchio restano scritte ma non si leggono più.

### L'AI della scansione

1. Il profilo scelto in *Impostazioni → Generale → AI della scansione* (salvato in `settings.json`); *(nessuna)* = solo
   le regole. La casella *Usa l'AI* della finestra *Controlla la musica* vale per quel controllo ed è ricordata per
   la prossima.
2. Al primo avvio senza profili: "Ollama locale", creato e scelto automaticamente (vedi
   [Controlla la musica](#controlla-la-musica)).
   Se cancelli tutti i profili non viene ricreato.
3. In console `--ai "<profilo>"` vale solo per quella scansione e non si salva; senza, la console usa solo le regole.

### I controlli di "Controlla la musica"

1. Le caselle della finestra: valgono per quel controllo; quelle tolte si ricordano in `settings.json`
   (`scan_checks_off`), così un controllo nuovo di una versione futura parte acceso.
2. Al primo uso, e con un `settings.json` senza `scan_checks_off`: tutti i controlli.

La casella *…e i nomi dubbi anche su MusicBrainz* (sotto *Artisti scritti in modi diversi*) si ricorda in `settings.json`
(`scan_musicbrainz`); al primo uso è spenta. In console MusicBrainz non si usa.
3. In console `--scan`: sempre tutti i controlli.

*File che non si aggiornano* sui file del PC si controlla solo per la cartella aperta, non per l'iPhone.

### La cartella della Libreria

`settings.json` (*Impostazioni → Generale*); senza valore `%USERPROFILE%\Music\myEasyMP3toIPhone`. Le impostazioni della
prima versione nel registro di Windows si copiano una volta, solo se `settings.json` non esiste.

### La lingua dell'interfaccia

1. *Impostazioni → Generale → Lingua dell'interfaccia* (`language` in `settings.json`: `it` o `en`), dal prossimo avvio.
2. Senza: italiano.

In inglese sono in inglese finestre, pulsanti, menu, messaggi, la barra di stato, i problemi e il rapporto di *Controlla la musica* e i motivi scritti dall'AI (il prompt le chiede l'inglese). Restano come sono i dati (titoli, artisti, album, percorsi), la console e questo README. Il codice resta scritto in italiano: i testi si traducono quando arrivano allo schermo con il catalogo `myeasymp3toiphone/i18n_en.py` (un testo nuovo nel codice va aggiunto lì: `tools/i18n_catalog.py` elenca quelli mancanti e un test lo controlla).

### La cartella aperta all'avvio

1. `--open <cartella>` sulla riga di comando (vale per quell'avvio, non si salva come scelta: ma quella cartella
   diventa l'ultima usata).
2. Altrimenti **l'ultima cartella usata** (`last_opened` in `settings.json`): quella aperta con *Apri cartella* o la
   Libreria, salvata ogni volta che una cartella finisce di caricarsi.
3. Se l'ultima cartella non è più disponibile (disco scollegato, cartella cancellata): la Libreria, con un avviso
   nella barra di stato.
4. Senza Libreria: nessuna cartella, con l'invito ad aprirne una.

La finestra *Apri cartella* parte invece da `last_folder`, l'ultima cartella scelta lì.

### Opzioni della finestra (`myEasyMP3toIPhone`)

| Opzione | Effetto | Salvata? |
|---|---|---|
| `--open <cartella>` | apre quella cartella all'avvio, al posto della Libreria (in sola lettura) | no |
| `--debug` | il log a livello DEBUG, se `MYEASYMP3TOIPHONE_LOG_LEVEL` non dice altro | no |

### Opzioni della console (`myEasyMP3toIPhone-cli`)

| Opzione | Effetto | Salvata? |
|---|---|---|
| `--version` | stampa la versione, senza toccare la cartella dati | — |
| `--env` | le variabili e dove sono le chiavi, mai un valore | — |
| `--scan <cartella>` | scansione con le sole regole; il rapporto va anche in `scansioni\` | no |
| `--ai "<profilo>"` | con `--scan`: anche l'AI, con quel profilo | no |
| `--selftest` | carica tutte le librerie (controllo di una build), senza toccare la cartella dati | — |
| `--debug` | il log a livello DEBUG, se `MYEASYMP3TOIPHONE_LOG_LEVEL` non dice altro (vale anche per la finestra) | no |

### Variabili della build

`MY_VSCODE_ZIP_DIR` e `MY_VSCODE_INSTALL_DIR` (vedi sotto): `build_dist.py` le legge dal file delle variabili e dal
sistema con le stesse regole; `vscode_deploy.py` eseguito da solo legge **solo il sistema**. Compaiono in `--env` solo
quando il programma gira dai sorgenti.

## Sviluppo e build

```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt -r requirements_build.txt
.venv\Scripts\python main.py              (la finestra; oppure avvia.bat)
.venv\Scripts\python main.py --cli --env  (la console)
.venv\Scripts\python -m pytest            (i test: mai la cartella dati vera, mai le chiavi vere)
.venv\Scripts\python build_dist.py        (la build; in VS Code: Ctrl+Shift+B)
```

**La versione** viene da git: `0.1.<numero di commit> (<data>)`, oppure `-dev` con modifiche non registrate. La build
richiede quindi il repository git.

**La build** (`build_dist.py`, PyInstaller con `myEasyMP3toIPhone.spec`) crea `dist\myEasyMP3toIPhone\` con
`myEasyMP3toIPhone.exe` (la finestra), `myEasyMP3toIPhone-cli.exe` (la console), `_internal\`, README.md, LICENSE e i file di
`dist_files` (READ ME FIRST.txt, Create/Remove shortcuts.cmd); controlla la build con `myEasyMP3toIPhone-cli --selftest`;
poi crea `dist\myEasyMP3toIPhone-<versione>-windows-x64.zip` (degli zip vecchi in dist resta solo quello precedente).
Infine `vscode_deploy.py`:

- copia lo zip in `MY_VSCODE_ZIP_DIR\myEasyMP3toIPhone\`;
- installa la build in `MY_VSCODE_INSTALL_DIR\myEasyMP3toIPhone\`: la versione installata diventa `myEasyMP3toIPhone.previous`,
  si scompatta la nuova (se non riesce, per esempio perché il programma è aperto, la vecchia torna al suo posto);
- se la versione sostituita non ha uno zip in `MY_VSCODE_ZIP_DIR`, lo crea; poi cancella `.previous`. Una cartella che
  non si riesce a cancellare diventa `myEasyMP3toIPhone.previous.<versione>.TODELETE`, da cancellare a mano;
- una variabile non impostata salta il suo passo, con un avviso alla fine.

L'icona si rigenera con `.venv\Scripts\python tools\make_icon.py`.

| File | Contenuto |
|---|---|
| `myeasymp3toiphone/tags.py` | lettura e scrittura dei tag e delle copertine (mutagen), ID3 v2.3 |
| `myeasymp3toiphone/library.py` | scansione delle cartelle, raggruppamento, nomi dei file, copia e spostamento |
| `myeasymp3toiphone/albumcheck.py` | MusicBrainz e Cover Art Archive, abbinamento delle tracce |
| `myeasymp3toiphone/scan.py` | *Controlla la musica*: regole, brani duplicati, confronto con l'iPhone, analisi AI, correzioni |
| `myeasymp3toiphone/artist_names.py` | le forme dei nomi d'artista: varianti certe, dubbi (AI, MusicBrainz), duetti |
| `myeasymp3toiphone/overlay.py`, `tag_cache.py` | le modifiche dei tag in sospeso; la cache dei tag e delle impronte |
| `myeasymp3toiphone/ai.py` | i fornitori di AI (Ollama, Azure, OpenAI via HTTP; Anthropic con l'SDK ufficiale) |
| `myeasymp3toiphone/iphone.py` | l'iPhone (pymobiledevice3): connessione, musica dell'app Musica, file, brani fantasma |
| `myeasymp3toiphone/phone_sync.py` | il protocollo di sincronizzazione di Apple (AirTrafficControl) per scrivere nell'app Musica |
| `myeasymp3toiphone/phone_actions.py` | invia, rimpiazza, cambia tag, elimina sull'iPhone |
| `myeasymp3toiphone/phone_library.py` | il database dell'app Musica, l'elenco salvato, il confronto con il PC |
| `myeasymp3toiphone/provenance.py`, `adoption.py` | impronte dell'audio, registro della provenienza, *Associa sorgente/i* |
| `myeasymp3toiphone/pending.py` | le modifiche all'iPhone in attesa (spunte della colonna *iPhone*) |
| `myeasymp3toiphone/i18n.py`, `i18n_en.py` | la lingua dell'interfaccia: la traduzione inglese dei testi e gli agganci a Qt |
| `myeasymp3toiphone/config.py` | cartella dati, impostazioni, profili AI, chiavi, `$NOME` |
| `myeasymp3toiphone/env_file.py` | il file delle variabili |
| `myeasymp3toiphone/environment.py` | il rapporto delle variabili (`--env`, *Informazioni*) |
| `myeasymp3toiphone/home_backup.py` | la copia della cartella dati prima di un cambio di formato |
| `myeasymp3toiphone/startup.py` | l'avvio: copia, variabili, migrazioni, registro, log |
| `myeasymp3toiphone/gui/` | l'interfaccia PySide6 (la tabella dei brani è un modello Qt, `track_model.py`: veloce anche con decine di migliaia di brani) |
