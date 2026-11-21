# myEasyMP3toIPhone

Programma per Windows (PySide6) per la musica: tag, album completi (MusicBrainz), scansione dei problemi con l'AI,
trasferimento da e verso l'iPhone (pymobiledevice3). Il pacchetto Python è `myeasymp3toiphone`; il programma e la build si
chiamano `myEasyMP3toIPhone`. Interfaccia, messaggi e documentazione sono in italiano.

Build, cartella dati, profili AI e chiavi seguono lo stesso meccanismo di `c:\Github\myCalibreTools` e la sua
specifica `config and build specs.md` (parti 1, 2 e 3: qui il file delle variabili c'è).

Test: `.venv\Scripts\python -m pytest` dalla cartella del repository. I test non toccano mai la cartella dati vera
(`tests/conftest.py`: cartella temporanea, credential store finto in memoria, niente rete verso Ollama) e non fanno mai
una build vera. Nomi e valori inventati.

## I file sul PC sono in sola lettura

Il programma non modifica, sposta o cancella mai i file delle cartelle aperte (compresa la Libreria). Le modifiche dei
tag vanno in `overlay.TagOverlay` (cartella dati) e si applicano solo alle copie: invio all'iPhone
(`iphone.UploadItem.prepare`), esportazione e importazione (`copy_organized(prepare=…)`), con
`tags.prepare_copy` / `write_tags(..., new_copy=True)`. `tags.protect_folder` blocca le scritture dentro le cartelle
aperte: non aggirarlo. Le operazioni sull'iPhone non toccano mai i file del PC (l'importazione dall'iPhone crea solo
file nuovi, `overwrite=False`).

## Regole per ogni commit

- **Una nuova impostazione, opzione della console o variabile d'ambiente, o un ordine di precedenza cambiato,
  aggiorna la sezione "Quale valore vince" del `README.md` nello stesso commit.** Leggi il codice invece di indovinare.
- **Una nuova variabile d'ambiente va in `environment.VARIABLES` e, vuota e commentata, in
  `myeasymp3toiphone/myEasyMP3toIPhone.TEMPLATE.env`.** Un test confronta l'elenco con il codice e con il modello.
- **I nomi delle variabili AI sono quelli di myCalibreTools** (`OLLAMA_API_BASE`, `OLLAMA_API_KEY`,
  `OLLAMA_FALLBACK_API_BASE`, `AZURE_FOUNDRY_EP`, `AZURE_FOUNDRY_KEY`; per OpenAI e Anthropic i nomi standard):
  `config.PROFILE_VARIABLES` li usa come predefiniti dei profili nuovi. Non inventarne di diversi.
- **Alza `DATA_FORMAT` in `myeasymp3toiphone/home_backup.py` a mano in ogni commit che cambia il formato di un file della
  cartella dati in modo che una versione precedente non lo sappia più leggere.** Nessun test se ne accorge.
- Una migrazione della cartella dati va in `startup.prepare`, dopo `backup_if_needed`, mai prima.
- Il file delle variabili si legge in `startup.prepare` prima di qualsiasi cosa legga una variabile (un test controlla
  l'ordine), da una funzione di avvio, mai all'import.

## Segreti

- Ogni campo che contiene una chiave o un indirizzo accetta `$NOME`, e si salva solo il nome. Scritto in chiaro, il
  valore va nel credential store (keyring, servizio `myEasyMP3toIPhone`), mai in un file di impostazioni. Gli indirizzi
  pubblici (`config.PUBLIC_SERVERS`) restano nel file.
- Una chiave non si mostra mai: mascherata nel campo; `--env` dice solo `impostata (file)`, `impostata (sistema)` o
  `N/A`; *Informazioni* mostra i valori ma mai una chiave o una password, e dice dove è salvata ogni chiave.
- Gli avvisi del file delle variabili nominano righe o variabili, mai quello che c'è dopo l'`=`.
- Non scrivere mai cartelle o valori veri del proprietario in un file tracciato.
- `config.KEYRING_SERVICE` ("myEasyMP3toIPhone") è il nome sotto cui sono salvate le chiavi: cambiarlo le fa perdere.

## Stile

Programmazione strutturata: un solo `return` alla fine di ogni funzione (`result = …` / `return result`), niente
`break`/`continue`, cicli espliciti per la logica non banale. Sollevare un'eccezione per un errore è ammesso.

## `vscode_deploy.py`

Condiviso tra progetti, solo libreria standard, indipendente da questo pacchetto: copiato tale e quale da
myCalibreTools. Non modificarlo qui.
