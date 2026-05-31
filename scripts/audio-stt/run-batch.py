"""Batch transkrypcji 5 pozostalych plikow z modelem base (juz zalado-
wany raz, leci sekwencyjnie). 2025-maj-pp jest pominiety (ma juz JSON)."""
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from transcribe import FILES, OUT_DIR
import json
from faster_whisper import WhisperModel

MODEL_NAME = "base"

print(f"Ladowanie modelu {MODEL_NAME}...", flush=True)
model = WhisperModel(MODEL_NAME, device="cpu", compute_type="int8")
print("Model gotowy.\n", flush=True)

for key, path in FILES:
    if not path.exists():
        print(f"[SKIP] {key}: brak pliku")
        continue
    out_file = OUT_DIR / f"{key}.json"
    if out_file.exists():
        print(f"[SKIP] {key}: juz transkrybowane")
        continue
    print(f">>> {key}: {path.name}", flush=True)
    segments_iter, info = model.transcribe(
        str(path),
        language="pl",
        word_timestamps=True,
        vad_filter=True,
        beam_size=5,
    )
    segments = []
    n_zadanie = 0
    for seg in segments_iter:
        words = [
            {"start": w.start, "end": w.end, "word": w.word}
            for w in (seg.words or [])
        ]
        segments.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text,
            "words": words,
        })
        # tylko kluczowe linie - "zadanie" lub co 60s
        txt = seg.text.strip().lower()
        if "zadanie" in txt:
            n_zadanie += 1
            print(f"  [{seg.start:7.2f}] {seg.text.strip()[:80]}", flush=True)
    out = {
        "key": key,
        "source": str(path),
        "duration": info.duration,
        "language": info.language,
        "segments": segments,
    }
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"  Zapisano {out_file.name} ({n_zadanie} markerow 'zadanie')\n", flush=True)

print("Batch zakonczony.")
