# Controlli: cosa facciamo oggi e cosa manca (lato PC)

Stato al 27/11/2026, letto dal codice (commit b270943). Scopo: rimettere ordine nei Controlli prima di cambiare
altro codice. Prima l'inventario di quello che c'è, nell'ordine in cui gira; poi l'analisi di cosa manca o non torna;
in fondo le decisioni da prendere.

## 1. Premesse

- **Perimetro di questo lavoro: solo il PC.** I controlli guardano i brani della scheda PC (la selezione, o tutto) e
  le correzioni restano sul PC: in sospeso nell'overlay e nei file solo dopo l'elenco approvato (`PcWriteDialog`).
  Niente si propaga da solo all'iPhone. Fuori perimetro per ora: I1–I4 (confronto con l'iPhone) e la parte iPhone di
  `check_flow.plan_apply`.
- **I controlli vedono i tag "come saranno"**: i tag dei file più le modifiche in sospeso dell'overlay
  (`Track.tags`); solo R2 guarda anche quelli del file (`original_tags`).
- **Cosa sappiamo dell'app Musica** (da `library.phone_group_key`, provato il 24/11/2026, e da `TODO.md`, 26/11/2026):
  - un nome "uguale" a uno che ha già (stesse lettere senza maiuscole, accenti, spazi, zeri davanti ai numeri)
    attacca il brano all'album o all'artista che c'è, e **tiene la grafia che ha già**: una correzione delle sole
    maiuscole inviata dopo non si vede;
  - "AA.VV.", "Artisti vari", "Various Artists" sono **artisti diversi** (sul telefono erano tre): conta dentro lo
    stesso album, che si divide; tra album diversi è solo una voce in più nell'elenco Artisti;
  - l'elenco Compilation segue la riga dell'album (artista dell'album + spunta compilation), non la spunta dei brani;
  - un album senza artista dell'album, con brani di artisti diversi, diventa un album per artista.

  Conseguenza: **la grafia giusta di artisti e album va decisa sul PC prima del primo invio.** Una base del PC che
  contiene due grafie dello stesso nome manda all'iPhone quella che arriva prima.

## 2. Come gira un controllo oggi

`gui/check_options.py` (le scelte) → `gui/scan_dialog.py` `ScanLauncher.run` → `_start_local` → `scan.scan_tracks`.

| # | Passo | Dove |
|---|---|---|
| 1 | Perimetro: brani selezionati, oppure artisti/album scelti, oppure tutto | `check_options.scope` |
| 2 | Impronte dell'audio (solo con "Brani duplicati") | `adoption.pc_fingerprints` |
| 3 | Raggruppamento per album: `Track.album_key` | `library.assign_groups` |
| 4 | Regole, in quest'ordine: R5 → R2, R3 → R7, R8 → R6 → R9, R10 → R11 → R12, R13 → R14 | `scan.rule_issues` (`scan.py:879`) |
| 5 | Sovrapposizioni: via R13 dentro un R11, via R10 dentro una collezione divisa, nota su R9 | `scan.merge_overlapping` (`scan.py:851`) |
| 6 | R16 nomi d'artista dubbi (con MusicBrainz se scelto; senza AI in questo passo) | `scan.detect_artist_doubts` (`scan.py:767`) |
| 7 | R15 stesso brano più volte (salta i file già in R7/R8) | `scan.detect_same_songs` (`scan.py:1029`) |
| 8 | Verifica online: W1, W2, W3 per album | `scan_dialog.online_check`, `check_flow.online_issues` (`check_flow.py:97`) |
| 9 | Analisi AI in background: `ai_review` (conferma/scarta le regole, ne aggiunge) e R16 di nuovo con l'AI | `scan_dialog._start_ai` (`scan_dialog.py:292`) |
| 10 | Problemi per album, righe "ora → diventa"; le righe di sole maiuscole si tolgono; `elsewhere` | `check_flow.group_by_album` (`check_flow.py:253`) |
| 11 | "Va bene così": problemi nascosti per album e tipo | `check_flow.filter_accepted`, `accepted.py` |
| 12 | Applica: correzioni unite per brano (stesso campo: vince l'ultima), overlay, poi `PcWriteDialog` | `check_flow.plan_apply` (`check_flow.py:355`), `check_results._run_plan` |

Con una selezione, solo R9/R10 ricevono anche il resto della libreria (`album_context`): tutte le altre regole
vedono solo i brani scelti.

## 3. Inventario dei controlli

Nell'ordine in cui girano. "Confronta con" rimanda alla sezione 4.

### Casella "File illeggibili"

**R5 — File illeggibili** · `scan.py:308` · gravità alta · nessuna correzione
- Trova: brani con errore di lettura (`Track.error`): danneggiati, non audio, solo online (OneDrive).
- Cosa fare: a mano (riscaricare, "Mantieni sempre su questo dispositivo").

### Casella "File che non si aggiornano"

**R2 — Vecchio tag ID3v1 diverso** · `scan.py:270` · bassa
- Trova: MP3 con ID3v1 il cui titolo, artista o album (primi 30 caratteri) è diverso dall'ID3v2.
- Confronta con: `_plain` (quindi maiuscole e punteggiatura non contano).
- Correzione: togli l'ID3v1 dai file del PC (dopo `PcWriteDialog`; i valori passano prima nell'ID3v2). Le copie per
  l'iPhone ne sono già senza (`tags.prepare_copy`).

**R3 — Tag APE** · `scan.py:270` · bassa
- Trova: MP3 con un tag APE (qualunque contenuto).
- Correzione: come R2.

### Casella "Brani duplicati"

**R7 — Copie "Titolo (2)"** · `scan.py:386` · alta · nessuna correzione
- Trova: `Nome (2).mp3` accanto a `Nome.mp3`, con lo stesso `album_key`.

**R8 — Stesso numero e titolo nell'album** · `scan.py:386` · media · nessuna correzione
- Trova: brani con stesso `album_key`, disco, numero di traccia e titolo (`_plain`), salvo una copia per formato
  (FLAC + MP3 va bene).

**R15 — Stesso brano più volte** · `scan.py:1029` · bassa · nessuna correzione · gira dopo l'AI delle regole
- Trova: stessa impronta audio, oppure stesso artista (`artist_norm`) e titolo senza aggiunte (`title_core`), durata
  entro 2 s e stesse parole di versione (live, remix…). Segnalato solo se due copie sono nello stesso album **e**
  nello stesso formato. Un problema per artista. Salta i file già in R7/R8.

### Casella "Tag mancanti"

**R6 — Brani senza titolo, album o artista** · `scan.py:342` · media · un problema per cartella
- Trova: titolo vuoto, album vuoto, oppure artista e artista dell'album entrambi vuoti.
- Correzione (se si riesce): album dal nome della cartella (senza "(anno)"), artista dalla cartella sopra, titolo dal
  nome del file senza "NN - ".
- Non trova: valori segnaposto ("Unknown Artist", "Traccia 01", "Track 1").

### Casella "Album con pochi brani"

**R9 — Numeri di traccia mancanti** · `scan.py:505` · alta se manca almeno metà, altrimenti media · nessuna correzione
- Trova: buchi nei numeri fino al più alto o al totale dichiarato, disco per disco; numerazione unica se i dischi non
  ripetono numeri (cofanetti). Album in più formati: conta la copia più completa (`album_gaps`). Immagini FLAC+CUE
  escluse. Album giudicato intero anche fuori dalla selezione.
- Cosa fare: Verifica online.

**R10 — Album di 1-2 brani** · `scan.py:505` · bassa · nessuna correzione
- Tolto da `merge_overlapping` se i suoi file sono dentro una collezione divisa.

### Casella "Collezioni divise su più album"

**R11 — Una cartella, più album** · `scan.py:576` · alta
- Trova: una cartella con almeno 2 brani in `album_key` diversi ma lo stesso nome d'album (`album_norm`, quindi anche
  "X CD1"/"X CD2").
- Correzione su tutti i brani della cartella: album = il nome più usato **senza** "CD n"; artista dell'album = quello
  più usato tra i brani che lo hanno, altrimenti l'artista principale dei duetti, altrimenti "Artisti vari" (+ spunta
  compilation) se gli artisti sono diversi, altrimenti l'artista più usato.

**R12 — Lo stesso album scritto in modi diversi (stesso artista)** · `scan.py:630` · alta
- Trova: più `album_key` con lo stesso `album_norm` e lo stesso `artist_norm` dell'artista.
- Correzione: album = nome più usato senza "CD n"; numero del disco dal nome; artista dell'album = il più usato tra
  "artista dell'album, o artista".

**R13 — Lo stesso album diviso tra artisti** · `scan.py:630` · media, solo quando è probabile (dal 28/11/2026: il
"forse" senza correzione dava falsi allarmi su nomi comuni come "Essentials")
- Trova: più `album_key` con lo stesso `album_norm` e artisti diversi.
- Correzione solo se nessun brano ha l'artista dell'album e (una cartella sola o un anno solo): "Artisti vari" +
  spunta compilation + nome unico. Tolto da `merge_overlapping` se è dentro un R11.

### Casella "Artisti scritti in modi diversi"

**R14 — Varianti certe** · `scan.py:687` · media
- Trova: `display_artist` (artista dell'album, o artista) con la stessa `variant_key` (senza maiuscole, accenti,
  punteggiatura, "the", ordine delle parole) ma scritti in modo diverso. **Salta le varianti di sole maiuscole.**
- Correzione: ovunque la grafia più usata (`best_spelling`), in artista e artista dell'album.

**R16 — Forse lo stesso artista** · `scan.py:767` · media se confermato, bassa se "da controllare"
- Trova: coppie dubbie tra nomi non duetti: solo il cognome, iniziali, quasi uguali (somiglianza ≥ 0,88)
  (`artist_names.candidate_pairs`). Decide MusicBrainz (se scelto), poi l'AI (in background); altrimenti "Forse".
- Correzione: la forma con più brani.

### Verifica online (cataloghi: MusicBrainz, Discogs, …)

**W1 — Brani che mancano rispetto all'edizione** · `check_flow.py:97` · media · nessuna correzione (non per CUE)
**W2 — Tag diversi dal catalogo** · `check_flow.py:97` · bassa
- Campi: titolo, artista, artista dell'album, album, anno, numeri e totali di traccia e disco (CUE: solo album,
  artista dell'album, anno). Le differenze di sole maiuscole non contano (`same_value`).
**W3 — Album non trovato** · non è più un problema (28/11/2026): `check_flow.online_note`, una riga del rapporto
e il conto nell'intestazione dei risultati

### Analisi AI

**AI — Problemi trovati dall'AI** · `scan.py:1389` · tipi: non aggiornato, album incompleto, collezione divisa,
duplicato, tag mancanti
- Riceve una tabella per album (raggruppata per artista dell'album) e i problemi delle regole; ne scarta alcuni
  (nota `ai_note`, il problema resta) e ne aggiunge altri.
- Correzione: album, artista dell'album, artista, anno, genere **su tutti i brani** degli album indicati; mai per i
  duplicati.

### "Va bene così"

`accepted.py` · per album (artista dell'album + album, con `album_norm`/`artist_norm`) e tipo (R9, R12…, "W", AI_…,
tutto l'album). Nasconde il problema e fa saltare AI e Verifica online su quell'album.

### Numeri che non ci sono più

R1 e R4 (sola lettura, ID3 v2.4/v2.2) sono ancora descritti nella docstring di `scan.py` ma non esistono. R17
(duetti) è stato tolto e resta solo per i "va bene così" già salvati.

## 4. Le cinque idee di "uguale"

| Funzione | Cosa ignora | Chi la usa |
|---|---|---|
| `library.group_name`, `artist_group_key` (`library.py:330`, `:164`) | maiuscole, accenti, spazi; **tutti gli "artisti vari" sono uno** | `Track.album_key`: il raggruppamento su cui lavorano **tutte** le regole |
| `scan._plain`, `album_norm`, `artist_norm` (`scan.py:166`) | in più: punteggiatura, "&" = "and", "CD n", "the" | R2, R8, R11, R12, R13, R15 |
| `artist_names.variant_key` (`artist_names.py:48`) | in più: ordine delle parole | R14, R16, artista principale dei duetti, gruppi per l'AI |
| `check_flow.same_value` (`check_flow.py:85`) | maiuscole | filtro di **tutte** le righe di correzione, W2 |
| `library.phone_group_key` (`library.py:171`) | maiuscole, accenti, spazi, zeri davanti; gli "artisti vari" restano diversi | solo il lato iPhone |

## 5. Analisi: cosa manca o non torna

Ogni punto ha un requisito proposto (REQ) e una priorità. Quelli decisi rimandano alla sezione 7, quelli aperti alla
sezione 8.

### A. Differenze che il raggruppamento nasconde (priorità alta)

**A1. Sole maiuscole, accenti, spazi in artista, artista dell'album, album.** "Queen"/"queen", "Pérez"/"Perez",
"Live  at X"/"Live at X" diventano lo stesso `album_key`, quindi:
- R12/R13 non le vedono (ci arrivano già unite);
- R14 salta apposta le varianti di sole maiuscole;
- `same_value` toglie le righe di sole maiuscole anche quando una regola le propone.

Sull'iPhone vince la grafia inviata per prima: due grafie sul PC portano a una grafia a caso sull'iPhone, e
correggerla dopo dal PC non basta.
→ **REQ-1 (deciso: D-1, D-2, D-3)**: un controllo "stesso nome scritto in modi diversi" che lavora sulle grafie
esatte (non su `album_key`), per artista, artista dell'album e album, e propone una grafia unica.

**A2. "Artisti vari" scritto in modi diversi dentro lo stesso album.** Sul PC "AA.VV.", "Artisti vari", "Various
Artists" sono un artista solo (`artist_group_key`): un album con brani "AA.VV." e brani "Artisti Vari" è un album solo
e nessuna regola lo segnala. Sull'iPhone sono due album (caso vero: "100 Greatest Male Voices", 93 brani "Artisti
Vari" e 7 "AA.VV.").
Tra album **diversi** invece grafie diverse non sono un problema: ogni album resta intero, al massimo l'elenco Artisti
ha una voce in più. Neanche "Artisti vari" (scritto dal programma, `scan.VARIOUS_ARTISTS`) contro "Artisti Vari" (già
sull'iPhone) è un problema: l'iPhone non guarda le maiuscole e tiene la grafia che ha.
→ **REQ-2 (deciso il 27/11/2026, vedi D-1)**: dentro un album, l'artista dell'album scritto in un modo solo,
identico carattere per carattere, maiuscole comprese, anche fra le grafie di "artisti vari".

**A3. Spazi all'inizio, alla fine o doppi** in titolo, artista, album: `group_name` li unisce, nessuna regola li
segnala.
→ **REQ-3 (deciso: D-3)**: segnalarli e toglierli (correzione sicura).

### B. Controlli che mancano per un album coerente (priorità alta o media)

**B1. Spunta Compilation diversa tra i brani dello stesso album** (alta). Nessuna regola la guarda.
→ **REQ-4**.

**B2. Compilation senza "Artisti vari" come artista dell'album, o "Artisti vari" senza spunta** (alta). Oggi la spunta
si aggiunge solo dentro le correzioni R11/R13 (`_unify_changes`), mai come controllo a sé.
→ **REQ-5**.

**B3. Artista dell'album presente su alcuni brani dell'album e vuoto su altri**, in cartelle diverse (media). R11
guarda una cartella sola; R12 lo prende solo se gli artisti dei brani hanno lo stesso `artist_norm`.
→ **REQ-6**: controllo per album, non per cartella. Per i brani raggruppati nello stesso album sul PC vale D-1 (anche
quelli con l'artista dell'album vuoto lo ricevono).

**B4. Numeri di disco incoerenti** (media): album a più dischi con brani senza numero di disco; totali di tracce o di
dischi diversi tra i brani dello stesso disco o album.
→ **REQ-7**.

**B5. R11 toglie "CD 2" dal nome dell'album senza scrivere il numero del disco** (alta, è un errore). Nella stessa
situazione anche R12 scatta e il numero del disco lo scrive. Se si applica solo R11, il numero del disco si perde.
→ **REQ-8**: una sola regola per "CD n nel nome", che sposta sempre il numero nel campo.

**B6. Anno e genere diversi dentro l'album** (bassa: l'iPhone non divide l'album, ma mostra un anno a caso).
→ **REQ-9: tolto** (D-4: non influenzano nulla).

**B7. Valori segnaposto** (media): "Unknown Artist", "Artista sconosciuto", "Track 01", "Traccia 1", titolo uguale
al nome del file con "NN - ". R6 guarda solo i campi vuoti; l'AI li cita nelle istruzioni, ma è facoltativa.
→ **REQ-10**.

**B8. Copertina mancante o diversa tra i brani dell'album** (media): nessuna regola.
→ **REQ-11: tolto** (D-4).

**B9. Tag di ordinamento** (artista/album "per l'ordinamento", TSOP/TSOA, soar/soaa): **non sono un problema.** Il
programma non li legge e non arrivano all'iPhone: scrive lui l'archivio dell'app Musica e mette come ordinamento lo
stesso testo del nome (`phone_sync.py:553-563`: `sort_artist = artist`, `sort_album = album`, `sort_album_artist =
album_artist`, `sort_name = title`). Nomi puliti vogliono dire ordinamento pulito.
→ **REQ-12: tolto** (D-5).

### C. Perimetro (priorità media)

**C1. Con una selezione le regole sui nomi sono cieche.** Solo R9/R10 vedono il resto della libreria. Se controllo un
album di "Battiato" e altrove c'è "Franco Battiato", R14/R16/R12/R13 non lo trovano.
→ **REQ-13**: le regole sui nomi confrontano la selezione con tutta la libreria; i problemi restano solo quelli che
toccano la selezione.

### D. Struttura: perché continuano a uscire errori

**D1. Cinque idee di "uguale"** (sezione 4). Le regole non sono d'accordo su cosa è "lo stesso": il raggruppamento
unisce cose che R14 tratta come diverse, `same_value` cancella righe che R11/R12 propongono, e "Artisti vari" è uno
sul PC ma tre sull'iPhone.
→ **REQ-14**: una sola funzione di confronto con livelli espliciti (esatto, maiuscole, accenti, spazi,
punteggiatura, ordine delle parole). Ogni regola dice a quale livello lavora.

**D2. Le sovrapposizioni si aggiustano a valle, caso per caso**: `merge_overlapping` (R13 dentro R11, R10 dentro una
divisione, nota su R9), `drop_repeated` (AI uguale a una regola), `elsewhere` (problema che si corregge nell'altro
album), `same_value`. Ogni nuovo caso aggiunge un'eccezione.
→ **REQ-15**: regole a livelli, dove ogni livello lavora su dati che il livello prima ha già reso puliti (sezione
6), invece di regole parallele riconciliate dopo.

**D3. Tutte le correzioni partono dai tag iniziali.** Due regole sullo stesso brano e campo (R11 e R12 sull'album; R14
e R16 sull'artista; W2 e R12) producono due righe; `plan_apply` tiene l'ultima senza dirlo. Dopo una correzione le
altre sono vecchie, e il testo di R9 dice di ripetere la scansione.
→ **REQ-16**: una riga per brano e campo; se due regole vogliono valori diversi, lo si mostra come conflitto.

**D4. R14 e R16 sono lo stesso controllo** con due chiavi e due correzioni (varianti certe e dubbie).
→ **REQ-17**: un controllo solo, con un grado di certezza.

**D5. Il tipo del problema non dice la regola**: R11, R12, R13, R14, R16 sono tutti `KIND_SPLIT`; l'AI usa gli
stessi tipi. Filtri, "va bene così" e consigli devono ricostruire la regola dal `rule_id`.

**D6. Testi non allineati**: la docstring di `scan.py` cita controlli che non esistono (sola lettura, ID3 v2.4/v2.2);
la casella "Artisti scritti in modi diversi" dice "le maiuscole da sole non contano".

### E. Altri controlli che mancano

**E1. Artista del brano scritto in modi diversi dentro un album che ha l'artista dell'album** (alta). R14 e R16
guardano `display_artist`, cioè l'artista dell'album quando c'è: un brano con artista "Quen" in un album di "Queen"
non si confronta mai. Sull'iPhone l'artista del brano conta (elenco Brani, pagine artista).
→ **REQ-18**: le varianti si cercano anche sull'artista dei brani, non solo su `display_artist`.

**E2. Album diversi sul PC che l'iPhone unisce** (alta). L'iPhone non conta gli zeri davanti ai numeri ("Raccolta
01" = "Raccolta 1", `library.phone_group_key`, provato il 24/11/2026); il PC sì (`group_name`, e anche `album_norm`
tiene "01" e "1" diversi). Sul PC sono due album, sull'iPhone uno solo con la grafia arrivata prima.
→ **REQ-19**: segnalare gli album che hanno la stessa `phone_group_key` (artista dell'album e album) ma sono
diversi sul PC.

**E3. Due album veri sotto lo stesso nome** (alta). Due compilation "Greatest Hits" di "Artisti vari", o due
edizioni dello stesso album, diventano un `album_key` solo (sul PC e sull'iPhone). Il segno: lo stesso disco e numero
di traccia con titoli diversi. R8 scatta solo con lo stesso titolo; R9 non vede niente (i numeri ci sono tutti).
→ **REQ-20**: stesso disco e numero di traccia con titoli diversi nello stesso album, nello stesso formato: "due
album sotto lo stesso nome, o numeri sbagliati" (cartelle e anni diversi lo rendono più probabile).

**E4. Formati che l'iPhone non suona o di cui il programma non scrive i tag** (alta, da verificare).
- WMA, WAV, AIFF: tag in sola lettura (`tags.READ_ONLY_EXTENSIONS`); le correzioni restano in sospeso e non arrivano
  mai ai file (WAV in pratica non porta tag sull'iPhone).
- OGG, Opus, WMA: l'app Musica non li suona (da verificare); il programma non converte.

→ **REQ-21 (deciso: D-7)**: si supportano solo MP3 e FLAC (e i formati delle suonerie); gli altri file si segnalano
come "formato non supportato".

**E5. Caratteri rovinati nei tag** (alta). "Ã¨" al posto di "è", "?" o "�" al posto delle lettere accentate,
tipici dei vecchi MP3 (codifica sbagliata). Sull'iPhone diventano un artista o un album in più.
→ **REQ-22**: segnalarli e, dove la conversione latin-1/UTF-8 è certa, proporre il testo giusto.

**E6. Numeri impossibili** (media): numero di traccia più alto del totale, disco più alto del numero di dischi,
totale presente su una parte dei brani. Estende B4.
→ **REQ-23** (insieme a REQ-7).

**E7. Titoli con dentro il numero o l'artista** (media): "01 - Titolo", "Artista - Titolo". Estende B7.
→ **REQ-24** (insieme a REQ-10).

**E8. Percorsi troppo lunghi** (media). Oltre il limite di Windows il file risulta solo "illeggibile" (R5), senza
dire perché (il 23/11/2026 alcuni sono stati rinominati a mano).
→ **REQ-25**: R5 dice il motivo; i percorsi vicini al limite si segnalano prima che diventino illeggibili.

**E9. Anno non valido** (bassa): "0000", non numerico, fuori misura. Si legge già tagliato a 4 caratteri.
→ **REQ-26: tolto** (D-4: l'anno non influenza nulla).

**E10. "Va bene così" non guarda le maiuscole** (bassa, dipende dalle decisioni). La chiave dell'album è
`album_norm`/`artist_norm`: un album segnato "va bene così" nasconderebbe anche i nuovi problemi di maiuscole (D-1).
→ **REQ-27**: i problemi di grafia della D-1 non si nascondono con un "va bene così" dato prima.

**Per la fase iPhone**: sul PC lo stesso album in FLAC e MP3 va bene, ma inviarli tutti e due crea doppioni
sull'iPhone. Quale formato si manda: D-8.

## 6. Ordine dei controlli (approvato il 27/11/2026, D-6)

Livelli che lavorano uno sull'altro. Le correzioni di un livello si vedono come già fatte nei livelli dopo.

1. **File**: illeggibili con il motivo (R5, REQ-25), vecchi tag (R2, R3), formati non supportati (REQ-21, D-7).
2. **Campi del singolo brano**: vuoti (R6), segnaposto e titoli con numero o artista (REQ-10, REQ-24), spazi e
   accenti invisibilmente diversi (REQ-3, D-3), caratteri rovinati (REQ-22).
3. **Nomi canonici**: una grafia per artista in tutta la libreria, maiuscole e accenti compresi, anche per l'artista
   dei brani (REQ-1, REQ-18, R14 + R16 → REQ-17, D-2, D-3), confrontando con tutta la libreria (REQ-13).
4. **Coerenza dell'album**: nome unico e "CD n" nel numero del disco (R11 + R12 → REQ-8), artista dell'album
   identico su tutti i brani (D-1: REQ-2, REQ-6), compilation (REQ-4, REQ-5, R13), dischi e numeri (REQ-7, REQ-23),
   album che l'iPhone unirebbe (REQ-19), due album sotto lo stesso nome (REQ-20).
5. **Completezza**: R9, R10, W1.
6. **Doppioni**: R7, R8, R15.
7. **Catalogo e AI**: W2, W3, AI (per proporre, non per decidere i nomi dei livelli 3 e 4).

Sotto tutto: una sola funzione di confronto (REQ-14), una riga per brano e campo (REQ-16).

## 7. Decisioni prese (27/11/2026)

**D-1 — L'artista dell'album è identico su tutti i brani dell'album.** Se un nome è usato come artista dell'album in
un album, tutti i brani di quell'album hanno esattamente quel nome, anche quando la differenza è solo di maiuscole o
minuscole. Cambia la decisione precedente "le sole maiuscole non sono una differenza".
- **Quale grafia vince**: quella con le iniziali maiuscole ("Franco Battiato"), se esistono grafie diverse.
- **Iniziali maiuscole** vuol dire: ogni parola di almeno 4 lettere comincia con la maiuscola (le parole corte, "e",
  "le", "di", "of", "the", sono libere: "Elio e le Storie Tese" va bene) e il nome non è tutto in maiuscolo; un nome
  tutto in maiuscolo ("AC/DC") vince solo se non ce n'è un altro con le iniziali maiuscole.
- **Più grafie con le iniziali maiuscole, o nessuna**: vince la prima, nell'ordine dei brani dell'album (disco, poi
  numero di traccia).
- **Brani dell'album con l'artista dell'album vuoto**: ricevono lo stesso nome.
- **Se tutti i brani hanno lo stesso artista**, anche l'album prende quell'artista come artista dell'album (vedi
  domanda 1 della sezione 8).
- Vale anche fra le grafie di "artisti vari" dello stesso album ("AA.VV." e "Artisti Vari" → una sola).

**D-2 — Una grafia sola per ogni nome, dappertutto.** Una volta scelto "Franco Battiato" (con la regola della D-1), lo
si applica dappertutto: artista dell'album in tutti gli album, artista dei brani, e lo stesso vale per il nome
dell'album dentro l'album. Supera il limite "tra album diversi non si impone niente" della prima stesura.

**D-3 — Spazi e accenti.**
- Spazi all'inizio, alla fine o doppi: correzione proposta sempre.
- La stessa lettera accentata salvata in due modi diversi nel file (invisibile a schermo): uniformata sempre.
- Accento contro niente accento ("Pérez" / "Perez"): vince la forma con l'accento.
- Accenti diversi ("Perché" / "Perchè"): vince la prima, ma il problema dice "accenti diversi, controlla" invece di
  presentarsi come correzione sicura.

**D-4 — Anno, genere e copertina diversi nello stesso album non si controllano**: non influenzano nulla. Tolti
REQ-9, REQ-11 e, per lo stesso motivo, REQ-26 (anno non valido).

**D-5 — Tag di ordinamento: nessun controllo.** Non arrivano all'iPhone (B9).

**D-6 — L'ordine a livelli della sezione 6 è la base** per riscrivere i controlli.

**D-7 — Formati supportati: solo MP3 e FLAC, e i formati delle suonerie.** Gli altri file musicali si segnalano come
"formato non supportato" (REQ-21).

**D-8 — Album in più formati: quale si manda all'iPhone** (per la fase iPhone), in quest'ordine di preferenza:
1. MP3 a 320 kbps, se c'è;
2. FLAC;
3. gli altri MP3.

**D-10 (28/11/2026) — Le parole corte in minuscolo.** Tra grafie che differiscono solo nelle maiuscole delle parole
corte (sotto le 4 lettere, dopo la prima parola: "to", "for", "of", "di", "e", "le"…) vince quella con le parole corte
in minuscolo, anche se è meno usata: "Tears for Fears", non "Tears For Fears"; "Frankie Goes to Hollywood". Viene
prima della "più usata" della D-9 (`names._short_words_lowercase`).

**D-9 — Risposte alle domande del 27/11/2026.**
- D-1, "tutti i brani hanno lo stesso artista": vale quando l'artista dell'album è vuoto, oppure è "Artisti vari"
  ma i brani sono tutti dello stesso artista (compilation segnata per sbaglio: si toglie anche la spunta compilation).
  Un artista dell'album diverso, già scritto, non si tocca.
- D-2, tra album diversi: vince la grafia più usata (più brani; a parità, più maiuscole) tra quelle con le
  iniziali maiuscole, o tra tutte se nessuna le ha.
- Nome dell'album dentro l'album: vince la grafia più usata nell'album; a parità, la prima nell'ordine dei brani
  (rispetta i titoli italiani con la sola prima maiuscola).
- D-7: gli altri formati (OGG, Opus, WMA, WAV, AIFF) restano nella scheda PC e i Controlli li segnalano come
  "formato non supportato", spiegando cosa fare. M4A resta supportato come MP3 e FLAC.

## 8. Domande ancora aperte

1. **D-8, per album o per brano** (fase iPhone): si sceglie una copia intera dell'album (tutto MP3 320, o tutto
   FLAC), o brano per brano? Se la copia MP3 320 è incompleta e quella FLAC completa, quale vince?

## 9. Stato dell'implementazione (28/11/2026)

Fatto, solo sul PC (sull'iPhone girano le regole di prima, fino a R16, e il confronto I1-I4):

| Requisito | Dove | Regola |
|---|---|---|
| REQ-14, un modo solo di dire "uguale" | `names.py` (`fold` a livelli, `choose_spelling`); `library.group_name`, `artist_names.variant_key`, `scan._plain`, `check_flow.same_value` lo usano | — |
| REQ-15, regole a livelli | `scan.rule_steps`, `scan_rules.RuleView` | ogni passo vede le correzioni di prima |
| REQ-16, una riga per brano e campo | `check_flow.plan_apply` (vince il passo dopo; stesso passo: `conflicts`, detto nella finestra di Applica) | — |
| REQ-1, REQ-2, D-1, D-2, D-3 | `scan_rules.detect_spelling_variants`, `detect_album_name_spellings`, `detect_album_artist_spellings` | R23, R24, R25 |
| D-9 (artista unico) | `scan_rules.detect_album_artist_from_artist` | R26 |
| REQ-3, D-3 | `scan_rules.detect_spaces` | R21 |
| REQ-4, REQ-5 | `scan_rules.detect_compilation_flags` | R27 |
| REQ-6 | R25 (dentro l'album del PC) | R25 |
| REQ-7, REQ-23 | `scan_rules.detect_track_numbers` | R30 (a mano), R31 |
| REQ-8 | `scan._with_disc_numbers` (R11 sposta "CD n" nel N. disco) | R11 |
| REQ-10, REQ-24 | `scan.is_placeholder` (R6), `scan_rules.detect_title_prefixes` | R6, R20 |
| REQ-13 | regole sui nomi e sugli album con tutta la musica (`RuleView.all`); R16 con `context`; i risultati trovano anche i brani fuori dalla selezione | — |
| REQ-17 | R14 e R16 nella stessa casella, con la stessa scelta della grafia | R14, R16 |
| REQ-18 | R14 e R23 guardano artista dei brani e artista dell'album | R14, R23 |
| REQ-19 | `scan_rules.detect_phone_merges` | R28 |
| REQ-20 | `scan_rules.detect_number_clashes`: nel livello 4, prima di R9; correzione dal nome del file ("05 - …") se ogni file ha il suo numero | R29 |
| REQ-21, D-7 | `scan_rules.detect_unsupported_formats` | R18 |
| REQ-22 | `scan_rules.detect_mojibake` | R22 |
| REQ-25 | `scan_rules.detect_long_paths`; R5 non conta più i percorsi troppo lunghi | R19 |
| REQ-27 | `accepted.SPELLING_TYPES`: "tutto l'album" non nasconde R23-R25 | — |
| D5, D6 | tipi nuovi `KIND_NAMES`, `KIND_FORMAT`; docstring e testi delle caselle riscritti | — |

Tolti per decisione: REQ-9, REQ-11, REQ-26 (D-4), REQ-12 (D-5).

Aggiunto il 28/11/2026: D-10 (parole corte in minuscolo); i caratteri che cambiano evidenziati nelle colonne Ora e
Diventa; i risultati delle regole prima delle impronte dell'audio (`scan_tracks(fingerprint_fn=…)`); la finestra di
Applica dice perché il pulsante è spento e si riaccende da sola. R29 (stesso numero, titoli diversi) passa al
livello 4, nella casella "Album con pochi brani o numeri sbagliati", e propone i numeri presi dai nomi dei file; R9
conta "l'album ne ha almeno N" sui numeri diversi, non sui file (una raccolta con i numeri degli album originali
diceva "almeno 25" su 15). Un album non trovato online non è più un problema (solo nel rapporto); R13 si segnala solo
quando la raccolta divisa è probabile (nessun artista dell'album, e una cartella sola o un anno solo).

Restano:
- R15 (stesso brano, con l'impronta) e R16 girano dopo i livelli, sui tag di partenza: non vedono le correzioni dei
  livelli; R16 usa la stessa scelta della grafia, quindi non la contraddice.
- La fase iPhone: D-8 (quale formato si manda) e la domanda 1 della sezione 8.
