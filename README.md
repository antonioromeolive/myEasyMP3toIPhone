# myEasyMP3toIPhone

Programma per Windows per organizzare la musica, modificarne i tag, controllare che gli album siano completi,
trovare i problemi della libreria (anche con l'AI) e trasferire la musica da e verso l'iPhone.

- [Installazione](#installazione)
- [Funzioni](#funzioni)
- [Controlla la musica](#controlla-la-musica)
- [Verifica album online](#verifica-album-online)
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

> **I file sul PC cambiano solo se lo approvi.** Il programma non sposta e non cancella mai i file delle cartelle che
> apri (compresa la Libreria). Le modifiche dei tag, fatte a mano, dalla scansione o da *Verifica album online*, restano
> **in sospeso** nella cartella dati e valgono per le **copie**: quelle inviate all'iPhone, esportate o importate.
> L'unica scrittura in un file del PC è **Usa i tag da iPhone a PC** (scheda iPhone), dopo una finestra
> che elenca ogni file e ogni campo che cambia (*Modifica N file*; non si può annullare). In cima, una casella per
> campo con quanti file cambia: si scrivono solo i campi lasciati accesi (per esempio solo *Artista album*, perché
> una correzione fatta sul PC in un altro campo non torni al valore vecchio dell'iPhone).
>
> **PC e iPhone non si allineano da soli.** Cancellare o cambiare un brano sull'iPhone non cambia niente sul PC, e
> cambiare i tag sul PC non cambia niente sull'iPhone: la differenza si vede (⟳, il nome del file in giallo) e il
> brano resta associato alla sua sorgente. Per allinearli scegli tu la direzione: **Usa i tag da PC a iPhone** o
> **Usa i tag da iPhone a PC** (tasto destro), oppure, mentre cambi i tag, la casella **Anche sull'iPhone** (editor
> della scheda PC) o **Anche sul PC** (*Cambia i tag* della scheda iPhone, solo come modifiche in sospeso): sono
> spente di serie e niente si allinea senza che tu lo chieda.
>
> **Tutto ciò che cambia l'iPhone va in attesa** e parte solo con **Applica** (vedi
> [Le azioni in attesa](#le-azioni-in-attesa-e-applica)).

Tre linguette: **PC** (i brani delle cartelle aperte), **iPhone** (la musica dell'app *Musica* dell'iPhone, vedi
[L'iPhone](#liphone)) e **Controlli** (*Controlla la musica* e *Verifica album online*, con i loro risultati: vedi
[Controlla la musica](#controlla-la-musica) e [Verifica album online](#verifica-album-online)).

| Pulsante | Cosa fa |
|---|---|
| **La mia musica** (Ctrl+L) | mostra insieme tutte le **cartelle della musica** di questo PC (*Impostazioni → Cartelle della musica*; una di loro è la **Libreria**, predefinita `Musica\myEasyMP3toIPhone`) |
| **Apri cartella…** | mostra i brani di una cartella qualsiasi, in sola lettura (da riga di comando: `myEasyMP3toIPhone --open <cartella>`) |
| **Importa nella Libreria…** | copia una cartella nella Libreria in `Artista / Album (Anno) / NN - Titolo.ext`, con le modifiche in sospeso applicate alle copie |
| **Esporta…** | copia i brani selezionati (o quelli dell'artista o dell'album scelti negli elenchi) in una cartella, con la stessa struttura e le modifiche in sospeso |
| **Impostazioni** | **cartelle della musica** di questo PC (e quale è la Libreria), AI della scansione, **lingua dell'interfaccia** (italiano o inglese), profili AI |
| **Informazioni** | versione, cartella dati, variabili d'ambiente e da dove viene ciascuna, dove sono le chiavi |

**Le cartelle della musica.** La musica non deve stare tutta in una cartella: in *Impostazioni → Cartelle della
musica* si elencano le cartelle di **questo computer** (per esempio `D:\Musica`, `E:\Archivio FLAC`), in ordine, e
una è segnata **Libreria** (dove vanno *Importa cartella* e *Copia da iPhone a PC*). Valgono per il nome del computer:
con la cartella dati condivisa tra due PC ognuno ha le sue, e quelle degli altri si vedono in grigio ma non si usano.
Nella scheda PC la scelta **Cartelle** mostra **tutte le cartelle della musica** insieme (come *La mia musica*), una
sola, la cartella aperta con *Apri cartella* o **Apri un'altra cartella…**. *Associa sorgenti* può cercare in tutte;
tra due copie dello stesso brano vince quella nella cartella più in alto. Togliere una cartella dall'elenco non
cancella niente; togliendo la Libreria diventa Libreria la prima cartella che resta (l'ultima non si toglie). La
prima volta l'elenco ha solo la Libreria di prima. Una cartella aperta con *Apri cartella* (riaperta all'avvio) non
fa parte dell'elenco: quando non c'è, la scheda lo dice e **Aggiungi la cartella aperta** la aggiunge. Sotto,
**Cartelle escluse**: sottocartelle da non usare (per esempio le suonerie dentro la cartella della musica), le stesse
di *Nascondi la cartella* (vedi sotto).

**Elenchi Artisti e Album (i filtri).** Sopra la tabella dei brani due elenchi affiancati, ognuno ordinabile cliccando
sull'intestazione:

- **Artisti** (artista, numero di album, numero di brani): sceglierne uno (o più, con Ctrl/Maiusc) filtra l'elenco
  Album sui suoi album e la tabella sui suoi brani;
- **Album** (album, artista, anno, brani; l'icona dice l'esito di *Verifica album online*): sceglierne uno (o più) mostra
  solo quei brani; con un album solo scelto e nessun brano selezionato in tabella, a destra compaiono la sua
  copertina e il suo nome (quella del primo dei suoi brani che ne ha una);
- la riga **(Tutti …)**, sempre in cima, toglie il filtro; scegliere un artista (o "(Tutti)") azzera l'album scelto
  prima; la casella *Cerca* filtra ancora dentro la scelta;
- **tasto destro** su un artista o un album (anche più righe scelte, o "(Tutti …)"): la riga diventa la scelta e il
  comando vale per **tutti i suoi brani** (artista o album interi, anche quelli che *Cerca* nasconde), con le stesse
  voci del tasto destro sui brani; tutte vanno **in attesa** fino ad *Applica*, anche a iPhone scollegato:
  - **Copia N brani (K album) da PC a iPhone**: i brani che non ci sono;
  - **Ricopia da PC a iPhone**: i brani ⟳ con la sorgente certa (registro) prendono il file del PC (perdono ascolti
    e playlist);
  - **Usa i tag da PC a iPhone**: solo i tag dei brani ⟳ con la sorgente certa (dove basta si cambiano i tag e
    restano ascolti e playlist; per artista e artista dell'album il brano si ricopia);
  - **Elimina N brani dall'iPhone**: i brani che ci sono con la sorgente certa. I file del PC non cambiano.
  I brani abbinati solo per i tag (≈) non si toccano: il menu li conta e invita ad associarli prima; quelli già in
  attesa si contano a parte;
- gli stessi due elenchi ci sono anche nella scheda iPhone, sopra i brani, con le voci del tasto destro sui brani
  dell'iPhone (vedi [L'iPhone](#liphone));
- **Formato** (accanto a *Cerca*): solo MP3, FLAC, M4A, OGG/Opus o WMA/WAV/AIFF, con il numero di brani di
  ciascuno. Vale per gli elenchi, la tabella, *Esporta*, *Verifica album online*, *Controlla la musica* e l'invio
  all'app Musica.
- **Rileggi** (F5, in alto a destra): rilegge la cartella aperta, cioè i file nuovi, tolti o cambiati (gli altri dalla
  cache dei tag); con **Maiusc** premuto rilegge tutti i file da zero.

**I filtri a pulsanti**, sotto *Cerca*, con quanti brani ha ognuno (fanno anche da legenda della colonna *iPhone*):
**Tutti**, **Non sull'iPhone** (anche quelli in attesa di essere copiati), **✔ Uguali**, **⟳ Tag diversi**, **≈ Da
rivedere**, **✎ Modificati** (modifiche dei tag in sospeso) e **＋ In attesa** (un'azione per l'iPhone aspetta
*Applica*). Se ne sceglie uno alla volta; valgono insieme a *Cerca*, *Formato* e agli elenchi Artisti e Album.

**La barra delle azioni**, sopra la tabella: *N brani scelti* (i selezionati o, se non ce n'è nessuno, quelli
dell'artista o dell'album scelti negli elenchi) e i pulsanti con le stesse voci del tasto destro: **Copia N brani da
PC a iPhone**, **Ricopia da PC a iPhone**, **Usa i tag da PC a iPhone**, **Elimina dall'iPhone** (tutti in attesa),
**Cambia i tag…** (apre l'editor a destra) ed **Esporta in una cartella…**. Sotto, in grigio, quanti sono già in
attesa e quanti sono abbinati solo per i tag (≈). L'**editor dei tag** si chiude con la ✕ in alto e si riapre con
*Cambia i tag* o il tasto **E**.

La tabella dei brani si ordina cliccando sull'intestazione di una colonna (Artista, Album, Titolo, Anno…); finché non
la clicchi i brani sono in ordine di artista, album, disco e traccia. *Esporta*, *Verifica album online* e *Invia all'app Musica*
senza brani selezionati in tabella usano l'artista o l'album scelti negli elenchi.

**Scorciatoie** sulla tabella dei brani (per i brani selezionati o, se non ce n'è nessuno, per quello su cui sei;
mentre scrivi in *Cerca* o nell'editor valgono come tasti normali):
- **E**: **Cambia i tag**: il cursore nel riquadro dei tag a destra (campo *Titolo*, già selezionato), nella scheda PC
  come nella scheda iPhone (lì va in attesa);
- **Canc**: **Elimina dall'iPhone**, in attesa fino ad *Applica* (nella scheda PC i brani che ci sono con la
  sorgente associata). I file del PC non si cancellano mai;
- **F5**, in tutta la finestra: **Rileggi** della scheda che vedi (PC: rilegge la cartella; iPhone: rilegge la sua
  musica). *Verifica album online* è **F7**, *Controlla la musica* **F6**.

Artisti e album che differiscono solo per maiuscole, accenti o spazi ("Queen" e "queen") sono un gruppo solo, mostrato
con la grafia più usata (a parità, quella con le maiuscole). Anche "AA.VV.", "Artisti vari", "Various Artists", "VA" e
simili sono **un artista solo**, e i loro album con lo stesso nome un album solo; altri nomi che valgono come loro si
aggiungono in *Impostazioni → Generale → Altri nomi per "Artisti vari"*. I tag dei file non cambiano: la scansione
segnala la variante, perché l'iPhone la considera un artista diverso.

**La barra in alto** è a gruppi: la musica (*La mia musica*, *Apri cartella…*), le copie (*Importa nella
Libreria…*, *Esporta…*) e, a destra, *Impostazioni* e *Informazioni*. **I pulsanti** hanno un colore che dice cosa
fanno: **verde** l'azione principale (*Applica*, *Copia da PC a iPhone*, *Connetti iPhone*, *Avvia…*), **rosso** quelli
che cancellano o interrompono (*Elimina dall'iPhone*, *Disconnetti*, *Ferma*), neutri gli altri (bordo blu al passaggio
del mouse), grigi quando non si possono premere. Le icone sono disegnate dal programma.

La riga scelta è **blu con il testo bianco** in tutti gli elenchi e le tabelle, anche in quello che non stai usando
(negli elenchi Artisti e Album si vede sempre cosa è scelto). Nelle tabelle dei brani (schede PC e iPhone) **ogni
album ha il suo sfondo**: azzurro e ambra si alternano da un album all'altro, con un tono chiaro e uno scuro a righe
alterne dentro l'album, anche per i brani con un'azione in attesa (si riconoscono dal segno blu della colonna
*iPhone*). Nella scheda PC lo
stesso album in due copie (due cartelle, o FLAC e MP3 nella stessa cartella) non si mescola: prima tutti i brani di
una copia, poi quelli dell'altra, ognuna con la sua tinta (le cartelle dei dischi, "CD1" e "CD2" dello stesso album,
restano un album solo).

**Colonne.** #, iPhone, Titolo, Artista, **Artista album**, Album, Anno, Genere, Durata, **Cartella**, File. *File*
è il nome del file; *Cartella* è il nome della cartella che lo contiene, o il suo percorso completo con *Impostazioni →
Generale → Mostra il percorso completo delle cartelle*. Il suggerimento di tutte e due mostra il percorso completo.

**Tasto destro sui brani**, oltre ai comandi per l'iPhone: **Copia negli appunti** → *Nome del file*, *Percorso
completo*, *Nome della cartella*, *Percorso della cartella* (una riga per brano; le cartelle una volta sola; in un sottomenu, per non confonderle con *Copia
da PC a iPhone*) e **Apri la cartella in Esplora risorse**
(un file solo: selezionato; più cartelle: le prime 5).

**Nascondi la cartella** (tasto destro sui brani): i brani delle cartelle che li contengono, sottocartelle comprese,
spariscono dalla scheda PC (elenchi, tabella, controlli) e non si usano per *Associa sorgenti* e *Controlla la
musica* dell'iPhone. I file non cambiano. Si ricorda tra un avvio e l'altro; il pulsante **Cartelle nascoste (N)…** in
alto le elenca e mostra di nuovo quelle che spunti. Le stesse cartelle si aggiungono e si tolgono anche in
*Impostazioni → Cartelle della musica → Cartelle escluse*.

**Larghezza delle colonne.** Ogni colonna si allarga e si stringe trascinando il bordo dell'intestazione, in tutte e due
le schede e negli elenchi Artisti e Album; se non ci stanno tutte compare la barra di scorrimento.

**Colonna iPhone.** Per ogni brano: **✔** nell'app *Musica* dell'iPhone c'è questo brano (la sua sorgente è questo
file, dal registro della provenienza), con gli stessi tag; **⟳** c'è, ma con tag diversi; **≈** grigio, *da rivedere*:
sull'iPhone c'è un brano con lo stesso titolo e album e un artista in comune, ma non è collegato a questo file, quindi
non è certo che sia lui; vuoto, non c'è. "Lo stesso titolo e album" vuol dire senza badare a maiuscole, accenti e
spazi; un brano con modifiche in sospeso si ritrova anche con i tag del file. Per rendere certo un ≈: nella scheda
iPhone, tasto destro → *Associa le probabili* (o *Associa sorgenti*). Si basa sulla musica
dell'iPhone letta all'ultima connessione e salvata nella cartella dati, quindi si vede anche a iPhone disconnesso (il
suggerimento sull'intestazione dice di quando è l'elenco).

### Le azioni in attesa e Applica

**Tutto ciò che cambia l'iPhone va in attesa**: *Copia da PC a iPhone*, *Ricopia da PC a iPhone*, *Usa i tag da PC a
iPhone*, *Cambia i tag sull'iPhone*, *Elimina dall'iPhone*, le spunte della colonna *iPhone*, *Copia i brani mancanti
degli album* e *Ricopia le copertine*. Si mettono in attesa anche a iPhone scollegato; non parte niente finché non
premi **Applica**. Restano immediati, con la loro conferma, solo i comandi che non cambiano l'iPhone o che lo
cambiano in blocco con un'anteprima: *Copia da iPhone a PC*, *Usa i tag da iPhone a PC*, le associazioni e *Playlist
per artista*.

- **La barra blu**, sopra le schede (si vede da tutte e due), dice quante azioni ci sono e quali (*4 brani da copiare
  da PC a iPhone · 1 brano da eliminare dall'iPhone*) e, sotto, in verde, l'ultima cosa appena aggiunta (già contata
  nel totale). Le azioni per brani di cartelle non aperte, o con l'iPhone non ancora letto, si contano a parte:
  partono quando ci sono. Il titolo della scheda iPhone lo ripete: **iPhone ● · 5 in attesa**.
- **Annulla tutto** toglie tutte le azioni (sull'iPhone non cambia niente).
- **Applica N azioni…** apre la finestra con **tutte le azioni**, divise per gruppo (*Copia da PC a iPhone*,
  *Ricopia da PC a iPhone*, *Usa i tag da PC a iPhone*, *Cambia i tag sull'iPhone*, *Elimina dall'iPhone*), ognuna
  con il brano e cosa cambia (il formato, i campi diversi, i valori nuovi). La **✕** di una riga, o **Togli il
  gruppo**, toglie le azioni dalla coda subito: non partono, il brano resta com'è e le rimetti dalle schede; per
  molte righe insieme selezionale e premi **Togli le selezionate** (o Canc). Un gruppo di più di 300 azioni si apre
  chiuso (si apre con la freccia). In fondo il tempo stimato, gli album da ricopiare interi per la grafia, le playlist da sistemare dopo un rimpiazzo.
  La finestra si apre anche a iPhone scollegato, per guardare e togliere; **Applica N azioni** si preme a iPhone
  connesso e fa tutto insieme (copia, elimina, cambia i tag, poi *Usa i tag* e *Ricopia*). Alla fine un messaggio
  dice cosa è stato fatto, per specie (*12 brani copiati da PC a iPhone*, *3 brani eliminati dall'iPhone*…), e quali
  azioni non sono riuscite e perché. Le azioni riuscite escono subito dalla coda; quelle non riuscite restano in
  attesa per riprovarle. Poi il programma rilegge la musica dell'iPhone; se l'elenco non mostra ancora quello che è
  stato fatto (l'iPhone aggiorna il suo database poco dopo), lo rilegge da solo dopo 5 secondi, al più 3 volte.
- Prima di copiare, l'avviso per i brani che sull'iPhone ci sono già in un altro formato (vedi sotto).
- Un brano ha un'azione sola: una nuova (per esempio *Ricopia* dopo *Usa i tag*) prende il posto della vecchia.
- Le azioni restano nella cartella dati (`iphone_in_attesa.json`) anche chiudendo il programma; quelle già fatte, o
  non più possibili, si tolgono da sole a ogni lettura dell'iPhone.
- **Uscendo dal programma** con azioni in attesa che si possono fare un avviso dice quali sono e il tempo stimato:
  **Applica ed esci** (a iPhone connesso: il programma si chiude alla fine, con un messaggio solo se qualcosa non
  riesce), **Esci senza applicare** (restano in attesa per la prossima volta) o **Annulla**.

La stima del tempo viene da una misura su un iPhone vero via cavo (circa 17 MB al secondo, 1 secondo per sessione,
qualche migliaio di brani nella libreria), resa un po' più prudente: circa 1 minuto ogni 60 brani da copiare, pochi
secondi per eliminare o cambiare i tag di centinaia di brani.

**Le spunte della colonna iPhone.** La spunta vuol dire "voglio questo brano sull'iPhone". Mettere o togliere una
spunta mette il brano **in attesa**, con un segno diverso da quelli delle cose fatte:

| Segno | Vuol dire |
|---|---|
| ✔ verde | c'è, uguale |
| ⟳ arancio | c'è, con tag diversi |
| ≈ grigio | forse c'è: abbinato solo per i tag, da rivedere |
| **＋ blu** | in attesa: da copiare da PC a iPhone |
| **－ rosso** | in attesa: da eliminare dall'iPhone |
| **⟳ blu** | in attesa: *Usa i tag da PC a iPhone* o *Ricopia da PC a iPhone* |

- Una spunta cambiata su una riga selezionata vale per tutte le righe selezionate. Anche **artisti e album** negli
  elenchi in alto hanno la spunta, a tre stati (tutti i brani sull'iPhone, alcuni, nessuno), in corsivo blu se
  dentro c'è qualcosa in attesa: cliccarla mette o toglie tutti i loro brani.
- **Togliere** una spunta vale solo per i brani che sull'iPhone vengono da quel file (colonna *Sorgente* della scheda
  iPhone): un brano abbinato solo per i tag non si toglie mai così (la sua spunta non si può togliere).
- **Si aggiornano dal PC solo i brani associati** (registro della provenienza: quel file è quel brano). Un brano
  abbinato solo per i tag (≈, anche se ha tag diversi) non si aggiorna, non si ricopia e non va in attesa: il menu
  lo conta a parte. Prima lo si associa (scheda iPhone: *Associa al file sul PC*, *Associa le probabili ≈*).

**Tag.** A destra si modificano titolo, artista, artista album, album, numero di traccia e di disco, anno, genere,
la spunta **Compilation** e la copertina (MP3, M4A, FLAC, OGG, Opus; copertina per MP3, M4A, FLAC). Con più brani
selezionati, solo i campi modificati valgono per tutti; la spunta mostra un quadratino pieno a metà quando i brani
sono diversi.

**Tutti i tipi di tag**, come TagScanner e Mp3tag. Negli MP3 si leggono **ID3v2** (2.2, 2.3, 2.4), **APEv2** e il
vecchio **ID3v1**, uniti campo per campo in quest'ordine: un campo vuoto si prende dal tipo seguente (un MP3 con solo
APE o solo ID3v1 mostra i suoi tag). Con un brano selezionato, sotto il nome del file, *Tag letti da: ID3v2.3 + APEv2*
dice da dove vengono. Le copie (iPhone, esportazione) ricevono i tag uniti, in ID3v2.3. **WMA, WAV e AIFF** si leggono
(ASF; ID3 e RIFF INFO per i WAV; ID3 per gli AIFF) e si vedono, ma i loro tag non si modificano e all'iPhone non si
inviano (serve una conversione).

**Compilation.** Un album di più artisti: l'*artista* è quello di ogni brano, l'*artista album* è "Artisti vari", e
in più c'è la spunta **Compilation** (nei file: TCMP negli MP3, COMPILATION nei FLAC e Ogg, cpil negli M4A). L'app
Musica dell'iPhone tiene insieme l'album solo con tutte e tre le cose; senza la spunta lo divide in un album per
artista. La scansione, quando propone "Artisti vari", propone anche la spunta. *Numera in ordine* assegna 1, 2, 3… nell'ordine della tabella. *Salva modifiche* **non
scrive nel file**: salva le modifiche in sospeso (`modifiche_tag.json` e `copertine\` nella cartella dati). In tabella
i brani modificati hanno il titolo in corsivo blu, e il suggerimento elenca le modifiche (*campo: prima → dopo*).
*Torna ai tag del file* le annulla. La casella **Anche sull'iPhone: usa questi tag da PC a iPhone** (sopra *Salva
modifiche*, spenta di serie e di nuovo spenta dopo ogni salvataggio) mette in attesa anche l'iPhone, per i brani che
lì hanno la sorgente certa: *Usa i tag da PC a iPhone*, o *Ricopia* se hai cambiato la copertina.

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
un disco esterno o di rete. Con la lettura di tutti i tipi di tag, gli MP3 della cache con un campo vuoto (titolo,
artista, album, anno, genere o numero) si rileggono una volta. Durante la lettura
gli elenchi sono vuoti: la barra di stato mostra l'avanzamento. Il programma si apre **una volta sola**: una seconda
copia lo dice e si chiude.

**File illeggibili.** Un file che non si riesce a leggere (danneggiato, bloccato, disponibile solo online in
OneDrive…) compare in rosso, con il motivo nel suggerimento, e non interrompe la lettura della cartella.

## Controlla la musica

*Controlla la musica* (linguetta **Controlli**, riquadro a sinistra; **F6** la apre, la "scansione") analizza i brani
aperti nella scheda PC, oppure la musica dell'app *Musica* dell'iPhone confrontata con le cartelle della musica del PC
(si può fare anche a iPhone disconnesso, con l'ultimo elenco letto). Nel riquadro scegli **quali controlli
fare** (le caselle della tabella qui sotto, ognuna con una riga di spiegazione; le scelte si ricordano). Prima
applica delle regole locali, veloci e gratuite; poi, se scegli di usarla, l'AI. Il rapporto resta in
`.myEasyMP3toIPhone\scansioni\`; **Avvia il controllo** lo fa partire e i risultati compaiono sotto, in *Risultati del
controllo*. Ogni problema può avere una **correzione**: si applica dai risultati, dopo
una conferma, come **modifiche in sospeso** (i file sul PC non cambiano; vanno sulle copie inviate all'iPhone); *Mostra
i brani* li seleziona nella scheda PC. I problemi trovati sull'iPhone non hanno correzioni automatiche: si correggono i
brani sul PC e poi si usa *Usa i tag da PC a iPhone* o *Ricopia da PC a iPhone*, o si cambiano dalla scheda iPhone
(tasto destro → *Cambia i tag*).

| Sintomo | Cosa cerca | Correzione |
|---|---|---|
| **File che non si aggiornano** | sull'iPhone, brani con tag diversi da quelli del PC (o delle modifiche in sospeso); MP3 con un vecchio tag ID3v1 diverso o con un tag APE (solo informazione: le copie inviate ne sono ripulite) | sull'iPhone nessuna (la colonna *iPhone* della scheda PC mostra le differenze) |
| **Album con pochi brani** | numeri di traccia mancanti, meno brani del totale dichiarato, album di 1-2 brani; sull'iPhone, album con meno brani che sul PC | (Verifica album online trova i titoli mancanti) |
| **Collezioni divise su più album** | una cartella con brani in album diversi; lo stesso album scritto in modi diversi o con "CD 1"/"Disc 2" nel nome; una compilation senza *Artista album* | unifica album e artista album ("Artisti vari" e la spunta *Compilation* per le compilation), sposta il numero del disco in *N. disco* |
| **Artisti scritti in modi diversi** | **certo**: le stesse parole a parte maiuscole, accenti, punteggiatura, "The" e ordine ("Battiato Franco" = "Franco Battiato", "AC/DC" = "ACDC"); **dubbio**: solo il cognome ("Battiato"), le iniziali ("F. Battiato"), un errore di battitura: decide l'AI (con album e anni) e, se lo chiedi, MusicBrainz (nomi e alias dell'artista), solo per questi gruppi; senza nessuno dei due restano "forse lo stesso artista", da controllare. **Duetti** ("A & B", "A feat. B", "A, B"): se A c'è anche da solo, artista e artista album diventano A e gli ospiti vanno nel titolo, "Titolo (feat. B)" (l'app Musica non gestisce più artisti); un nome come "Simon & Garfunkel" resta com'è | scrive ovunque la forma **più usata** (quella con più brani); per l'iPhone poi *Usa i tag da PC a iPhone* e *Applica* |
| **Solo sull'iPhone** | brani dell'app Musica senza un brano uguale (artista, album, titolo) nella Libreria del PC | nessuna: salvali sul PC dalla scheda iPhone (tasto destro → *Copia da iPhone a PC*) |
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

## Verifica album online

*Verifica album online* (linguetta **Controlli**, riquadro a destra; **F7** la apre) confronta gli album scelti negli
elenchi della scheda PC (o tutti) con un **catalogo su internet**: dice
se manca qualche brano e propone i tag giusti e la copertina. È diverso da *Controlla la musica*, che confronta i tuoi
brani tra loro (e con l'iPhone), senza cataloghi.

Nel riquadro si scelgono i **cataloghi** (le scelte si ricordano), poi **Avvia la verifica**:

| Catalogo | Com'è | Predefinito |
|---|---|---|
| **Deezer** | veloce, gratis, senza chiave | acceso |
| **Apple Music** | l'iTunes Search API, gratis e senza chiave, con i nomi che usa l'app Musica; circa 20 richieste al minuto (il paese del negozio è quello di Windows) | acceso |
| **Discogs** | tante edizioni, anche rare e in vinile; vuole un **token personale** in `DISCOGS_TOKEN` (discogs.com, *Impostazioni → Sviluppatori → Generate new token*); senza, la casella è spenta | spento |
| **MusicBrainz** | il più completo, ma una richiesta al secondo | spento |

Con più cataloghi scelti **si provano in quest'ordine** (dal più veloce), album per album, **finché uno dà l'album
completo**; se nessuno lo dà, vale il risultato migliore (quello con meno brani mancanti) e i risultati dicono quali
cataloghi sono stati provati e con che esito. La casella **AI per scegliere tra edizioni dubbie** (spenta di
base) interviene solo quando due edizioni di un album sono ugualmente probabili: l'AI della scansione riceve titoli e
numero dei brani e le edizioni trovate, e ne sceglie una (il motivo si vede nei risultati). CDDB/freedb ha chiuso nel
2020; il suo erede gnudb vuole la struttura del CD (TOC), che dei file non hanno.

**In background.** La verifica non blocca il programma: il riquadro e la barra di stato dicono a che punto è
(*Ferma*, nel riquadro, la interrompe; i risultati già trovati restano; *Vedi*, nella barra di stato, porta alla
linguetta) e l'icona di ogni album nell'elenco *Album* ne mostra l'esito man mano. Alla fine, o quando la fermi, i
**risultati** compaiono sotto, in *Risultati della verifica*: per ogni album le tracce dell'edizione trovata e i tuoi file, le **mancanti in rosso** e quelle non
riconosciute in grigio. Si può scegliere un'altra edizione, *Correggere i tag con questi dati* (titolo, numeri di
traccia e disco, album, artista album, anno, e la copertina: tutto in sospeso, per le copie) e *Apri su …* la pagina
dell'edizione nel catalogo. Aprire un'altra cartella ferma la verifica in corso.

## L'iPhone

**Basta attaccare l'iPhone con il cavo:** il programma lo rileva da solo (controlla ogni 3 secondi) e si connette. La
prima volta l'iPhone chiede **"Autorizzare questo computer?"**: tocca *Autorizza* e inserisci il codice. La scheda
**iPhone** e la barra di stato dicono a che punto è; se la connessione automatica non riesce (iPhone bloccato,
autorizzazione negata) lo dice lì, e *Connetti iPhone* riprova. Senza il driver Apple la scheda dice di installare
*Dispositivi Apple*. Il pulsante dice cosa fa: **verde "Connetti iPhone"** quando non è connesso, **rosso
"Disconnetti iPhone"** quando lo è; il titolo della scheda diventa **"iPhone ●"** in verde, così lo si vede anche
dalla scheda PC (con le azioni in attesa: **iPhone ● · 5 in attesa**). Dopo *Disconnetti* il programma non si riconnette da solo finché non premi *Connetti iPhone* o stacchi
e riattacchi il cavo. Staccando il cavo l'iPhone risulta disconnesso.

**Il riquadro dell'iPhone**, in cima alla scheda: nome e stato della connessione, quanti brani ci sono e di quando
è l'elenco, **Rileggi** (F5), **Connetti/Disconnetti iPhone** e **?**, che apre la spiegazione dei segni delle colonne
e di dove sono le azioni. Sotto, sempre, l'avviso di non premere *Sincronizza* in iTunes.

**La barra delle azioni** sopra i brani dell'iPhone ha le voci del tasto destro per i brani scelti (o, senza
selezione, per quelli dell'artista o dell'album scelti): **Copia N brani da iPhone a PC…**, **Ricopia da PC a
iPhone**, **Usa i tag da PC a iPhone**, **Cambia i tag…**, **Associa al file sul PC…**, **Elimina dall'iPhone**. Il
menu **Strumenti** ha il resto: *Usa i tag da iPhone a PC…*, *Mostra nella scheda PC*, *Copia i brani mancanti degli
album* e *Ricopia le copertine* (per i brani scelti o, senza scelta, per tutti), *Associa al file sul PC tutti i
brani senza sorgente…*, *Associa le probabili ≈*, *Associa la sorgente proposta in rosso*, *Togli la sorgente* e
*Rifai le playlist per artista sull'iPhone…*.

**Il riquadro dei tag**, a destra, è fatto come quello della scheda PC: i tag dei brani selezionati come li mostra l'app
Musica e la copertina del file associato sul PC (l'immagine che ha l'iPhone non si legge da qui; se l'album sull'iPhone
non ha l'immagine lo dice). Si cambiano titolo (un brano alla volta), album, numeri, anno, genere e *Compilation*:
**Metti in attesa** e l'iPhone cambia con *Applica*. Artista, artista dell'album e totali si vedono ma non si cambiano
qui; i brani non messi da un computer si vedono soltanto. Si chiude con la ✕ e si riapre con *Cambia i tag* o **E**.

**La musica dell'app Musica.** Connesso l'iPhone, la scheda **iPhone** mostra i brani dell'app *Musica* con i
titoli, gli artisti e gli album che mostra l'app: il programma ne copia sul PC il database (`MediaLibrary.sqlitedb`)
e lo legge, perché sul telefono i file hanno nomi casuali (`F12/ABCD.mp3`). Sono solo i brani con un file
sull'iPhone, non quelli in streaming da Apple Music. *Cerca* filtra per titolo, artista o album.

- **Colonne:** N., Sul PC, Sorgente, Titolo, Artista, **Artista album**, Album, Anno, Genere, Durata, **Cartella della
  sorgente** e **File della sorgente** (il file del PC da cui viene il brano: la cartella, con il solo nome o il
  percorso completo come nella scheda PC, e il nome del file; per una sorgente su un altro computer la cartella è
  `COMPUTER: cartella`). Per un brano senza
  sorgente può mostrare **in rosso una sorgente proposta**, cercata tra i file della cartella aperta senza leggere
  l'audio (circa un secondo e mezzo per 500 brani senza sorgente e 15.000 file):
  1. **album intero**: per ogni album dell'iPhone i file con lo stesso titolo (anche dal nome del file, senza
     maiuscole, accenti, punteggiatura e parentesi) e la stessa durata (entro 2 secondi), se una cartella li ha tutti
     (con più cartelle così, quella con più numeri di traccia uguali, poi le *cartelle preferite*). Un album su più
     dischi conta come una cartella sola: `Album\CD 1 …`, `Album\CD 2 …` e anche `Album (Disc 1)`, `Album CD2`. Un
     doppione sull'iPhone (lo stesso brano due volte) non fa perdere l'album: il file va a uno solo;
  2. per gli altri brani, come **Associa sorgenti** senza impronta né AI: il **nome della cartella** e le **regole**
     (vedi sotto), solo le proposte *molto probabili* e *probabili*.
  Un file già associato a un altro brano non si propone. Il suggerimento sul nome dice la certezza e il motivo. La
  proposta non è ancora una sorgente: tasto destro → **Associa questa sorgente** la scrive nel registro e cartella e
  nome tornano del colore normale.
- **Sul PC:**

  | Segno | Significato |
  |---|---|
  | ✔ verde | la sorgente (dal registro della provenienza) c'è, con gli stessi tag |
  | ⟳ arancio | la sorgente c'è, con tag diversi: *Usa i tag da PC a iPhone*, *da iPhone a PC* o *Ricopia da PC a iPhone* |
  | ≈ grigio | **da rivedere**: nella cartella aperta c'è un brano con lo stesso titolo, album e artista, ma non è collegato: non è certo che sia la sorgente |
  | ✖ rosso | il registro ha una sorgente su questo PC, ma il file non c'è più |
  | vuoto | non trovato |

  La sorgente vale anche **fuori dalla cartella aperta**: il programma ne legge i tag (solo lettura, con la cache dei
  tag) e la confronta, così ✔ e ⟳ non dipendono da quale cartella è aperta. Il suggerimento lo dice.

**Il suggerimento di ✔ e ⟳** (colonna *iPhone* della scheda PC, *Sul PC* della scheda iPhone) è una tabella: in
cima il brano abbinato (il brano dell'iPhone, o il file del PC con il percorso) e come è stato abbinato, *certo*
dal registro della provenienza o *probabile* solo per artista, album e titolo; sotto, tutti i tag confrontati, sul PC
e sull'iPhone affiancati, con i valori diversi evidenziati. Artisti e album che differiscono solo per maiuscole o
accenti non sono evidenziati: sull'iPhone sono lo stesso gruppo.
- **Tasto destro** su uno o più brani (le stesse voci sugli elenchi Artisti e Album, per tutti i loro brani):
  - **Copia N brani da iPhone a PC…** (subito, a iPhone connesso) copia i file in una cartella a scelta (proposta:
    la Libreria), ordinati in `Artista/Album (Anno)/NN - Titolo` con i nomi che mostra l'app; crea solo file nuovi,
    un file già presente sul PC non viene mai sostituito;
  - **Mostra nella scheda PC** seleziona i brani corrispondenti del PC;
  - **Ricopia da PC a iPhone** e **Usa i tag da PC a iPhone** (per i brani con la sorgente certa e tag diversi, ⟳):
    in attesa, come nella scheda PC;
  - **Usa i tag da iPhone a PC…** (⟳; subito) mostra l'elenco dei file e, per ognuno, i campi che cambiano (*ora sul
    PC → diventa*); con **Modifica N file** li scrive nei file (MP3 in ID3v2.3; WMA, WAV e AIFF no), senza
    annullamento. Le modifiche in sospeso di quei file entrano nel file insieme; una copertina in sospeso resta in
    sospeso;
  - **Cambia i tag…** (tasto **E**, nel riquadro a destra): titolo (un brano alla volta), album, genere, anno, numeri,
    *Compilation*; va in attesa. La casella **Anche sul PC** (spenta, si rispegne dopo ogni volta) mette gli stessi tag sui file del PC associati, come modifiche in
    sospeso (i file non cambiano);
  - **Copia i brani mancanti degli album da PC a iPhone** e **Ricopia le copertine da PC a iPhone** (vedi sotto),
    in attesa;
  - **Associa al file sul PC…**, **Associa le probabili ≈** (rende certi i brani ≈ scelti, dopo una conferma),
    **Associa la sorgente proposta in rosso** (come *cartella*), **Togli la sorgente**: subito, solo il registro;
  - **Elimina N brani dall'iPhone** (tasto **Canc**): in attesa;
  - **File della sorgente** → *Copia negli appunti* (nome del file, percorso completo, nome e percorso della cartella) e *Apri la cartella
    in Esplora risorse*, come nella scheda PC.
- L'elenco letto resta in `iphone_musica.json` nella cartella dati: scheda iPhone, colonna *iPhone* e scansione
  funzionano anche a telefono disconnesso. **Rileggi** lo rilegge dall'iPhone connesso; senza iPhone rifà il
  confronto con il PC.

### Scrivere nell'app Musica

Il programma scrive nella musica dell'app Musica con lo stesso servizio di sincronizzazione di Apple che usano iTunes e
CopyTrans Manager (*AirTrafficControl*), senza iTunes e senza sincronizzare tutto: ogni volta manda solo le modifiche
("Delta"), mai una sostituzione completa.

| Dove | Tasto destro | Cosa fa |
|---|---|---|
| Scheda **PC** | **Copia da PC a iPhone** | i brani che non sono sull'iPhone: una copia con i tag e la copertina modificati (i file del PC non cambiano) |
| Schede **PC** e **iPhone** | **Ricopia da PC a iPhone** | i brani **associati** con tag diversi (⟳): vedi *Ricopia* qui sotto |
| Schede **PC** e **iPhone** | **Usa i tag da PC a iPhone** | i brani associati ⟳ prendono i tag del PC: dove basta si cambiano i tag (restano ascolti e playlist), per artista e artista dell'album si ricopiano |
| Scheda **iPhone** | **Cambia i tag…** (riquadro a destra) | titolo (un brano alla volta), album, genere, anno, numero di traccia e di disco, la spunta **Compilation** (a tre stati con brani diversi); un campo vuoto non cambia, 0 svuota anno o numero |
| Schede **PC** e **iPhone** | **Elimina dall'iPhone** | toglie i brani dall'app Musica; l'iPhone cancella i loro file da solo, entro qualche minuto |

Tutte vanno **in attesa** e partono con **Applica** (vedi [Le azioni in attesa](#le-azioni-in-attesa-e-applica)).

- Alla fine di ogni scrittura il programma manda all'iPhone l'avviso di fine sincronizzazione, come iTunes (una prova:
  non è documentato).
- **L'app Musica potrebbe non aggiornarsi da sola** se è aperta durante l'invio: chiudila del tutto (scorri via la sua scheda)
  e riaprila; i brani si trovano nella tua libreria (*Libreria → Artisti* o *Brani*), non cercando in Apple Music.
- **Formati:** MP3, FLAC (l'iPhone li suona così come sono) e M4A in AAC. Gli M4A in Apple Lossless non ancora.
- **Copertine:** quella modificata, o altrimenti quella del file, se è JPEG o PNG.
- **Album e artisti:** sull'iPhone album e artisti dell'album sono gruppi: un brano va nel gruppo che c'è già con un
  nome "uguale" e il gruppo tiene la sua grafia, finché esiste (anche vuoto). Per l'iPhone sono uguali i nomi che
  differiscono per maiuscole, accenti, spazi o zeri davanti ai numeri ("Raccolta 01" = "Raccolta 1"); "AA.VV.",
  "Artisti vari" e "Various Artists" invece sono tre artisti diversi. Il confronto (colonna *iPhone*, giallo della
  scheda iPhone) guarda i nomi come sono scritti: anche una grafia diversa è una differenza (⟳), e ogni
  aggiornamento dal PC la corregge da solo (vedi *La grafia* sotto).
- **Compilation:** si invia la spunta, con l'artista dell'album ("Artisti vari" se manca): l'album resta intero
  nell'app Musica.
- **Ricopia** prima copia la versione del PC, poi toglie quella vecchia, solo se la copia è riuscita. Il brano
  ricopiato perde il conteggio degli ascolti. Le **playlist messe da un computer** (le ♪ di *Playlist per artista*,
  quelle di CopyTrans o iTunes) che lo contenevano **si rifanno da sole**, nello stesso *Applica*: stesso nome, stesso
  ordine, il brano nuovo al posto di quello vecchio (il messaggio alla fine le elenca). Se il brano nuovo non risulta
  ancora sull'iPhone la playlist resta com'è, senza di lui, e il messaggio lo dice. Le **playlist fatte sul
  telefono** il computer non le può cambiare: la finestra di *Applica* e il messaggio alla fine dicono in quali era
  ciascun brano, così lo rimetti a mano (le playlist smart si aggiornano da sole). Lo stesso vale per gli album
  ricopiati interi per la grafia.
- **Una modifica da una parte non cambia l'altra.** Cambiando i tag nella scheda **PC** (editor, scansione,
  *Verifica album online*, *Torna ai tag del file*) l'iPhone resta com'è; con **Cambia i tag** nella scheda **iPhone**
  i file del PC restano come sono. I brani con la sorgente su questo PC diventano ⟳, con il nome del file **in
  giallo** (scheda iPhone, colonne della sorgente; scheda PC, colonne Cartella e File), e restano associati. Si
  allineano solo con un'azione tua: **Usa i tag da PC a iPhone** / **da iPhone a PC** (tasto destro), oppure le caselle
  **Anche sull'iPhone** / **Anche sul PC** mentre cambi i tag (spente di serie).
- **Artista e artista dell'album** non si cambiano con *Cambia i tag* della scheda iPhone: sull'iPhone cambiarli
  rinominerebbe l'artista per tutti i suoi brani. Si cambiano nella scheda PC, poi *Ricopia da PC a iPhone*.
- La spunta **Compilation** di *Cambia i tag* cambia solo il brano. Una compilation vuole anche l'artista dell'album
  *Artisti vari*: se nell'app Musica i brani non si raccolgono in un solo album, metti spunta e "Artisti vari"
  nella scheda PC e usa *Ricopia da PC a iPhone*, che manda brano e album insieme.
- **Rifai le playlist per artista sull'iPhone…** (scheda iPhone, menu **Strumenti** della barra delle azioni) rifà
  le playlist dell'iPhone. Prima legge musica e
  playlist dall'iPhone e mostra il piano; non scrive niente finché non confermi:
  - **per artista**: una playlist per ogni *artista dell'album* (non l'artista dei singoli brani) con almeno 2 album
    e 5 brani; i dischi di un album ("CD 1", "CD 2") contano come un album solo. Dentro: gli album per anno, poi
    disco e numero di traccia;
  - **per compilation**: gli album "AA.VV." / "Artisti vari", con la spunta *Compilation* o con tanti artisti
    diversi. I volumi della stessa serie vanno in una playlist sola: quelli nella stessa cartella sul PC con il nome
    della cartella nel loro nome (es. `Raccolta Ottanta\Raccolta Ottanta Vol. 3\…`, la playlist prende il nome della
    cartella), poi quelli con lo stesso nome a parte "Vol. N" e "CD N". Un album solo ha la sua playlist se ha almeno
    20 brani;
  - i nomi cominciano con **♪** ("♪ Rosa Neri"); ogni playlist si può togliere dal piano con la sua spunta;
  - **si cancellano tutte le playlist messe da un computer** (CopyTrans, iTunes, questo programma, comprese le ♪ della
    volta prima). Quelle fatte sull'iPhone, le smart e le cartelle restano: un computer non le può toccare;
  - prima si creano le nuove, poi si cancellano le vecchie; i brani non cambiano. In una playlist possono stare solo
    i brani messi da un computer (non quelli acquistati sul telefono);
  - **Prova** crea solo "♪ PROVA", una copia della prima playlist spuntata, e non cancella niente: per vedere sul
    telefono che va, prima di farlo davvero. La volta dopo si cancella con le altre.
  Dopo un *Ricopia* non serve rifarle: le playlist messe da un computer si rifanno da sole con i brani nuovi.
- Si possono aggiornare ed eliminare solo i brani messi sull'iPhone da un computer (iTunes, CopyTrans, questo
  programma), non quelli acquistati o scaricati sul telefono.
- Serve l'iPhone connesso e sbloccato, con la gestione manuale della musica attiva (in *Dispositivi Apple* o in
  iTunes, con l'iPhone attaccato: *Gestisci manualmente musica e video*) e senza *Sincronizza libreria* di Apple Music. Se manca qualcosa il programma
  lo dice e non scrive niente.

**Da dove viene un brano.** Il programma tiene un **registro della provenienza**: per ogni brano dell'iPhone
(il suo identificativo fisso, `sync_id`), il computer e il file da cui viene, con dimensione, data, le modifiche in
sospeso al momento dell'invio e l'**impronta dell'audio**, e come è nata l'associazione (*inviato*, *impronta*,
*cartella*, *regole*, *ai*, *a mano*, *salvato*). Ogni invio lo registra; un'eliminazione toglie la riga. Il registro sta nella
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

Sopra l'elenco dei brani ci sono gli elenchi **Artisti** e **Album**, come nella scheda PC (senza le spunte): un
artista o un album scelto mostra solo i suoi brani, insieme a *Cerca* e ai filtri a pulsanti.

I **filtri a pulsanti** (prima il menu *Mostra*), con quanti brani ha ognuno, filtrano l'elenco per sorgente (per esempio solo i brani *senza sorgente*), e per la colonna *Sul PC*:
*Da rivedere: abbinati solo per i tag (≈)*, *Sorgente con tag diversi (⟳)* (anche solo la grafia), *Con una
sorgente proposta (in rosso)* e *Album senza immagine sull'iPhone*.

**La grafia.** Quando un aggiornamento dal PC (*Ricopia da PC a iPhone*, *Usa i tag da PC a iPhone*, *Ricopia le
copertine*, tutti con *Applica*) tocca un brano associato che sull'iPhone ha l'album o l'artista
dell'album scritto in modo diverso dal PC ("Raccolta 1" invece di "Raccolta 01", "ARTISTA" invece di "Artista"),
il programma ne prende l'album intero e lo reinvia, nella stessa operazione. L'iPhone infatti tiene il nome che
ha già per un album o un artista finché la sua riga esiste, anche vuota (provato il 24/11/2026: né un nuovo invio,
né *Cambia tag*, né il riavvio lo cambiano), e cancella le righe vuote solo in certe sessioni di eliminazione (con
100 brani tolti insieme sì). Quindi, prima del resto dell'aggiornamento:
1. invia i brani di servizio che servono (3 secondi di silenzio, album "myEasyMP3toIPhone servizio");
2. toglie in una sessione i brani di quegli album insieme a quelli di servizio (almeno 100 nell'ultima sessione);
3. controlla nel database dell'iPhone che i nomi vecchi siano spariti;
4. reinvia gli album dal PC, con la sua grafia, e aggiorna il registro della provenienza.

Si prende sempre l'album intero, anche i brani non scelti; se è scritto diversamente l'artista dell'album, tutti gli
album di quell'artista (sull'iPhone la sua riga è una sola). La finestra di *Applica* lo dice, con quanti brani in
più. Un album con brani senza sorgente associata non si può reinviare intero: i suoi brani si aggiornano come gli
altri e restano con la grafia dell'iPhone (la finestra lo dice). Il reinvio si fa sempre, anche se l'iPhone tenesse
i nomi vecchi (allora lo dice). Come *Ricopia*, i brani reinviati perdono gli ascolti e le playlist fatte sul telefono (quelle di un computer si rifanno da sole). Un brano di servizio
rimasto da un'operazione interrotta si toglie alla successiva.

**Lo stesso brano in un altro formato.** Ad *Applica*, prima di copiare brani nuovi (*Copia da PC a iPhone*, *Copia
i brani mancanti degli album*, le spunte) il programma controlla se qualcuno c'è già sull'iPhone in un altro formato (stesso artista,
stesso titolo, durata uguale entro 2 secondi, estensione diversa: per esempio il FLAC di un brano che sull'iPhone è
MP3), o se nello stesso invio ci sono due copie in formati diversi. Se sì, un avviso li elenca: **Invia senza
questi** (scelta predefinita; tra due copie nello stesso invio resta quella della prima cartella preferita; quelli
lasciati fuori escono dalla coda e il messaggio lo dice), **Invia anche questi** o **Annulla** (non parte niente). La stessa canzone nello stesso formato in un'altra raccolta non conta. All'uscita
(*Applica ed esci*) l'avviso non compare: si è già confermato.

**Copia i brani mancanti degli album da PC a iPhone** (scheda iPhone, tasto destro sui brani, o su un artista o un
album; prima si chiamava *Completa l'album*): per un album di cui sull'iPhone ci sono solo alcuni brani, mette in
attesa gli altri. Dai brani scelti con la sorgente associata (✔, ⟳) risale alla loro copia dell'album sul PC (la
stessa cartella, con i dischi "CD1", "CD2" insieme, e lo stesso album) e prende quelli che sull'iPhone non ci
sono. Una copia in un'altra cartella (per
esempio in FLAC) non si manda; un brano abbinato solo per i tag (≈) non conta.

**Ricopia le copertine da PC a iPhone** (scheda iPhone, tasto destro sui brani, o su un artista o un album, anche
"(Tutti gli artisti)"; prima si chiamava *Sistema le copertine*; il filtro *Album senza immagine sull'iPhone* li
mostra): gli
album messi sull'iPhone da altri programmi (CopyTrans, iTunes) possono non avere l'immagine dell'album anche se i
loro brani hanno la copertina: l'iPhone non ne ha scelta una. Gli album inviati da questo programma ce l'hanno
sempre. Il comando mette in attesa *Ricopia* per i brani di quegli album con la sorgente associata e l'iPhone
sceglie l'immagine (provato il 24/11/2026). Come *Ricopia*: perdono gli ascolti e le playlist fatte sul telefono. Il programma copia sempre
la copertina che sta *dentro* il file (JPEG o PNG); un'immagine a parte nella cartella (`folder.jpg`) non si usa.

Quando un brano ha la
sorgente, il confronto delle colonne *Sul PC* e *iPhone* usa quel file esatto: un doppione sul PC con gli stessi tag
non prende il suo posto. **Copia da iPhone a PC** associa ogni brano salvato al suo file nuovo (verificato con l'impronta),
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
- **Associa sorgenti…** (più brani, per esempio un album intero): la finestra di *Associa sorgenti* (sotto) per
  i brani scelti, anche quelli che hanno già una sorgente.
- **Togli sorgente**: il brano torna *senza sorgente*.

**Sorgenti sparite.** Il programma non cancella mai i file del PC: li cancelli tu (per esempio un doppione). Quando
apri una cartella o leggi l'iPhone, i brani dell'iPhone il cui file sul PC non c'è più (*file non trovato*) si
segnalano con un avviso, una volta per sessione. Prima il programma li cerca da solo nella cartella aperta, in
meno di un secondo anche con migliaia di brani: un file **spostato o rinominato** si ritrova (1) con lo stesso nome
e la stessa dimensione, e lo stesso audio se il registro ne ha l'impronta; (2) con lo stesso audio e un altro nome
(tra più copie, quella nella cartella con il nome più simile a prima); (3) per gli altri, l'album intero in una
cartella e le regole, come le proposte in rosso. La colonna *Ritrovato sul PC* dice dove, il suggerimento come.
Per il punto (2), dopo l'apertura di una cartella il programma calcola **in sottofondo** l'impronta dei file che non
ce l'hanno ancora nella cache dei tag (la prima volta tutti, uno o due minuti; poi solo i file nuovi, spostati o
cambiati): non blocca niente e si ferma se apri un'altra cartella o esci.
Per quelli spuntati l'avviso offre: **Associa i file ritrovati** (si scrive solo il registro della provenienza),
**Cerca un'altra sorgente** (la finestra di *Associa sorgente*, uno alla volta, con per prima la copia con lo stesso
audio),
**Lascia senza sorgente** o **Elimina dall'iPhone** (in attesa fino ad *Applica*). Un file su un disco che ora non è collegato non
conta come sparito. Il contrario non succede mai: eliminare un brano dall'iPhone non cambia niente sul PC, e i
doppioni del PC e quelli dell'iPhone si gestiscono in modo del tutto separato.

**Brani fantasma.** A ogni lettura dell'iPhone il programma guarda anche quali file ci sono nelle cartelle della musica
del telefono (una lettura per cartella, non per brano): un brano dell'elenco il cui file non c'è è un *fantasma*.
La colonna *Sorgente* dice *senza file*, la barra di stato li conta, il filtro *Senza file sull'iPhone* li elenca e
*Controlla la musica* dell'iPhone li segnala tra i file illeggibili. Non si tolgono da soli: tasto destro →
*Elimina dall'iPhone*.

L'**impronta** riassume l'audio e non cambia quando cambiano i tag: per gli MP3 i primi 64 KB dopo il tag ID3, per i
FLAC l'impronta dell'audio che il file porta nella sua intestazione, per gli M4A l'inizio del blocco audio. Così un
brano dell'iPhone si riconosce anche se titolo, album o artista sono diversi da quelli del PC (le compilation, i
brani "sciolti"): su 40 brani messi sull'iPhone da CopyTrans, 40 sono stati ritrovati così sul PC.

**Associa sorgenti** (scheda iPhone: *Strumenti → Associa al file sul PC tutti i brani senza sorgente*, o
*Associa al file sul PC* per i brani scelti) ritrova il file del PC dei brani
dell'iPhone (messi da CopyTrans, da un altro computer…) e lo scrive nel registro. Una finestra chiede:

- **Brani:** tutti quelli senza sorgente, oppure quelli selezionati (anche con una sorgente: la si può sostituire);
- **Dove cercare:** una cartella con tutte le sue sottocartelle (proposta: quella dove stanno le sorgenti già note
  degli stessi album, altrimenti la cartella aperta), oppure **Tutte le cartelle della musica di questo PC**. Una
  cartella fuori da quelle aperte si legge in quel momento (con la cache dei tag);
- **Come**, in ordine, dal più veloce; per ogni brano ci si ferma al primo che lo trova:

1. **nome della cartella** (sempre, veloce: non legge l'audio): una cartella il cui nome, o quello della cartella sopra,
   contiene il nome dell'album (senza maiuscole, accenti, punteggiatura e parentesi: "Il Disco" si trova in
   `Artista - Il disco (1999)\CD1`), e dentro un file con lo stesso titolo e la stessa durata (entro 2 secondi).
   Con anche lo stesso numero di traccia è **molto probabile**, e il brano non ha bisogno d'altro; senza il numero è
   **probabile** (spuntato, ma se c'è l'impronta si controlla anche quella); con il titolo solo simile è **da
   controllare**;
2. **impronta dell'audio** (casella, accesa di base): stesso audio = stesso brano, qualunque siano titolo, album,
   artista; con più copie sul PC sceglie quella con i tag più simili. **Certo.** Si leggono solo le impronte dei
   brani che il nome della cartella non ha trovato con sicurezza, e solo dei file del PC con una durata vicina. A
   iPhone disconnesso valgono solo quelle già lette;
3. **regole**: durata entro 2 secondi e titolo e artista quasi uguali, con un solo candidato chiaramente migliore (per
   esempio un'altra codifica dello stesso brano). Molto probabile;
4. **AI** (casella, accesa se c'è l'AI della scansione), per i dubbi veri (per esempio una versione dal vivo e una in
   studio): riceve per ogni brano dell'iPhone al più 5 candidati del PC con titolo, artista, album, durata e
   **cartella**, e dice quale è la stessa registrazione, o nessuno, con la sicurezza e il motivo. Spuntato solo se
   l'AI è sicura. Senza AI, i dubbi si mostrano da controllare.

**Più copie dello stesso brano sul PC.** Con *Impostazioni → Generale → Cartelle preferite* (in ordine, separate da
punto e virgola: nomi di cartella, che valgono in qualsiasi punto del percorso, o percorsi interi) ogni associazione
sceglie la copia nella prima di quelle cartelle, poi nella seconda…: la proposta in rosso, *Associa sorgente*,
*Associa sorgenti* (nome della cartella, impronta, regole). Le copie con stessi tag e durata in cartelle diverse
contano come un candidato solo, quindi non sono un dubbio da far decidere all'AI. Senza cartelle preferite, vince il
percorso più corto.

Prima di scrivere mostra **una lista sola** con tutte le proposte: brano dell'iPhone, file del PC, **certezza** (certo,
molto probabile, probabile, da controllare), come e perché, con le spunte già messe per quelle certe o molto
probabili. Si può togliere o mettere ogni spunta (**un brano senza spunta resta com'è**) e, per la riga selezionata,
**Scegli un altro file…**. I brani senza un file sul PC sono in rosso: restano *solo sull'iPhone* (il programma non li
tocca mai da solo), oppure, con la casella in fondo, si associano dopo uno alla volta con la finestra di *Associa
sorgente*. La prima volta l'impronta di un brano dell'iPhone si legge in circa un quarto di secondo (un quarto d'ora
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
| `DISCOGS_TOKEN` | il token personale di Discogs, per *Verifica album online* con il catalogo Discogs; si manda solo nell'intestazione delle richieste a Discogs, mai altrove | Discogs non si usa (la casella è spenta) |
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
| `settings.json` | cartella della Libreria, ultime cartelle usate, AI della scansione e controlli tolti, lingua, percorso completo delle cartelle, cartelle nascoste, cataloghi di *Verifica album online*, posizione della finestra |
| `ai_profiles.json` | i profili AI (senza chiavi e senza indirizzi privati: quelli sono nella Gestione credenziali) |
| `secrets.json` | solo senza credential store: le chiavi |
| `scansioni\scansione_<data>.txt` | il rapporto di ogni scansione |
| `iphone_musica.json` | la musica dell'app Musica dell'iPhone all'ultima connessione (tag, durata, file sul telefono), per la scheda iPhone, la colonna *iPhone* e la scansione a telefono disconnesso |
| `iphone_in_attesa.json` | le azioni sull'iPhone in attesa di *Applica*: per file del PC (copia, ricopia, usa i tag, la spunta tolta) o per brano dell'iPhone (elimina, cambia i tag con i valori, ricopia e usa i tag scelti nella scheda iPhone); il formato 1 delle versioni precedenti si legge ancora |
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

- La copia sull'iPhone (*Copia da PC a iPhone*, con *Applica*) non ha impostazioni: l'identità della libreria e l'ancora
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

### Le cartelle della musica e la Libreria

1. *Impostazioni → Cartelle della musica* (`music_folders` in `settings.json`: per **nome del computer**, l'elenco
   `folders` in ordine e la cartella `library`, la Libreria). Vale per questo computer; le voci degli altri computer
   restano e non si usano.
2. Senza un elenco per questo computer: la Libreria sola, cioè `library_dir` in `settings.json` (che segue sempre
   la Libreria scelta, così una versione precedente del programma la trova ancora), altrimenti
   `%USERPROFILE%\Music\myEasyMP3toIPhone`.

Una cartella dell'elenco dentro un'altra (per esempio la Libreria dentro la cartella principale) si legge una volta
sola, con quella che la contiene; la stessa cartella non si aggiunge due volte, comunque scritta. Una cartella che non
c'è (disco scollegato) si salta: *La mia musica* e *Associa sorgenti* usano le altre e lo dicono.

Le impostazioni della prima versione nel registro di Windows si copiano una volta, solo se `settings.json` non
esiste.

### La lingua dell'interfaccia

1. *Impostazioni → Generale → Lingua dell'interfaccia* (`language` in `settings.json`: `it` o `en`), dal prossimo avvio.
2. Senza: italiano.

In inglese sono in inglese finestre, pulsanti, menu, messaggi, la barra di stato, i problemi e il rapporto di *Controlla la musica* e i motivi scritti dall'AI (il prompt le chiede l'inglese). Restano come sono i dati (titoli, artisti, album, percorsi), la console e questo README. Il codice resta scritto in italiano: i testi si traducono quando arrivano allo schermo con il catalogo `myeasymp3toiphone/i18n_en.py` (un testo nuovo nel codice va aggiunto lì: `tools/i18n_catalog.py` elenca quelli mancanti e un test lo controlla).

### Il percorso completo delle cartelle

*Impostazioni → Generale → Mostra il percorso completo delle cartelle* (`show_full_path` in `settings.json`): vale per
la colonna *Cartella* della scheda PC e *Cartella della sorgente* della scheda iPhone, subito. Senza: spento (il solo
nome della cartella; per una cartella di disco, "CD1", "Disk 2", "cd 2 - studio", anche quella sopra: `Album\CD1`).
Le colonne dei file mostrano sempre il solo nome; il suggerimento delle celle mostra sempre il percorso completo.

### Le cartelle nascoste

1. `hidden_folders` in `settings.json`: si aggiunge con tasto destro → *Nascondi la cartella* nella scheda PC o con
   *Impostazioni → Cartelle della musica → Cartelle escluse*, e si toglie con *Cartelle nascoste (N)…* o nelle
   Impostazioni. Vale subito, per ogni cartella aperta (anche la Libreria), con le sottocartelle, anche quando
   *Associa sorgenti* e *Controlla la musica* dell'iPhone rileggono le cartelle; le maiuscole non contano.
2. Senza: nessuna cartella nascosta.

### Le cartelle preferite

1. *Impostazioni → Generale → Cartelle preferite* (`preferred_folders` in `settings.json`, una lista in ordine): con
   più copie di un brano sul PC, le associazioni scelgono la copia nella prima cartella della lista, poi nella
   seconda…; una voce con `\`, `/` o `:` è un percorso (con le sottocartelle), senza è il nome di una cartella in
   qualsiasi punto del percorso; le maiuscole non contano. Vale subito.
2. Poi l'ordine delle **cartelle della musica** di questo computer: vince la copia nella cartella più in alto.
3. Senza, o per le copie fuori da tutte: il percorso più corto (con l'impronta, prima la copia con i tag più simili).

### Gli altri nomi per "Artisti vari"

1. *Impostazioni → Generale → Altri nomi per "Artisti vari"* (`various_artists` in `settings.json`, separati da punto e
   virgola nel campo): valgono come "AA.VV." negli elenchi Artisti e Album delle due schede e per le playlist delle
   compilation, subito. Maiuscole, accenti, spazi e punteggiatura non contano.
2. Sempre, anche senza: "AA.VV.", "Artisti vari", "Autori vari", "Vari artisti", "Various Artists", "Various", "VA",
   "Vari". Solo questi valgono nel confronto con l'iPhone (colonna *Sul PC*), perché l'iPhone non conosce gli altri. In
   console i nomi aggiunti non valgono.

### I cataloghi di "Verifica album online"

1. Le caselle della finestra di *Verifica album online*: valgono per quella verifica e si ricordano in `settings.json`
   (`album_services`, nell'ordine fisso Deezer, Apple Music, Discogs, MusicBrainz; `album_ai` per l'AI).
2. Al primo uso, e con un `settings.json` senza `album_services`: Deezer e Apple Music; l'AI spenta.
3. Discogs vale solo con `DISCOGS_TOKEN` impostata (file delle variabili o sistema, come ogni variabile); senza, la
   casella è spenta anche se era scelta.
4. L'AI è quella della scansione (*Impostazioni → Generale → AI della scansione*); senza un profilo la casella è spenta.
5. Il paese del negozio di Apple Music è quello delle impostazioni internazionali di Windows (`it-IT` → `IT`); se non
   si legge, `US`.

### La cartella aperta all'avvio

1. `--open <cartella>` sulla riga di comando (vale per quell'avvio, non si salva come scelta: ma quella cartella
   diventa l'ultima usata).
2. Altrimenti **quello che era aperto l'ultima volta** (`last_opened` in `settings.json`, salvato ogni volta che le
   cartelle finiscono di caricarsi): una cartella aperta da sola, o `*` per le cartelle della musica.
3. Se l'ultima cartella non è più disponibile (disco scollegato, cartella cancellata), e la prima volta: le
   **cartelle della musica** di questo computer (quelle che ci sono), con un avviso nella barra di stato se l'ultima
   cartella manca.
4. Senza nessuna cartella della musica: niente, con l'invito ad aprirne una.

La finestra *Apri cartella* parte invece da `last_folder`, l'ultima cartella scelta lì.

### Opzioni della finestra (`myEasyMP3toIPhone`)

| Opzione | Effetto | Salvata? |
|---|---|---|
| `--open <cartella>` | apre quella cartella all'avvio, al posto delle cartelle della musica (in sola lettura) | no |
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
| `myeasymp3toiphone/tags.py` | lettura di tutti i tipi di tag (ID3v2, APEv2, ID3v1, MP4, Vorbis, ASF, RIFF INFO), scrittura dei tag e delle copertine (mutagen), ID3 v2.3 |
| `myeasymp3toiphone/library.py` | scansione delle cartelle, raggruppamento, nomi dei file, copia e spostamento |
| `myeasymp3toiphone/albumcheck.py` | *Verifica album online*: i cataloghi (Deezer, Apple Music, Discogs, MusicBrainz e Cover Art Archive), l'ordine dei servizi, l'abbinamento delle tracce |
| `myeasymp3toiphone/scan.py` | *Controlla la musica*: regole, brani duplicati, confronto con l'iPhone, analisi AI, correzioni |
| `myeasymp3toiphone/artist_names.py` | le forme dei nomi d'artista: varianti certe, dubbi (AI, MusicBrainz), duetti |
| `myeasymp3toiphone/overlay.py`, `tag_cache.py` | le modifiche dei tag in sospeso; la cache dei tag e delle impronte |
| `myeasymp3toiphone/ai.py` | i fornitori di AI (Ollama, Azure, OpenAI via HTTP; Anthropic con l'SDK ufficiale) |
| `myeasymp3toiphone/iphone.py` | l'iPhone (pymobiledevice3): connessione, musica dell'app Musica, file, brani fantasma |
| `myeasymp3toiphone/phone_sync.py` | il protocollo di sincronizzazione di Apple (AirTrafficControl) per scrivere nell'app Musica |
| `myeasymp3toiphone/phone_actions.py` | invia, rimpiazza, cambia tag, elimina sull'iPhone |
| `myeasymp3toiphone/phone_library.py` | il database dell'app Musica, l'elenco salvato, il confronto con il PC |
| `myeasymp3toiphone/provenance.py`, `adoption.py` | impronte dell'audio, registro della provenienza, *Associa sorgente/i* |
| `myeasymp3toiphone/pending.py`, `gui/apply_dialog.py` | le azioni sull'iPhone in attesa e la finestra di *Applica* |
| `myeasymp3toiphone/i18n.py`, `i18n_en.py` | la lingua dell'interfaccia: la traduzione inglese dei testi e gli agganci a Qt |
| `myeasymp3toiphone/config.py` | cartella dati, impostazioni, profili AI, chiavi, `$NOME` |
| `myeasymp3toiphone/env_file.py` | il file delle variabili |
| `myeasymp3toiphone/environment.py` | il rapporto delle variabili (`--env`, *Informazioni*) |
| `myeasymp3toiphone/home_backup.py` | la copia della cartella dati prima di un cambio di formato |
| `myeasymp3toiphone/startup.py` | l'avvio: copia, variabili, migrazioni, registro, log |
| `myeasymp3toiphone/gui/` | l'interfaccia PySide6 (la tabella dei brani è un modello Qt, `track_model.py`: veloce anche con decine di migliaia di brani; `widgets.py` i filtri a pulsanti e la barra delle azioni; `checks_panel.py` la linguetta Controlli; `icons.py` le icone; `theme.py` i colori) |
