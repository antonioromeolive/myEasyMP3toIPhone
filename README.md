# myEasyMP3toIPhone

Programma per Windows per organizzare la musica, modificarne i tag, controllare che gli album siano completi,
trovare i problemi della libreria (anche con l'AI) e trasferire la musica da e verso l'iPhone.

- [Installazione](#installazione)
- [Funzioni](#funzioni)
- [La scansione](#la-scansione)
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
| **Scansione** | cerca i problemi della cartella aperta o della musica sull'iPhone (vedi sotto) |
| **Impostazioni** | cartella della Libreria, AI della scansione, profili AI |
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
  elenchi, la tabella, *Esporta*, *Verifica album*, la *Scansione* della cartella e l'invio all'app Musica.

La tabella dei brani si ordina cliccando sull'intestazione di una colonna (Artista, Album, Titolo, Anno…); finché non
la clicchi i brani sono in ordine di artista, album, disco e traccia. *Esporta*, *Verifica album* e *Invia all'app Musica*
senza brani selezionati in tabella usano l'artista o l'album scelti negli elenchi.

Artisti e album che differiscono solo per maiuscole, accenti o spazi ("Queen" e "queen") sono un gruppo solo, mostrato
con la grafia più usata (a parità, quella con le maiuscole). I tag dei file non cambiano: la scansione segnala la
variante, perché l'iPhone la considera un artista diverso.

**Colonna iPhone.** Per ogni brano: **✔** nell'app *Musica* dell'iPhone c'è lo stesso brano, con gli stessi tag;
**⟳** c'è lo stesso brano, ma con tag diversi (il suggerimento elenca le differenze, *sul PC* / *sull'iPhone*); vuoto,
non c'è. "Lo stesso brano" vuol dire stesso titolo e stesso album, senza badare a maiuscole, accenti e spazi, e un
artista in comune; un brano con modifiche in sospeso si ritrova anche con i tag del file. Si basa sulla musica
dell'iPhone letta all'ultimo collegamento e salvata nella cartella dati, quindi si vede anche a iPhone scollegato (il
suggerimento sull'intestazione dice di quando è l'elenco).

**Tag.** A destra si modificano titolo, artista, artista album, album, numero di traccia e di disco, anno, genere e
copertina (MP3, M4A, FLAC, OGG, Opus; copertina per MP3, M4A, FLAC). Con più brani selezionati, solo i campi
modificati valgono per tutti. *Numera in ordine* assegna 1, 2, 3… nell'ordine della tabella. *Salva modifiche* **non
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

## La scansione

*Scansione* (F6) analizza la cartella aperta, oppure la musica dell'app *Musica* dell'iPhone confrontata con la
Libreria (si può fare anche a iPhone scollegato, con l'ultimo elenco letto). Prima
applica delle regole locali, veloci e gratuite; poi, se scegli di usarla, l'AI. Il rapporto resta in
`.myEasyMP3toIPhone\scansioni\`. Ogni problema può avere una **correzione**: si applica dalla finestra dei risultati, dopo
una conferma, come **modifiche in sospeso** (i file sul PC non cambiano; vanno sulle copie inviate all'iPhone); *Mostra
i brani* li seleziona nella scheda PC. I problemi trovati sull'iPhone non hanno correzioni automatiche: si correggono i
brani sul PC e poi si usa *Rimpiazza*, o si cambiano dalla scheda iPhone (tasto destro).

| Sintomo | Cosa cerca | Correzione |
|---|---|---|
| **File che non si aggiornano** | sull'iPhone, brani con tag diversi da quelli del PC (o delle modifiche in sospeso); MP3 con un vecchio tag ID3v1 diverso o con un tag APE (solo informazione: le copie inviate ne sono ripulite) | sull'iPhone nessuna (la colonna *iPhone* della scheda PC mostra le differenze) |
| **Album con pochi brani** | numeri di traccia mancanti, meno brani del totale dichiarato, album di 1-2 brani; sull'iPhone, album con meno brani che sul PC | (Verifica album trova i titoli mancanti) |
| **Collezioni divise su più album** | una cartella con brani in album diversi; lo stesso album scritto in modi diversi o con "CD 1"/"Disc 2" nel nome; una compilation senza *Artista album*; lo stesso artista scritto in modi diversi | unifica album e artista album ("Artisti vari" per le compilation), sposta il numero del disco in *N. disco* |
| **Solo sull'iPhone** | brani dell'app Musica senza un brano uguale (artista, album, titolo) nella Libreria del PC | nessuna: salvali sul PC dalla scheda iPhone (tasto destro → *Salva su PC*) |
| **Brani doppi** | solo **dentro lo stesso album**: una copia "Titolo (2)" con lo stesso album, lo stesso brano (numero e titolo) due volte nell'album. Lo stesso brano in album diversi (l'album originale e una raccolta) è legittimo e non si segnala | nessuna automatica: quale copia tenere lo decidi tu (*Mostra i brani*) |
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

**Basta collegare l'iPhone con il cavo:** il programma lo rileva da solo (controlla ogni 3 secondi) e si collega. La
prima volta l'iPhone chiede **"Autorizzare questo computer?"**: tocca *Autorizza* e inserisci il codice. La scheda
**iPhone** e la barra di stato dicono a che punto è; se il collegamento automatico non riesce (iPhone bloccato,
autorizzazione negata) lo dice lì, e *Collega iPhone* riprova. Senza il driver Apple la scheda dice di installare
*Dispositivi Apple*. Scollegando l'iPhone la scheda lo segna come scollegato.

**La musica dell'app Musica.** Collegato l'iPhone, la scheda **iPhone** mostra i brani dell'app *Musica* con i
titoli, gli artisti e gli album che mostra l'app: il programma ne copia sul PC il database (`MediaLibrary.sqlitedb`)
e lo legge, perché sul telefono i file hanno nomi casuali (`F12/ABCD.mp3`). Sono solo i brani con un file
sull'iPhone, non quelli in streaming da Apple Music. *Cerca* filtra per titolo, artista o album.

- **Sul PC:** ✔ nella cartella aperta nella scheda PC c'è lo stesso brano, con gli stessi tag; ⟳ c'è, con tag diversi
  (il suggerimento dice quali); vuoto, non c'è. Lo stesso confronto della colonna *iPhone* della scheda PC.
- **Tasto destro** su uno o più brani: **Salva su PC…** copia i file in una cartella a scelta (proposta: la Libreria),
  ordinati in `Artista/Album (Anno)/NN - Titolo` con i nomi che mostra l'app; crea solo file nuovi, un file già
  presente sul PC non viene mai sostituito. **Mostra nella scheda PC** seleziona i brani corrispondenti del PC.
- L'elenco letto resta in `iphone_musica.json` nella cartella dati: scheda iPhone, colonna *iPhone* e scansione
  funzionano anche a telefono scollegato (*Aggiorna elenco* lo rilegge).

### Scrivere nell'app Musica

Il programma scrive nella musica dell'app Musica con lo stesso servizio di sincronizzazione di Apple che usano iTunes e
CopyTrans Manager (*AirTrafficControl*), senza iTunes e senza sincronizzare tutto: ogni volta manda solo le modifiche
("Delta"), mai una sostituzione completa.

| Dove | Tasto destro | Cosa fa |
|---|---|---|
| Scheda **PC** | **Invia all'iPhone** | i brani selezionati che non sono sull'iPhone: una copia con i tag e la copertina modificati (i file del PC non cambiano) |
| Scheda **PC** | **Rimpiazza sull'iPhone** | i brani selezionati che sull'iPhone hanno tag diversi (⟳): vedi *Rimpiazza* qui sotto |
| Scheda **iPhone** | **Rimpiazza con la versione del PC** | lo stesso, partendo dai brani dell'iPhone |
| Scheda **iPhone** | **Cambia tag…** | titolo (un brano alla volta), album, genere, anno, numero di traccia e di disco; un campo vuoto non cambia, 0 svuota anno o numero |
| Scheda **iPhone** | **Elimina dall'iPhone…** | toglie i brani dall'app Musica; l'iPhone cancella i loro file da solo, entro qualche minuto |

- **L'app Musica non si aggiorna da sola** se è aperta durante l'invio: chiudila del tutto (scorri via la sua scheda)
  e riaprila; i brani si trovano nella tua libreria (*Libreria → Artisti* o *Brani*), non cercando in Apple Music.
- **Formati:** MP3, FLAC (l'iPhone li suona così come sono) e M4A in AAC. Gli M4A in Apple Lossless non ancora.
- **Copertine:** quella modificata, o altrimenti quella del file, se è JPEG o PNG.
- **Album e artisti:** un brano va nell'album e nell'artista già presenti sull'iPhone con lo stesso nome (senza badare
  a maiuscole, accenti e spazi), con la grafia dell'iPhone: niente doppioni.
- **Rimpiazza** prima invia la versione del PC, poi toglie quella vecchia, solo se l'invio è riuscito. Il brano
  rimpiazzato perde il conteggio degli ascolti e la presenza nelle playlist fatte sull'iPhone.
- **Artista e artista dell'album** non si cambiano con *Cambia tag*: sull'iPhone cambiarli rinominerebbe l'artista per
  tutti i suoi brani. Si cambiano nella scheda PC, poi *Rimpiazza*.
- Si possono aggiornare ed eliminare solo i brani messi sull'iPhone da un computer (iTunes, CopyTrans, questo
  programma), non quelli acquistati o scaricati sul telefono.
- Serve l'iPhone collegato e sbloccato, con la gestione manuale della musica attiva (in iTunes: *Riepilogo →
  Gestisci manualmente musica e video*) e senza *Sincronizza libreria* di Apple Music. Se manca qualcosa il programma
  lo dice e non scrive niente.

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

Il vecchio invio tramite iTunes (riquadro *Invio all'app Musica dell'iPhone (tramite iTunes)*) non è più nella scheda
iPhone: con un iPhone caricato da un altro programma poteva far cancellare la musica del telefono.

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
| `settings.json` | cartella della Libreria, ultime cartelle usate, AI della scansione, posizione della finestra |
| `ai_profiles.json` | i profili AI (senza chiavi e senza indirizzi privati: quelli sono nella Gestione credenziali) |
| `secrets.json` | solo senza credential store: le chiavi |
| `scansioni\scansione_<data>.txt` | il rapporto di ogni scansione |
| `iphone_musica.json` | la musica dell'app Musica dell'iPhone all'ultimo collegamento (tag, durata, file sul telefono), per la scheda iPhone, la colonna *iPhone* e la scansione a telefono scollegato |
| `itunes_aggiunti.json` | per ogni file inviato a iTunes: la sua copia, le modifiche applicate e il brano di iTunes (ID permanente) |
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
dalle voci `myCopiaStiMP3` a `myEasyMP3toIPhone`; la Libreria e la cartella delle copie per iTunes restano dove sono
(`Musica\myCopiaStiMP3…`, ora scritte in `settings.json`); la playlist di iTunes `myCopiaStiMP3` si rinomina al primo
invio. Una variabile di sistema `MYCOPIASTIMP3_HOME` non vale più: va rinominata `MYEASYMP3TOIPHONE_HOME`.

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
- Il vecchio invio tramite iTunes non è più nella scheda iPhone. Le sue impostazioni restano in `settings.json` ma non
  si usano: `itunes_dir` (*Impostazioni → Generale → Cartella delle copie per iTunes*; senza valore
  `%USERPROFILE%\Music\myEasyMP3toIPhone per iTunes`) e `itunes_sync` (predefinito sì).

### L'AI della scansione

1. Il profilo scelto in *Impostazioni → Generale → AI della scansione* (salvato in `settings.json`); *(nessuna)* = solo
   le regole. La casella *Usa l'AI* della finestra Scansione vale per quella scansione ed è ricordata per la prossima.
2. Al primo avvio senza profili: "Ollama locale", creato e scelto automaticamente (vedi [La scansione](#la-scansione)).
   Se cancelli tutti i profili non viene ricreato.
3. In console `--ai "<profilo>"` vale solo per quella scansione e non si salva; senza, la console usa solo le regole.

### La cartella della Libreria

`settings.json` (*Impostazioni → Generale*); senza valore `%USERPROFILE%\Music\myEasyMP3toIPhone`. Le impostazioni della
prima versione nel registro di Windows si copiano una volta, solo se `settings.json` non esiste.

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
| `myeasymp3toiphone/scan.py` | la scansione: regole, confronto con l'iPhone, analisi AI, correzioni |
| `myeasymp3toiphone/ai.py` | i fornitori di AI (Ollama, Azure, OpenAI via HTTP; Anthropic con l'SDK ufficiale) |
| `myeasymp3toiphone/iphone.py` | l'iPhone (pymobiledevice3: AFC e house_arrest) |
| `myeasymp3toiphone/config.py` | cartella dati, impostazioni, profili AI, chiavi, `$NOME` |
| `myeasymp3toiphone/env_file.py` | il file delle variabili |
| `myeasymp3toiphone/environment.py` | il rapporto delle variabili (`--env`, *Informazioni*) |
| `myeasymp3toiphone/home_backup.py` | la copia della cartella dati prima di un cambio di formato |
| `myeasymp3toiphone/startup.py` | l'avvio: copia, variabili, migrazioni, registro, log |
| `myeasymp3toiphone/gui/` | l'interfaccia PySide6 |
