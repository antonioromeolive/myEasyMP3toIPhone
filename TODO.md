# TODO

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
