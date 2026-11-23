# TODO

## Le proposte dubbie di "Associa sorgenti"

Sui dati veri restano 44 proposte non spuntate (regole senza un candidato chiaro). Controllare cosa ne dice l'AI
della scansione e se i candidati sono giusti (versioni dal vivo, remaster). In attesa: l'utente non ha ancora fatto
*Associa sorgenti* con la build nuova.

## Invio di M4A in Apple Lossless (ALAC) — solo se servirà

Oggi si inviano MP3, FLAC e AAC. ALAC vuole il suo formato di inserimento (rustunes `protocol/alac.rs`: tra
l'altro `gapless_heuristic_info`, `analysis_inhibit_flags`). Per ora non serve: i 20 M4A della musica dell'utente
sono tutti AAC.

## Da provare con l'iPhone attaccato (solo brani PROVA, poi tolti)

Fatto e provato senza telefono (test e finestre di prova); da confermare sul telefono vero:
- **Compilation in Cambia tag**: `update_track` con `is_compilation` (rustunes lo accetta ma non l'ha verificato):
  il brano cambia spunta? L'album nell'app Musica si raccoglie? Se no, la finestra lo spiega già (Rimpiazza).
- **Brani fantasma**: la lettura delle cartelle F00… (`iphone._music_files`) e il brano `F05/W0084007.mp3` segnato
  *senza file* (lo elimina l'utente).
- **Applica** (passo 5): invio, eliminazione e aggiornamento in una volta, poi le spunte in attesa che spariscono.
- **Modifica dei tag dal PC** su un brano collegato: Cambia tag per titolo e album, Rimpiazza per l'artista, il
  promemoria delle playlist.
- **Playlist per artista** (`insert_playlist`, `delete_playlist`: rustunes li ha provati su un telefono, ma solo
  con playlist di 1-42 brani): prima **Prova** ("♪ PROVA", una playlist vera di decine o centinaia di brani, in
  ordine?), poi il piano completo. Controllare che le playlist di CopyTrans abbiano un `sync_id` (se risultano tutte
  "fatte sull'iPhone", il computer non le può cancellare) e il messaggio finale se Sincronizza libreria è attiva.
- **Album e artisti che l'iPhone tiene con il nome vecchio**: dopo *Rimpiazza* i brani nuovi finiscono nell'album
  che c'era ("Raccolta 1" invece di "Raccolta 01", "Artisti Vari" invece di "AA.VV.", e anche un album con un altro
  artista dell'album). Ipotesi: l'iPhone attacca il brano al gruppo con il nome "uguale" che c'è già, e Rimpiazza
  toglie il vecchio solo dopo. Prova con un album PROVA: togliere prima tutti i brani dell'album e poi inviarli; se
  l'album prende il nome nuovo, offrirlo come *Rimpiazza l'album intero* per le differenze vere (artista dell'album).
- **App Musica che non si aggiorna da sola**: dopo ogni scrittura il programma manda l'avviso di fine
  sincronizzazione di iTunes (`com.apple.itunes-mobdev.syncDidFinish`, `iphone.post_sync_finished`). Con l'app
  Musica aperta: se si aggiorna da sola, togliere dal messaggio finale l'invito a chiuderla e riaprirla; se no,
  provare anche `syncWillStart` all'inizio della sessione.

## Da provare con l'AI locale (Ollama acceso)

- *Controlla la musica* → **Brani duplicati**: le 368 coppie dubbie (versioni live, remix…) sulla collezione vera;
  controllare qualche risposta.
- **Artisti scritti in modi diversi**: i 22 gruppi dubbi, con e senza MusicBrainz.
- In inglese, i motivi dell'AI devono arrivare in inglese.

## Da provare sui dati veri (le novità del 22/11/2026)

Fatto e provato con i test (risposte finte, nessuna rete tranne una prova di Deezer e Apple Music); da guardare sulla
musica vera:
- **Tutti i tipi di tag** (ID3v2 → APEv2 → ID3v1, WMA/WAV/AIFF in sola lettura): l'MP3 d'esempio che nella scheda
  PC era senza tag è stato cancellato. Trovarne un altro che TagScanner legge e il programma no, e vedere cosa dice
  *Tag letti da* nell'editor. Alla prima apertura gli MP3 della cache con un campo vuoto si rileggono.
- **Associa sorgenti** con il nome della cartella: quanti brani trova senza impronta sulla Libreria vera, e se i
  *molto probabile* sono giusti. Provare anche *Tutta la Libreria* e i brani selezionati che hanno già una sorgente.
- **Sul PC** nella scheda iPhone: ✔/⟳ per le sorgenti fuori dalla cartella aperta (quanto ci mette con migliaia di
  brani su un disco esterno), ≈ e il filtro *Da rivedere*, ✖, *Associa le probabili*.
- **Sorgenti proposte in rosso** (album intero in una cartella): quante ne trova sulla Libreria vera, se sono giuste,
  *Associa questa sorgente*. **Allinea i tag** nei due versi, con l'iPhone attaccato (solo brani PROVA).
- **Verifica album online**: Deezer e Apple Music sulla Libreria vera (album italiani: il negozio Apple è quello di
  Windows), l'ordine dei servizi, *Ferma*, la finestra dei risultati non modale. Discogs con `DISCOGS_TOKEN`
  impostata. L'AI per le edizioni dubbie con Ollama acceso.
