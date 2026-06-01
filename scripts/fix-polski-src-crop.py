"""
Dla problematycznych polskich zadan ktore wciaz uzywaja pelnej strony (ark-/cz1-/cz12-)
jako src zadania:
1. Otwiera referenced webp
2. Detect fioletowych naglowkow "Zadanie N."
3. Tnie fragment dla TEGO zadania (uzywajac OCR + heurystyki)
4. Zapisuje zad-NN.webp + updates src w meta

Idempotentne. Pomija jesli zad-NN.webp juz istnieje.
"""
import re
import subprocess
from pathlib import Path
from PIL import Image
import numpy as np

CONTENT = Path(r"D:\matura-online.pl\src\content\zadania")
PUBLIC = Path(r"D:\matura-online.pl\public\arkusze")
TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Re: znajdź <MaterialZrodlowy> z alt="Zadanie N..." i src=pełna strona
MATERIAL_RE = re.compile(
    r'(<MaterialZrodlowy\s+src=")([^"]+)("[^>]*?alt="(Zadanie\s+\d+[^"]*)"[^>]*?/>)',
    re.DOTALL,
)

def detect_purple_bands(arr, min_h=20):
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    purple = (r>=180)&(r<=240)&(g>=170)&(g<=220)&(b>=210)&(b<=250)
    pct = purple.mean(axis=1)
    is_band = pct >= 0.5
    bands = []
    start = None
    for y, h in enumerate(is_band):
        if h and start is None:
            start = y
        elif not h and start is not None:
            if y - start >= min_h:
                bands.append((start, y))
            start = None
    return bands

def ocr_nr(img, y_start, y_end):
    crop = img.crop((0, max(0, y_start-5), img.width, y_end+10))
    crop_up = crop.resize((crop.width*4, crop.height*4), Image.LANCZOS).convert("L")
    crop_bin = crop_up.point(lambda p: 0 if p < 128 else 255)
    tmp = Path.cwd() / "_ocr_fix.png"
    crop_bin.save(tmp)
    try:
        for psm in ("7","6","11"):
            r = subprocess.run([TESSERACT, str(tmp), "-", "-l", "pol", "--psm", psm],
                               capture_output=True, timeout=30)
            txt = r.stdout.decode("utf-8", errors="replace")
            m = re.search(r"[Zz]adanie\s*(\d+)", txt)
            if m:
                return int(m.group(1))
    finally:
        tmp.unlink(missing_ok=True)
    return None

def process_file(mdx_path: Path):
    text = mdx_path.read_text(encoding="utf-8")
    # Znajdz zadanie nr z nazwy pliku
    m = re.search(r"-(\d+)\.mdx$", mdx_path.name)
    if not m: return 0
    zad_nr = int(m.group(1))
    zad_filename = f"zad-{zad_nr:02d}.webp"

    changed = 0
    new_text = text

    # Znajdz wszystkie MaterialZrodlowy z alt=Zadanie i src=pelna strona
    for match in list(MATERIAL_RE.finditer(text)):
        src_url = match.group(2)
        if not re.search(r'/(ark|arkusz|cz1|cz2|cz12)-\d+\.webp$', src_url):
            continue
        if 'zad-' in src_url:
            continue
        # Pobierz lokalny path
        local_folder = PUBLIC / src_url.replace("/arkusze/", "").rsplit("/", 1)[0]
        page_filename = src_url.rsplit("/", 1)[1]
        page_path = local_folder / page_filename
        if not page_path.exists():
            continue

        zad_path = local_folder / zad_filename
        if zad_path.exists():
            # Tylko update src, plik istnieje
            new_text = new_text.replace(src_url, f"{src_url.rsplit('/', 1)[0]}/{zad_filename}")
            changed += 1
            print(f"  {mdx_path.name}: zad-{zad_nr:02d}.webp istnieje, update src")
            continue

        # Pociac referenced page na fragment dla TEGO zadania
        img = Image.open(page_path).convert("RGB")
        arr = np.array(img)
        bands = detect_purple_bands(arr)
        # OCR per band żeby znaleźć ten dla zad_nr
        target_band_idx = None
        ocr_results = []
        for i, (ys, ye) in enumerate(bands):
            nr = ocr_nr(img, ys, ye)
            ocr_results.append(nr)
            if nr == zad_nr:
                target_band_idx = i
                break

        if target_band_idx is None:
            # FALLBACK: OCR czesciowo czytelne. Jesli ktorykolwiek band ma rozpoznany nr X,
            # i zadania w CKE sa KOLEJNE, mozemy wyliczyc indeks dla zad_nr.
            for i, nr in enumerate(ocr_results):
                if nr is not None:
                    # Jesli band i to nr X, to band 0 to nr (X - i), band j to (X - i + j)
                    base = nr - i
                    candidate_idx = zad_nr - base
                    if 0 <= candidate_idx < len(bands):
                        target_band_idx = candidate_idx
                        print(f"  {mdx_path.name}: FALLBACK pozycyjny (band {nr} na pozycji {i}, zad {zad_nr} → band {candidate_idx})")
                        break

        if target_band_idx is None:
            print(f"  {mdx_path.name}: nie znalazlem naglowka zad {zad_nr} w {page_filename} (OCR: {ocr_results})")
            continue

        # Crop od bands[target_band_idx].start do bands[target+1].start (lub end-of-page-100)
        ys, ye = bands[target_band_idx]
        top = max(0, ys - 5)
        if target_band_idx + 1 < len(bands):
            bottom = bands[target_band_idx + 1][0] - 5
        else:
            bottom = img.height - 100  # zostaw footer

        crop = img.crop((0, top, img.width, bottom))
        crop.save(zad_path, "WEBP", quality=85)
        print(f"  {mdx_path.name}: utworzono {zad_filename} ({crop.height}px), update src")
        new_text = new_text.replace(src_url, f"{src_url.rsplit('/', 1)[0]}/{zad_filename}")
        changed += 1

    if changed > 0:
        mdx_path.write_text(new_text, encoding="utf-8")
    return changed

def main():
    total = 0
    for f in sorted(CONTENT.glob("jezyk-polski-*.mdx")):
        c = process_file(f)
        total += c
    print(f"\nNaprawiono {total} src w plikach")

if __name__ == "__main__":
    main()
