"""
Z transkrypcji JSON + ffmpeg silencedetect wyznacza granice z1/z2/z3
dla kazdego z 6 arkuszy.

Algorytm:
  1. Whisper transkrypcja -> regex "zadanie pierwsze/drugie/trzecie" lub
     "zadanie 1/2/3".
  2. Silencedetect ffmpeg (noise=-35dB, d=25s) -> lista pauz >=25s.
  3. Brakujace markery uzupelnia silencedetectem:
     - Jesli z1 nieznane: z1 = pierwsza pauza_start - 5  (przed nia pada "Zadanie pierwsze")
     - Jesli z2 nieznane: srodkowa pauza miedzy z1 i z3 - 5
     - Jesli z3 nieznane: zazwyczaj whisper lapie, fallback: pauza_start - 5
       w drugiej polowie audio

Wynik: boundaries.json z mapowaniem:
  { "2025-maj-pp": { "z1": 34, "z2": 853, "z3": 1140, "duration": 1487 } }
"""
import json
import re
import subprocess
import sys
from pathlib import Path

TRANS_DIR = Path(__file__).parent / "transcripts"
OUT = Path(__file__).parent / "boundaries.json"
SOURCE_DIR = Path(r"D:\matury-online.pl\arkusze\jezyk-angielski")

SOURCE_MAP = {
    "2023-maj-pp": SOURCE_DIR / "2023" / "matura_2023_angielski_podstawowy_nagrania_mp3.mp3",
    "2023-maj-pr": SOURCE_DIR / "2023" / "matura_2023_angielski_rozszerzony_nagrania_mp3.mp3",
    "2024-maj-pp": SOURCE_DIR / "2024" / "matura_2024_podstawowy_angielski_nagrania_mp3.mp3",
    "2024-maj-pr": SOURCE_DIR / "2024" / "matura_2024_rozszerzony_angielski_nagrania_mp3.mp3",
    "2025-maj-pp": SOURCE_DIR / "2025" / "matura_2025_podstawowy_angielski_nagrania_mp3.mp3",
    "2025-maj-pr": SOURCE_DIR / "2025" / "matura_2025_rozszerzony_angielski_nagrania_mp3.mp3",
}

ORDINAL = {
    "z1": [r"\bzadanie\s+pierwsze\b", r"\bzadanie\s+1\b"],
    "z2": [r"\bzadanie\s+drugie\b", r"\bzadanie\s+2\b"],
    "z3": [r"\bzadanie\s+trzecie\b", r"\bzadanie\s+3\b"],
}

def find_marker_in_transcript(transcript, patterns):
    flat_words = []
    for seg in transcript["segments"]:
        for w in seg["words"]:
            flat_words.append(w)
    text = ""
    word_positions = []
    for w in flat_words:
        if text and not text.endswith(" "):
            text += " "
        start = len(text)
        text += w["word"].strip()
        word_positions.append((start, len(text), w))
    text_lower = text.lower()
    earliest = None
    for pat in patterns:
        m = re.search(pat, text_lower)
        if m:
            char_pos = m.start()
            for (cs, ce, w) in word_positions:
                if cs <= char_pos < ce:
                    if earliest is None or w["start"] < earliest:
                        earliest = w["start"]
                    break
    return earliest

def silencedetect(mp3_path, threshold_db=-35, min_dur=25):
    """Lista (start, end) pauz >= min_dur sekund."""
    cmd = [
        "ffmpeg", "-hide_banner",
        "-i", str(mp3_path),
        "-af", f"silencedetect=noise={threshold_db}dB:d={min_dur}",
        "-f", "null", "-",
    ]
    out = subprocess.run(cmd, capture_output=True, text=True).stderr
    pauses = []
    start = None
    for line in out.splitlines():
        m = re.search(r"silence_start: ([\d.]+)", line)
        if m:
            start = float(m.group(1))
            continue
        m = re.search(r"silence_end: ([\d.]+) \| silence_duration: ([\d.]+)", line)
        if m and start is not None:
            end = float(m.group(1))
            pauses.append((start, end))
            start = None
    return pauses

def get_duration(mp3_path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp3_path)]
    return float(subprocess.run(cmd, capture_output=True, text=True).stdout.strip())

def resolve_boundaries(key):
    trans_file = TRANS_DIR / f"{key}.json"
    if not trans_file.exists():
        print(f"  [WARN] {key}: brak transkrypcji, fallback tylko silencedetect")
        transcript = None
    else:
        with open(trans_file, encoding="utf-8") as f:
            transcript = json.load(f)

    src = SOURCE_MAP[key]
    pauses = silencedetect(src)
    duration = transcript["duration"] if transcript else get_duration(src)
    print(f"  {key}: {len(pauses)} pauz >=25s, duration={duration:.0f}s")
    for p_start, p_end in pauses:
        print(f"    pauza: {p_start:.0f}-{p_end:.0f} (dur {p_end-p_start:.0f}s)")

    # Whisper-detected markers
    z1 = z2 = z3 = None
    if transcript:
        z1 = find_marker_in_transcript(transcript, ORDINAL["z1"])
        z2 = find_marker_in_transcript(transcript, ORDINAL["z2"])
        z3 = find_marker_in_transcript(transcript, ORDINAL["z3"])
        print(f"    whisper: z1={z1} z2={z2} z3={z3}")

    # Fallbacks ze silencedetect
    if z1 is None and pauses:
        z1 = max(0, pauses[0][0] - 5)
        print(f"    fallback z1={z1:.0f} (z pauzy[0])")
    if z3 is None and pauses:
        # Ostatnia pauza w drugiej polowie audio (przed nia pewnie "Zadanie trzecie")
        candidates = [p for p in pauses if p[0] > duration * 0.55]
        if candidates:
            z3 = max(0, candidates[0][0] - 5)
            print(f"    fallback z3={z3:.0f}")
    if z2 is None and z1 is not None and z3 is not None and pauses:
        # Pauza miedzy z1+50s a z3-50s; po pauzie pada "Zadanie drugie"
        mid_pauses = [p for p in pauses if z1 + 50 < p[0] < z3 - 50]
        if mid_pauses:
            # Wez ostatnia (najblizsza z3) - typowo pauza tuz przed "Zadanie drugie"
            p = mid_pauses[0]
            z2 = p[1]  # koniec pauzy = start "Zadanie drugie"
            print(f"    fallback z2={z2:.0f} (z pauzy {p[0]:.0f}-{p[1]:.0f})")

    if all(x is not None for x in (z1, z2, z3)):
        return {"z1": round(z1, 1), "z2": round(z2, 1), "z3": round(z3, 1), "duration": round(duration, 1)}
    return None

def main(only=None):
    out = {}
    if OUT.exists():
        with open(OUT, encoding="utf-8") as f:
            out = json.load(f)

    for key in SOURCE_MAP:
        if only and key != only:
            continue
        print(f"\n>>> {key}")
        result = resolve_boundaries(key)
        if result:
            out[key] = result
            print(f"  OK z1={result['z1']} z2={result['z2']} z3={result['z3']}")
        else:
            print(f"  FAIL: niekompletne markery, sprawdz ręcznie")

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nZapisano: {OUT}")

if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else None
    main(only)
