# TODO

## Le parole: "connetti" per il cavo, "sorgente" per la provenienza

Oggi "collega" vuol dire due cose: il cavo ("Collega iPhone") e la provenienza ("Collega al PC", "Collega a un file
del PC", "Scollega dal PC"). Per il cavo **connetti / connesso / disconnetti**; per la provenienza **sorgente /
associa**: il pulsante per tutti i brani "Associa sorgenti…", col tasto destro "Associa sorgente…" e "Togli
sorgente", la colonna *Origine* diventa *Sorgente* (e "Solo sull'iPhone" = senza sorgente). Da applicare a interfaccia,
messaggi e README.

## Il pulsante dell'iPhone: "Connetti iPhone" (verde) / "Disconnetti iPhone" (rosso)

Oggi il pulsante dice sempre "Collega iPhone" e lo stato è solo nel testo accanto: non si capisce.
- iPhone non connesso: pulsante **verde "Connetti iPhone"**; durante la connessione "Connessione…";
- connesso: pulsante **rosso "Disconnetti iPhone"**, che chiude la connessione;
- dopo *Disconnetti* il programma **non** si riconnette da solo quando vede il telefono (oggi lo fa ogni 3 secondi):
  resta disconnesso finché si preme *Connetti* o si stacca e riattacca il cavo;
- lo stato si vede anche fuori dalla scheda iPhone (per esempio "iPhone ●" verde nel titolo della scheda), così dalla
  scheda PC si sa se l'invio è possibile.

## "Associa sorgente" (tasto destro nella scheda iPhone)

Sostituisce l'attuale *Collega a un file del PC…* (un elenco semplice dei 5 file più simili, filtrati per titolo).
- Nome della voce: **Associa sorgente…**, per un brano alla volta.
- Una **tabella** di brani del PC tra cui scegliere: Titolo | Artista | Album | Durata | **Percorso** (ben visibile)
  | Perché; più "Scegli un altro file…".
- Su un brano che ha già una sorgente: si mostra quella attuale e si chiede se sostituirla.
- **Il primo, già selezionato, è il più probabile**: si accetta con *Associa* senza cambiare niente. Ordine:
  1. **impronta dell'audio** uguale (certo): cercata tra tutti i file con durata entro 2 s, **senza filtro sul
     titolo** (oggi le compilation con titoli diversi restano fuori); impronte del PC dalla cache, quelle mancanti
     calcolate al momento (pochi file); quella dell'iPhone dalla memoria o letta dal telefono se è collegato;
  2. altrimenti titolo, artista e durata (il punteggio di oggi);
  3. se i primi due candidati sono vicini, **decide l'AI** della scansione (una richiesta, il brano e i suoi
     candidati con la cartella), e la colonna *Perché* riporta il motivo.
- Calcolo in background (impronte e AI richiedono qualche secondo), poi la finestra.
- Nel registro il collegamento ha il "come" giusto: *impronta* o *ai* se si accetta la proposta, *a mano* se si
  sceglie un altro brano.

**Versione "per cartella"**: con più brani selezionati (per esempio un album intero) la voce diventa **Associa
sorgente da una cartella…**:
- si sceglie la cartella del PC da cui vengono (proposta: quella dove stanno già i brani collegati dello stesso album,
  o la più probabile secondo le impronte);
- per ogni brano selezionato si cerca il file in quella cartella e nelle sue sottocartelle (impronta, poi titolo e
  durata; i brani possono essere di album diversi) e si mostra una tabella di riepilogo: brano dell'iPhone → file
  trovato (con il percorso e il "perché"), da confermare;
- i brani **senza** un file nella cartella sono evidenziati con un avviso, e per ognuno si propone di associarlo uno
  alla volta (la finestra di *Associa sorgente* per quel brano), oppure di lasciarlo così.

## "Cambia tag" sull'iPhone: manca la spunta Compilation

La finestra *Cambia tag* della scheda iPhone (titolo, album, genere, anno, numeri) non ha la casella
**Compilation**, che invece c'è nell'editor dei tag della scheda PC. Va aggiunta, a tre stati come nell'editor (sì,
no, valori diversi), con l'artista dell'album: una compilation vuole anche "Artisti vari".
- Sul telefono `update_track` accetta `is_compilation` (campo sicuro secondo rustunes, docs/05 §2), ma cambia solo
  il brano: la riga dell'album resta com'è. Va provato sul telefono se basta a tenere insieme l'album nell'app
  Musica; se non basta, per i brani già sull'iPhone la strada è *Rimpiazza con la versione del PC* (che manda brano e
  album con la spunta, provato).
- Anche l'**artista dell'album** non si cambia oggi da *Cambia tag* (rinominerebbe l'artista per tutti i suoi brani):
  per una compilation va spiegato nella finestra che "Artisti vari" si mette nella scheda PC e poi *Rimpiazza*.

## Cambiare i tag da una parte propone di cambiarli anche dall'altra

Quando un brano è collegato (registro della provenienza), una modifica dei tag da un lato chiede se va fatta anche
sull'altro:
- **dalla scheda PC** (editor dei tag, correzioni della scansione, Verifica album) su brani collegati a brani
  dell'iPhone: "Aggiornare anche i N brani sull'iPhone?". Sì: i campi sicuri (titolo, album, genere, anno, numeri,
  compilation) con *Cambia tag* sull'iPhone; artista e artista dell'album, che sull'iPhone non si cambiano senza
  rischi, con *Rimpiazza* (detto prima: si perdono ascolti e playlist del brano). Senza iPhone collegato, o con il
  passo 5, i brani restano ⟳ "in attesa di aggiornamento" e si applicano dopo;
- **dalla scheda iPhone** (*Cambia tag*) su brani collegati a file di questo PC: "Salvare le stesse modifiche anche
  per i file del PC?". Sì: le modifiche vanno in sospeso sui file collegati (overlay: i file non cambiano mai), anche
  se non sono nella cartella aperta;
- la domanda dice quanti brani sono collegati e quanti no (questi cambiano da una parte sola); una casella "non
  chiederlo più, fallo sempre / mai" si ricorda nelle impostazioni (e va nella sezione "Quale valore vince" del README).

## Una sorgente sparita dal PC (per esempio un doppione cancellato)

Il programma non cancella mai i file del PC; li cancella l'utente (per esempio un doppione trovato con *Controlla la
musica*). All'apertura della cartella o alla connessione, i brani dell'iPhone la cui sorgente non c'è più (*file non
trovato*) si segnalano con un avviso che li elenca e offre, per tutti o uno per uno:
- **un'altra sorgente**: la finestra di *Associa sorgente*, con prima proposta la copia con lo stesso audio (impronta);
- **lasciarli senza sorgente** (orfani: tornano "solo sull'iPhone");
- **eliminarli anche dall'iPhone**.
Il contrario no: cancellare un brano (o un doppione) dall'iPhone non cambia mai niente sul PC. In generale i doppioni
sul PC e quelli sull'iPhone si gestiscono in modo del tutto separato.

## Passo 5: spunte, stato "in attesa" e barra Applica

Già deciso: nella colonna *iPhone* della scheda PC una spunta = "voglio questo brano sull'iPhone".
- Stati: ✔ verde (c'è, uguale), ⟳ arancio (c'è, diverso), vuoto (non c'è); **in attesa**: ＋ blu (da inviare),
  － rosso (da togliere), ⟳ blu (da aggiornare), con la riga in leggera tinta azzurra o rosa. Forma e colore
  diversi da quelli "fatti".
- Spunta anche su artisti e album interi negli elenchi in alto, a tre stati (tutti, alcuni ◐, nessuno), con il
  segno "in attesa" se dentro c'è qualcosa da applicare.
- Una barra in fondo quando c'è qualcosa in attesa: "In attesa: N da inviare, N da togliere, N da aggiornare —
  [Annulla le modifiche] [Applica…]"; *Applica* mostra l'elenco e chiede conferma, poi fa tutto in poche sessioni.
- Le modifiche in attesa si salvano nella cartella dati (non si perdono chiudendo il programma).
- Togliere una spunta agisce solo sui brani **collegati** (registro della provenienza); i brani di origine
  sconosciuta non si toccano mai per una spunta.

## Varianti dei nomi degli artisti (dopo il passo 5)

"Battiato", "Franco Battiato", "Battiato Franco", "F. Battiato", accenti, errori di battitura, duetti. Decisioni già
prese: livelli regole certe → AI con il contesto (album, anni, titoli; gruppi per cognome) → MusicBrainz (alias)
facoltativo; **vince la forma più usata**; **duetti: artista e artista album = artista principale, ospiti nel titolo**
"Titolo (feat. Ospite)" (l'app Musica non gestisce artisti multipli); album intero in coppia: principale = primo
nome. Risultato come problemi della scansione con la correzione, poi *Rimpiazza* per l'iPhone. Attenzione ai nomi veri
con iniziali ("B.B. King"). Numeri misurati: 2.696 nomi, 4 per ordine delle parole, 56 "solo cognome", 33 quasi
uguali, 47 con iniziali, 656 duetti.

## Scansione: un nome chiaro e la scelta di cosa controllare (con i brani duplicati)

- Il pulsante **"Scansione"** è ambiguo (la spiegazione nel suggerimento è buona, il nome no): diventa **"Controlla
  la musica"** (deciso).
- Nella finestra che si apre, dopo la scelta di *cosa* scansionare (cartella aperta o iPhone), una serie di **caselle**
  per scegliere *quali controlli* fare, ognuna con una riga di spiegazione: file che non si aggiornano, album con pochi
  brani, collezioni divise su più album, artisti scritti in modi diversi, tag mancanti, file illeggibili e **brani
  duplicati**. Le scelte si ricordano tra un avvio e l'altro.
- **Brani duplicati** = **lo stesso brano**, non necessariamente lo stesso file: con l'impronta dell'audio (già in
  cache) le copie identiche anche con tag e nomi diversi; in più lo stesso brano in file diversi (un MP3 e un FLAC
  dello stesso pezzo, due codifiche, un remaster uguale nella durata), senza confondere le versioni davvero diverse
  (dal vivo, remix): l'AI (locale) vede **solo le coppie già sospette** per altri criteri (durata entro 2 s, titolo e
  artista simili, audio diverso), mai tutti i brani. Oggi la regola "Brani doppi" cerca solo dentro lo stesso album. Nessuna
  correzione automatica: quale tenere lo decide l'utente (*Mostra i brani*). Dato misurato: 2.718 brani dell'iPhone
  hanno due o più copie con lo stesso audio nella cartella del PC.

## Brani "fantasma" sull'iPhone

Brani nel database dell'app Musica il cui file non c'è (uno trovato: `F05/W0084007.mp3`, OBJECT_NOT_FOUND).
Segnalarli (scheda iPhone, scansione) e proporre di eliminarli (`delete_track`).

## Le proposte dubbie di "Collega al PC"

Sui dati veri restano 44 proposte non spuntate (regole senza un candidato chiaro). Controllare cosa ne dice l'AI
della scansione e se i candidati sono giusti (versioni dal vivo, remaster). In attesa: l'utente non ha ancora fatto
*Collega al PC* con la build nuova.

## Invio di M4A in Apple Lossless (ALAC) — solo se servirà

Oggi si inviano MP3, FLAC e AAC. ALAC vuole il suo formato di inserimento (rustunes `protocol/alac.rs`: tra
l'altro `gapless_heuristic_info`, `analysis_inhibit_flags`). Per ora non serve: i 20 M4A della musica dell'utente
sono tutti AAC.

## L'app Musica che non si aggiorna da sola

Dopo un invio l'app Musica, se è aperta, va chiusa e riaperta. iTunes e CopyTrans mandano probabilmente un avviso di
fine sincronizzazione (notification proxy, `com.apple.itunes-mobdev.syncDidFinish`): da provare, non è documentato
e rustunes non lo usa.

## Tabella dei brani del PC con molte righe

Riempire la tabella costa ~1,7 s per 30.000 brani (270.000 celle). Un modello Qt (QAbstractTableModel) lo
eliminerebbe; tocca selezione, ordinamento e scorrimento (43 punti in `main_window.py`).

## Interfaccia anche in inglese

Un'opzione in *Impostazioni* per la lingua dell'interfaccia: italiano (oggi l'unica) o inglese. Tutti i testi
dell'interfaccia e i messaggi oggi sono scritti in italiano dentro il codice: vanno raccolti in un catalogo (le
traduzioni di Qt, `tr()`/`.ts`, o un dizionario del programma), con la traduzione italiana di Qt già caricata
(`theme.install_italian`) scelta in base alla lingua. Nuova impostazione: va nella sezione "Quale valore vince" del
README. Da decidere: se anche README, rapporti della scansione e prompt per l'AI cambiano lingua.
