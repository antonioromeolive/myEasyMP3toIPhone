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
- **App Musica che non si aggiorna da sola**: dopo ogni scrittura il programma manda l'avviso di fine
  sincronizzazione di iTunes (`com.apple.itunes-mobdev.syncDidFinish`, `iphone.post_sync_finished`). Con l'app
  Musica aperta: se si aggiorna da sola, togliere dal messaggio finale l'invito a chiuderla e riaprirla; se no,
  provare anche `syncWillStart` all'inizio della sessione.

## Da provare con l'AI locale (Ollama acceso)

- *Controlla la musica* → **Brani duplicati**: le 368 coppie dubbie (versioni live, remix…) sulla collezione vera;
  controllare qualche risposta.
- **Artisti scritti in modi diversi**: i 22 gruppi dubbi, con e senza MusicBrainz.
- In inglese, i motivi dell'AI devono arrivare in inglese.
