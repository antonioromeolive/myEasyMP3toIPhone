# TODO

## Varianti dei nomi degli artisti (dopo il passo 5)

"Battiato", "Franco Battiato", "Battiato Franco", "F. Battiato", accenti, errori di battitura, duetti. Decisioni già
prese: livelli regole certe → AI con il contesto (album, anni, titoli; gruppi per cognome) → MusicBrainz (alias)
facoltativo; **vince la forma più usata**; **duetti: artista e artista album = artista principale, ospiti nel titolo**
"Titolo (feat. Ospite)" (l'app Musica non gestisce artisti multipli); album intero in coppia: principale = primo
nome. Risultato come problemi della scansione con la correzione, poi *Rimpiazza* per l'iPhone. Attenzione ai nomi veri
con iniziali ("B.B. King"). Numeri misurati: 2.696 nomi, 4 per ordine delle parole, 56 "solo cognome", 33 quasi
uguali, 47 con iniziali, 656 duetti.

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
