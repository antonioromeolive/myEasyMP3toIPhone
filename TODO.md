# TODO

## Il pulsante "Collega iPhone" deve dire se l'iPhone è collegato

Oggi il pulsante dice sempre "Collega iPhone" e lo stato è solo nel testo accanto: non si capisce. Quando l'iPhone è
collegato il pulsante deve mostrarlo, con un colore diverso (per esempio verde "Connesso all'iPhone"); scollegato
torna "Collega iPhone"; durante il collegamento "Collegamento…". Lo stesso stato si potrebbe vedere anche fuori dalla
scheda iPhone (barra di stato o titolo della scheda), così si sa dalla scheda PC se l'invio è possibile.

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

**Versione "per cartella"**: con più brani selezionati (per esempio un album intero) la voce diventa **Associa
sorgente da una cartella…**:
- si sceglie la cartella del PC da cui vengono (proposta: quella dove stanno già i brani collegati dello stesso album,
  o la più probabile secondo le impronte);
- per ogni brano selezionato si cerca il file in quella cartella (impronta, poi titolo e durata) e si mostra una
  tabella di riepilogo: brano dell'iPhone → file trovato (con il percorso e il "perché"), da confermare;
- i brani **senza** un file nella cartella sono evidenziati con un avviso, e per ognuno si propone di associarlo uno
  alla volta (la finestra di *Associa sorgente* per quel brano), oppure di lasciarlo così.

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

## GitHub

I commit dopo `3185cf8` e il tag `v0.1.2` sono solo locali: fare il push quando si vuole.
