# TODO

## ⟳ "tag diversi": una tabella invece della spiegazione

Oggi il suggerimento di ⟳ (colonna *Sul PC* della scheda iPhone, colonna *iPhone* della scheda PC) è un elenco di
righe "Campo: sul PC "…", sull'iPhone "…"". Va sostituito da una tabella (i suggerimenti di Qt accettano HTML):
- **riga 1**: il brano "sospettato" di essere l'equivalente: nella scheda iPhone il file del PC (percorso), nella
  scheda PC il brano dell'iPhone (artista — titolo, album); e **come** è stato abbinato: dal registro della
  provenienza (*inviato*, *impronta*, *a mano*… = certo) o solo per tag (artista, album, titolo = probabile);
- **poi una riga per campo**: Campo | Sul PC | Sull'iPhone, con tutti i tag confrontati (titolo, artista, artista
  album, album, anno, genere, numeri, compilation) e i valori diversi evidenziati;
- per ✔ la stessa tabella, senza evidenziazioni.

## "Associa sorgente" (tasto destro nella scheda iPhone)

Sostituisce l'attuale *Collega a un file del PC…* (un elenco semplice dei 5 file più simili, filtrati per titolo).
- Nome della voce: **Associa sorgente…**, per un brano alla volta.
- Una **tabella** di brani del PC tra cui scegliere: Titolo | Artista | Album | Durata | **Percorso** (ben visibile)
  | Perché; più "Scegli un altro file…".
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

## Doppioni sul PC con le impronte

2.718 brani dell'iPhone hanno due o più copie con lo stesso audio nella cartella del PC. Una regola della
scansione che li trova con l'impronta dell'audio (già in cache), anche con tag e nomi diversi; nessuna correzione
automatica: quale tenere lo decide l'utente.

## Brani "fantasma" sull'iPhone

Brani nel database dell'app Musica il cui file non c'è (uno trovato: `F05/W0084007.mp3`, OBJECT_NOT_FOUND).
Segnalarli (scheda iPhone, scansione) e proporre di eliminarli (`delete_track`).

## Le proposte dubbie di "Collega al PC"

Sui dati veri restano 44 proposte non spuntate (regole senza un candidato chiaro). Controllare cosa ne dice l'AI
della scansione e se i candidati sono giusti (versioni dal vivo, remaster).

## Il vecchio invio tramite iTunes

Non è più nella scheda iPhone. Decidere se togliere del tutto `itunes.py`, i suoi test, le impostazioni `itunes_dir`
e `itunes_sync`, il campo in *Impostazioni*, la migrazione in `startup.py` e il pulsante per installare ffmpeg.

## Invio di M4A in Apple Lossless (ALAC)

Oggi si inviano MP3, FLAC e AAC. ALAC vuole il suo formato di inserimento (rustunes `protocol/alac.rs`: tra
l'altro `gapless_heuristic_info`, `analysis_inhibit_flags`).

## L'app Musica che non si aggiorna da sola

Dopo un invio l'app Musica, se è aperta, va chiusa e riaperta. iTunes e CopyTrans mandano probabilmente un avviso di
fine sincronizzazione (notification proxy, `com.apple.itunes-mobdev.syncDidFinish`): da provare, non è documentato
e rustunes non lo usa.

## Tabella dei brani del PC con molte righe

Riempire la tabella costa ~1,7 s per 30.000 brani (270.000 celle). Un modello Qt (QAbstractTableModel) lo
eliminerebbe; tocca selezione, ordinamento e scorrimento (43 punti in `main_window.py`).

## GitHub

I commit dopo `3185cf8` e il tag `v0.1.2` sono solo locali: fare il push quando si vuole.
