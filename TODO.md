# TODO

## Le proposte dubbie di "Collega al PC"

Sui dati veri restano 44 proposte non spuntate (regole senza un candidato chiaro). Controllare cosa ne dice l'AI
della scansione e se i candidati sono giusti (versioni dal vivo, remaster). In attesa: l'utente non ha ancora fatto
*Collega al PC* con la build nuova.

## Invio di M4A in Apple Lossless (ALAC) — solo se servirà

Oggi si inviano MP3, FLAC e AAC. ALAC vuole il suo formato di inserimento (rustunes `protocol/alac.rs`: tra
l'altro `gapless_heuristic_info`, `analysis_inhibit_flags`). Per ora non serve: i 20 M4A della musica dell'utente
sono tutti AAC.

## L'app Musica che non si aggiorna da sola — da provare sul telefono

Dopo ogni scrittura il programma ora manda all'iPhone l'avviso di fine sincronizzazione di iTunes
(`com.apple.itunes-mobdev.syncDidFinish`, notification proxy; `iphone.post_sync_finished`). Da provare con l'app
Musica aperta su un brano PROVA: se si aggiorna da sola, togliere dal messaggio finale l'invito a chiuderla e
riaprirla; se no, provare anche `syncWillStart` all'inizio della sessione.

## Interfaccia anche in inglese

Un'opzione in *Impostazioni* per la lingua dell'interfaccia: italiano (oggi l'unica) o inglese. Tutti i testi
dell'interfaccia e i messaggi oggi sono scritti in italiano dentro il codice: vanno raccolti in un catalogo (le
traduzioni di Qt, `tr()`/`.ts`, o un dizionario del programma), con la traduzione italiana di Qt già caricata
(`theme.install_italian`) scelta in base alla lingua. Nuova impostazione: va nella sezione "Quale valore vince" del
README. Da decidere: se anche README, rapporti della scansione e prompt per l'AI cambiano lingua.
