"""
Transkrybuj 6 plikow MP3 (matura angielski 2023-2025 PP+PR)
faster-whisper, model small, word timestamps, jezyk pl.

Lektor CKE zapowiada "Zadanie pierwsze/drugie/trzecie" przed kazdym
zadaniem - regex znajdzie granice po transkrypcji.

Wynik: ./transcripts/<basename>.json z segmentami + word timestamps.
"""
import io
import json
import sys
from pathlib import Path
from faster_whisper import WhisperModel

# Force UTF-8 stdout (whisper czesto produkuje chinskie halucynacje, CP1250 wyjebie)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SOURCE_DIR = Path(r"D:\matury-online.pl\arkusze\jezyk-angielski")
OUT_DIR = Path(__file__).parent / "transcripts"
OUT_DIR.mkdir(exist_ok=True)

FILES = [
    ("2023-maj-pp", SOURCE_DIR / "2023" / "matura_2023_angielski_podstawowy_nagrania_mp3.mp3"),
    ("2023-maj-pr", SOURCE_DIR / "2023" / "matura_2023_angielski_rozszerzony_nagrania_mp3.mp3"),
    ("2024-maj-pp", SOURCE_DIR / "2024" / "matura_2024_podstawowy_angielski_nagrania_mp3.mp3"),
    ("2024-maj-pr", SOURCE_DIR / "2024" / "matura_2024_rozszerzony_angielski_nagrania_mp3.mp3"),
    ("2025-maj-pp", SOURCE_DIR / "2025" / "matura_2025_podstawowy_angielski_nagrania_mp3.mp3"),
    ("2025-maj-pr", SOURCE_DIR / "2025" / "matura_2025_rozszerzony_angielski_nagrania_mp3.mp3"),
    ("2026-maj-pp", SOURCE_DIR / "2026" / "matura_2026_angielski_podstawowy_nagrania_mp3.mp3"),
    ("2026-maj-pr", SOURCE_DIR / "2026" / "matura_2026_angielski_rozszerzony_nagrania_mp3.mp3"),
]

# Polskie "zadanie pierwsze" wymaga modelu ktory rozumie kontekst.
# small = ~244M, dobry kompromis na CPU. medium = ~769M, lepszy ale 3x wolniej.
MODEL_NAME = "small"

def main(only=None, model_name=None):
    name = model_name or MODEL_NAME
    print(f"Ladowanie modelu {name}...", flush=True)
    model = WhisperModel(name, device="cpu", compute_type="int8")
    print("Model gotowy.", flush=True)

    for key, path in FILES:
        if only and key != only:
            continue
        if not path.exists():
            print(f"  [SKIP] {key}: nie ma pliku {path}", flush=True)
            continue
        out_file = OUT_DIR / f"{key}.json"
        if out_file.exists():
            print(f"  [SKIP] {key}: juz transkrybowane ({out_file})", flush=True)
            continue
        print(f"\n>>> {key}: {path.name}", flush=True)
        segments_iter, info = model.transcribe(
            str(path),
            language="pl",
            word_timestamps=True,
            vad_filter=True,
            beam_size=5,
        )
        segments = []
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
            # Live preview - pokaz co transkrybuje
            print(f"  [{seg.start:7.2f}-{seg.end:7.2f}] {seg.text.strip()[:100]}", flush=True)
        out = {
            "key": key,
            "source": str(path),
            "duration": info.duration,
            "language": info.language,
            "segments": segments,
        }
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"  Zapisano: {out_file}", flush=True)

if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else None
    model_name = sys.argv[2] if len(sys.argv) > 2 else None
    main(only, model_name)
