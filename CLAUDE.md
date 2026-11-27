# myEasyMP3toIPhone

Programma per Windows (PySide6) per la musica: tag, album completi (MusicBrainz), scansione dei problemi con l'AI,
trasferimento da e verso l'iPhone (pymobiledevice3). Il pacchetto Python è `myeasymp3toiphone`; il programma e la build si
chiamano `myEasyMP3toIPhone`. Interfaccia, messaggi e documentazione sono in italiano.

Build, cartella dati, profili AI e chiavi seguono lo stesso meccanismo di `c:\Github\myCalibreTools` e la sua
specifica `config and build specs.md` (parti 1, 2 e 3: qui il file delle variabili c'è).

Test: `.venv\Scripts\python -m pytest` dalla cartella del repository. I test non toccano mai la cartella dati vera
(`tests/conftest.py`: cartella temporanea, credential store finto in memoria, niente rete verso Ollama) e non fanno mai
una build vera. Nomi e valori inventati.

## I file sul PC cambiano solo con l'approvazione dell'utente

Il programma non sposta e non cancella mai i file delle cartelle aperte (compresa la Libreria). Le modifiche dei tag
vanno in `overlay.TagOverlay` (cartella dati) e si applicano solo alle copie: invio all'iPhone
(`iphone.UploadItem.prepare`), esportazione e importazione (`copy_organized(prepare=…)`), con
`tags.prepare_copy` / `write_tags(..., new_copy=True)`. `tags.protect_folder` blocca le scritture dentro le cartelle
aperte: non aggirarlo.

Le eccezioni passano tutte da `gui/pc_write.py`: **Usa i tag da iPhone a PC** (scheda iPhone), **Applica le correzioni
scelte** dei Controlli (casella *Sul PC: scrivi nei file*, per i brani collegati e per quelli solo sul PC) e *Correggi
tag* di Dettagli della verifica online (scelta *Anche nei file del PC…*) scrivono i tag nei file originali con
`tags.write_tags_approved`, solo dopo `PcWriteDialog`, che elenca ogni file e ogni campo che cambia (ora → diventa) e
dice che non si può annullare. Ogni nuova scrittura nei file del PC deve passare da una finestra così: chiara e
approvata, mai automatica.

Le correzioni dei Controlli vanno dalla parte dove c'è il brano (`check_flow.plan_apply`): un brano collegato (registro)
sul PC e sull'iPhone (*Usa i tag da PC a iPhone*, in attesa), uno solo sul PC solo sul PC, uno solo sull'iPhone solo
sull'iPhone (*Cambia i tag*, in attesa; solo `pending.EDIT_FIELDS`, solo brani messi da un computer).

Le suonerie hanno la loro cartella (`settings.ringtone_folder`, esclusa dalla scheda PC): **Crea una suoneria** vi
scrive solo file nuovi (ffmpeg `-n`, `ringtones.unique_target`) e il brano di partenza non cambia; **Rinomina** e
**Sposta nel cestino** (scheda Suonerie) valgono solo per i `.m4r` di quella cartella (`ringtones.in_folder`), dopo
una conferma. ffmpeg non si distribuisce: lo installa l'utente.

PC e iPhone non si allineano da soli: cancellare o cambiare sull'iPhone non cambia il PC, cambiare sul PC non cambia
l'iPhone (niente domande a finestra "aggiorna anche l'altra parte"). La differenza si vede (⟳, nome del file in giallo)
e il brano resta associato; si allinea solo con un'azione esplicita: Usa i tag da PC a iPhone / da iPhone a PC,
Ricopia, oppure le caselle **Anche sull'iPhone** (editor dei tag della scheda PC: va in attesa) e **Anche sul PC**
(Cambia i tag della scheda iPhone: solo modifiche in sospeso nell'overlay, mai i file). Le caselle sono spente di
serie e quella dell'editor si rispegne dopo ogni salvataggio. L'importazione dall'iPhone crea solo file nuovi
(`overwrite=False`).

## Tutto ciò che scrive sull'iPhone va in attesa

Copia, Ricopia, Usa i tag da PC a iPhone, Cambia i tag, Elimina (e le spunte della colonna iPhone) mettono una voce in
`pending.Pending` (per file del PC o per brano dell'iPhone) e partono solo con **Applica**, che mostra
`apply_dialog.ApplyDialog` (ogni azione si toglie con la ✕). Una nuova azione verso l'iPhone segue la stessa strada:
mai una scrittura sull'iPhone direttamente da un menu. Così anche le suonerie: *Invia come suoneria* ed *Elimina
dall'iPhone* della scheda Suonerie sono voci `RING_SEND` / `RING_DELETE` della stessa coda, e partono con Applica
(`phone_ringtones.apply_ringtones`: una sessione che chiede solo la classe Ringtone, mai Media). Restano immediati, con la loro conferma: Copia da iPhone a PC,
Usa i tag da iPhone a PC, le associazioni (solo il registro), Playlist per artista (anteprima e prova). I nomi delle
azioni dicono il verso a parole ("da PC a iPhone", "da iPhone a PC").

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
