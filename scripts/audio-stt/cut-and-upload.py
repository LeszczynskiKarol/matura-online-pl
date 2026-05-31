"""
Na podstawie boundaries.json:
  - ffmpeg cut na 3 pliki per arkusz (z1, z2, z3), libmp3lame 128k
  - aws s3 cp + cache-control immutable
  - cloudfront invalidate

Usage: python cut-and-upload.py [--dry] [--key 2025-maj-pp]
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
BOUNDARIES = ROOT / "boundaries.json"
SOURCE_DIR = Path(r"D:\matury-online.pl\arkusze\jezyk-angielski")
OUT_DIR = Path(r"D:\matura-online.pl\public\audio\jezyk-angielski")

S3_BUCKET = "www.matura-online.pl"
S3_PREFIX = "audio/jezyk-angielski"
CF_DIST = "EWPUJ4X7VMGIQ"

FILE_MAP = {
    "2023-maj-pp": SOURCE_DIR / "2023" / "matura_2023_angielski_podstawowy_nagrania_mp3.mp3",
    "2023-maj-pr": SOURCE_DIR / "2023" / "matura_2023_angielski_rozszerzony_nagrania_mp3.mp3",
    "2024-maj-pp": SOURCE_DIR / "2024" / "matura_2024_podstawowy_angielski_nagrania_mp3.mp3",
    "2024-maj-pr": SOURCE_DIR / "2024" / "matura_2024_rozszerzony_angielski_nagrania_mp3.mp3",
    "2025-maj-pp": SOURCE_DIR / "2025" / "matura_2025_podstawowy_angielski_nagrania_mp3.mp3",
    "2025-maj-pr": SOURCE_DIR / "2025" / "matura_2025_rozszerzony_angielski_nagrania_mp3.mp3",
}

def run(cmd, **kw):
    print(f"  $ {' '.join(str(c) for c in cmd)}", flush=True)
    subprocess.run(cmd, check=True, **kw)

def main():
    dry = "--dry" in sys.argv
    only = None
    if "--key" in sys.argv:
        only = sys.argv[sys.argv.index("--key") + 1]

    with open(BOUNDARIES, encoding="utf-8") as f:
        bnd = json.load(f)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cf_paths = []

    for key, source in FILE_MAP.items():
        if only and key != only:
            continue
        if key not in bnd:
            print(f"[SKIP] {key}: brak w boundaries.json")
            continue
        b = bnd[key]
        if not all(b.get(k) is not None for k in ("z1", "z2", "z3")):
            print(f"[SKIP] {key}: niekompletne granice {b}")
            continue
        # Granice: z1 -> z2 -> z3 -> koniec
        # Marginesy: -1s przed nastepnym zadaniem (bezpiecznik na zapowiedz lektora)
        BUFFER = 1.0
        cuts = [
            (1, b["z1"], b["z2"] - BUFFER),
            (2, b["z2"], b["z3"] - BUFFER),
            (3, b["z3"], b["duration"]),
        ]
        for nr, start, end in cuts:
            out_file = OUT_DIR / f"{key}-{nr}.mp3"
            print(f"\n>>> {key}-{nr}: {start:.2f}s -> {end:.2f}s ({end-start:.1f}s)")
            if dry:
                continue
            run([
                "ffmpeg", "-y",
                "-i", str(source),
                "-ss", str(start),
                "-to", str(end),
                "-c:a", "libmp3lame",
                "-b:a", "128k",
                str(out_file),
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Upload
            s3_key = f"{S3_PREFIX}/{key}-{nr}.mp3"
            run([
                "aws", "s3", "cp",
                str(out_file),
                f"s3://{S3_BUCKET}/{s3_key}",
                "--content-type", "audio/mpeg",
                "--cache-control", "public, max-age=31536000, immutable",
            ])
            cf_paths.append(f"/{s3_key}")

    if cf_paths and not dry:
        print(f"\n>>> CloudFront invalidation ({len(cf_paths)} paths)")
        run([
            "aws", "cloudfront", "create-invalidation",
            "--distribution-id", CF_DIST,
            "--paths", *cf_paths,
        ], stdout=subprocess.DEVNULL)
        print(f"Done. Invalidate paths: {cf_paths}")

if __name__ == "__main__":
    main()
