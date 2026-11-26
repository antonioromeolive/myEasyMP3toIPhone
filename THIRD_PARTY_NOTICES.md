# Codice e dati di terzi

## rustunes

La scrittura nella musica dell'app Musica dell'iPhone (`myeasymp3toiphone/phone_sync.py`, `phone_actions.py`) segue
la ricostruzione del protocollo AirTrafficControl di **rustunes** (<https://github.com/fbiba/rustunes>): la richiesta
Grappa fissa da 84 byte, le costanti e il calcolo della firma `.cig`, la sequenza dei messaggi, le operazioni
`insert_track`, `update_track` e `delete_track` e le regole su album, artisti e copertine. I vettori di prova
`tests/fixtures/grappa-fixed-vectors.plist` vengono da rustunes così come sono.

```text
MIT License

Copyright (c) 2026 Feim Biba

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## go-tunes

Le suonerie verso l'iPhone (`myeasymp3toiphone/phone_sync.py`, sezione delle suonerie, e `phone_ringtones.py`)
seguono la forma delle sessioni della classe Ringtone di **go-tunes** (<https://github.com/yinyajiang/go-tunes>): la
cartella `iTunes_Control/Ringtones/Sync`, le operazioni `insert_track` (con `is_ringtone` e `ringtone_info.guid`) e
`delete_track` (con `path` e `device_path`), il catalogo `Ringtones.plist` dell'host e quello delle suonerie fatte
sull'iPhone in `/Purchases`. Nessun codice copiato: solo il formato, riscritto in Python.

```text
MIT License

Copyright (c) 2026 yajiang

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
