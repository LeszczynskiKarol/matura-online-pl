# Audio STT pipeline — angielski matura

Cel: pociąć **jeden** MP3 per arkusz (CKE publikuje 1 plik z 3 zadaniami) na
**3 osobne** pliki per zadanie, autodetekcją granic.

## Workflow

```bash
# 1. Transkrypcja (faster-whisper, CPU, model small, język pl)
#    Lektor mówi "Zadanie pierwsze/drugie/trzecie" — to nasze markery.
python transcribe.py                  # wszystkie 6 plików
python transcribe.py 2025-maj-pp      # tylko jeden klucz

# 2. Ekstrakcja granic z transkrypcji (regex)
python extract-boundaries.py          # produkuje boundaries.json

# 3. Cięcie ffmpeg + upload S3 + CF invalidation
python cut-and-upload.py --dry        # dry-run, pokazuje granice
python cut-and-upload.py              # właściwy cut + upload
python cut-and-upload.py --key 2025-maj-pp  # pojedynczy arkusz

# 4. Update meta plików zadań (audioUrl per zadanie)
python update-meta.py
```

## Pliki

- `transcribe.py` — uruchamia faster-whisper na 6 MP3 z `D:\matury-online.pl\arkusze\jezyk-angielski\YYYY\`
- `extract-boundaries.py` — parsuje transkrypcję, znajduje pierwsze "Zadanie pierwsze/drugie/trzecie", zapisuje `boundaries.json`
- `cut-and-upload.py` — ffmpeg libmp3lame 128k cut, upload S3 z immutable cache, CF invalidate
- `update-meta.py` — wstawia `audioUrl: ...` do frontmatter 18 plików zadań

## Gdzie idą pliki

- Local cut: `D:\matura-online.pl\public\audio\jezyk-angielski\<key>-<nr>.mp3`
- S3: `s3://www.matura-online.pl/audio/jezyk-angielski/<key>-<nr>.mp3`
- CDN: `https://www.matura-online.pl/audio/jezyk-angielski/<key>-<nr>.mp3`

`public/audio/` jest w .gitignore (binarki). `deploy.sh` ma `--exclude "audio/*"` żeby nie czyściło ich przy syncu.

## Manualna korekta

Jeśli boundaries.json ma błędną wartość (whisper nie złapał frazy), edytuj `boundaries.json` ręcznie i odpal `cut-and-upload.py --key <key>` na nowo dla danego arkusza.
