"""
Wycina TEKSTY ZRODLOWE z polskich arkuszy jako tekst-1.webp i tekst-2.webp.

Detekcja: szuka napisu "Tekst 1.", "Tekst 2." (boldem) na stronach ark-04..06
przy uzyciu Tesseract OCR per band. Tekst N konczy sie gdy zaczyna sie Tekst N+1
lub gdy pojawia sie naglowek fioletowy "Zadanie 1.".

Sklejanie multi-strona: jesli Tekst N zaczyna sie na stronie X i konczy na
stronie X+1, sklejamy pionowo fragmenty obu stron.

Wynik: tekst-1.webp, tekst-2.webp w folderze arkusza + update src w meta wszystkich
zadan ktore wczesniej linkowaly na ark-04/05/06 jako "Tekst 1" / "Tekst 2".
"""
import re
import subprocess
from pathlib import Path
from PIL import Image
import numpy as np

CONTENT = Path(r"D:\matura-online.pl\src\content\zadania")
PUBLIC = Path(r"D:\matura-online.pl\public\arkusze")
TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# 4 polskie arkusze do przetworzenia
ARKUSZE = [
    {"id": "2023-maj-pp", "folder": "2023-maj-pp", "prefix": "cz1"},
    {"id": "2024-maj-pp", "folder": "2024-maj-pp", "prefix": "cz12"},
    {"id": "2025-maj-pp", "folder": "2025-maj-pp", "prefix": "cz1"},
    {"id": "2026-maj-pp", "folder": "2026-maj-pp-cz1", "prefix": "ark"},
]

def ocr_text(img, psm="6"):
    """OCR strony — grayscale, mocniejsza binaryzacja (threshold 180 zeby
    szary pasek tla zniknal i tekst zostal czarny)."""
    SCALE = 4
    up = img.resize((img.width * SCALE, img.height * SCALE), Image.LANCZOS).convert("L")
    # Threshold 180: szary pasek (~230) staje sie bialy, czarny tekst (~50) zostaje
    bin_img = up.point(lambda p: 0 if p < 180 else 255)
    tmp = Path.cwd() / "_ocr_full.png"
    bin_img.save(tmp)
    try:
        r = subprocess.run(
            [TESSERACT, str(tmp), "-", "-l", "pol", "--psm", psm, "tsv"],
            capture_output=True, timeout=120,
        )
        return r.stdout.decode("utf-8", errors="replace"), SCALE
    finally:
        tmp.unlink(missing_ok=True)

def find_marker_y(img, marker_re):
    """Zwraca Y pierwszego wystapienia markera (regex) w OCR strony, lub None."""
    tsv = ocr_text(img)
    lines = tsv.strip().split("\n")
    if len(lines) < 2:
        return None
    # Format TSV: level page_num block_num par_num line_num word_num left top width height conf text
    header = lines[0].split("\t")
    try:
        top_idx = header.index("top")
        text_idx = header.index("text")
    except ValueError:
        return None
    # Zbieramy linie tekstu z ich Y (grupuje po line_num + par)
    for ln in lines[1:]:
        parts = ln.split("\t")
        if len(parts) <= text_idx:
            continue
        txt = parts[text_idx]
        if marker_re.search(txt):
            try:
                return int(parts[top_idx])
            except (ValueError, IndexError):
                continue
    return None

# Bardziej efektywne: szukamy "Tekst 1." po linii (sklej slowa z tej samej linii)
def find_line_y(img, line_pattern):
    """Skleja slowa per linia i szuka linii pasujacej do regex. Zwraca Y w skali ORYG."""
    tsv, scale = ocr_text(img)
    lines = tsv.strip().split("\n")
    if len(lines) < 2:
        return None
    header = lines[0].split("\t")
    try:
        top_idx = header.index("top")
        text_idx = header.index("text")
        line_num_idx = header.index("line_num")
        par_idx = header.index("par_num")
        block_idx = header.index("block_num")
    except ValueError:
        return None
    # Grupuj po (block, par, line) -> teksty i top
    grouped = {}
    for ln in lines[1:]:
        parts = ln.split("\t")
        if len(parts) <= text_idx:
            continue
        txt = parts[text_idx].strip()
        if not txt:
            continue
        try:
            key = (parts[block_idx], parts[par_idx], parts[line_num_idx])
            top = int(parts[top_idx])
        except (ValueError, IndexError):
            continue
        if key not in grouped:
            grouped[key] = {"top": top, "words": []}
        grouped[key]["words"].append(txt)
    # Sortuj po top, znajdz pierwsza linia ktora matchuje
    sorted_lines = sorted(grouped.items(), key=lambda kv: kv[1]["top"])
    for _, info in sorted_lines:
        line_text = " ".join(info["words"])
        if line_pattern.search(line_text):
            return info["top"] // scale  # przelicz na oryginalna skale
    return None

def detect_purple_header_y(arr, after_y=0):
    """Znajduje fioletowy naglowek (Zadanie N.) po pozycji after_y."""
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    purple = (r>=180)&(r<=240)&(g>=170)&(g<=220)&(b>=210)&(b<=250)
    pct = purple.mean(axis=1)
    is_band = pct >= 0.5
    for y in range(after_y, len(is_band)):
        if is_band[y]:
            # Sprawdz czy to band >= 20px
            end = y
            while end < len(is_band) and is_band[end]:
                end += 1
            if end - y >= 20:
                return y
    return None

def crop_pages_vertical(pages):
    """Sklejaj pionowo crop'y (lista (img, top, bottom))."""
    crops = []
    for img, top, bottom in pages:
        crops.append(img.crop((0, top, img.width, bottom)))
    if len(crops) == 1:
        return crops[0]
    width = max(c.width for c in crops)
    total_h = sum(c.height for c in crops)
    out = Image.new("RGB", (width, total_h), (255, 255, 255))
    y = 0
    for c in crops:
        out.paste(c, (0, y))
        y += c.height
    return out

def process_arkusz(ark):
    folder = PUBLIC / "jezyk-polski" / ark["folder"]
    prefix = ark["prefix"]
    print(f"\n=== {ark['id']} ({folder.name}) ===")

    # Wczytaj strony 04, 05, 06
    pages = {}
    for n in (4, 5, 6):
        p = folder / f"{prefix}-{n:02d}.webp"
        if not p.exists():
            print(f"  brak {p.name}")
            continue
        pages[n] = Image.open(p).convert("RGB")

    if 4 not in pages:
        return

    # Detekcja Tekst 1. i Tekst 2. na stronach 04-06
    locations = {}  # nazwa -> (page_nr, y)
    for n, img in pages.items():
        for marker, name in [
            (re.compile(r"\bTekst\s*1\b\.?", re.IGNORECASE), "T1"),
            (re.compile(r"\bTekst\s*2\b\.?", re.IGNORECASE), "T2"),
        ]:
            if name in locations:
                continue
            y = find_line_y(img, marker)
            if y is not None:
                locations[name] = (n, y)
                print(f"  {name} na stronie {n} y={y}")

    # Detekcja "Zadanie 1." (fioletowy band) na stronach 05-06
    for n in (5, 6):
        if n not in pages: continue
        arr = np.array(pages[n])
        zad1_y = detect_purple_header_y(arr, after_y=0)
        if zad1_y is not None:
            locations["Z1"] = (n, zad1_y)
            print(f"  Z1 (Zadanie 1.) na stronie {n} y={zad1_y}")
            break

    # Crop Tekst 1: od T1 do T2 (lub do Z1 jesli T2 brak)
    if "T1" in locations:
        t1_pages = []
        t1_p, t1_y = locations["T1"]
        end_marker = locations.get("T2") or locations.get("Z1")
        if end_marker is None:
            # nieznany koniec - bierzemy do konca strony T1
            t1_pages.append((pages[t1_p], max(0, t1_y - 10), pages[t1_p].height - 100))
        else:
            end_p, end_y = end_marker
            if end_p == t1_p:
                # T1 i T2/Z1 na tej samej stronie
                t1_pages.append((pages[t1_p], max(0, t1_y - 10), end_y - 10))
            else:
                # T1 na stronie t1_p, T2 na end_p (kolejna)
                t1_pages.append((pages[t1_p], max(0, t1_y - 10), pages[t1_p].height - 100))
                # dorzuc fragmenty na posrednich stronach
                for mid in range(t1_p + 1, end_p):
                    if mid in pages:
                        t1_pages.append((pages[mid], 100, pages[mid].height - 100))
                # koncowa strona
                t1_pages.append((pages[end_p], 100, end_y - 10))
        out = crop_pages_vertical(t1_pages)
        out_path = folder / "tekst-1.webp"
        out.save(out_path, "WEBP", quality=85)
        print(f"  TEKST 1: {out_path.name} ({out.height}px, {len(t1_pages)} fragment)")

    # Crop Tekst 2: od T2 do Z1
    if "T2" in locations:
        t2_pages = []
        t2_p, t2_y = locations["T2"]
        end_marker = locations.get("Z1")
        if end_marker is None:
            t2_pages.append((pages[t2_p], max(0, t2_y - 10), pages[t2_p].height - 100))
        else:
            end_p, end_y = end_marker
            if end_p == t2_p:
                t2_pages.append((pages[t2_p], max(0, t2_y - 10), end_y - 10))
            else:
                t2_pages.append((pages[t2_p], max(0, t2_y - 10), pages[t2_p].height - 100))
                for mid in range(t2_p + 1, end_p):
                    if mid in pages:
                        t2_pages.append((pages[mid], 100, pages[mid].height - 100))
                t2_pages.append((pages[end_p], 100, end_y - 10))
        out = crop_pages_vertical(t2_pages)
        out_path = folder / "tekst-2.webp"
        out.save(out_path, "WEBP", quality=85)
        print(f"  TEKST 2: {out_path.name} ({out.height}px, {len(t2_pages)} fragment)")

def update_meta_src(ark):
    """Zamiana ark-04/cz1-04/cz12-04 -> tekst-1.webp, analogicznie -05 -> tekst-2.webp
    ale TYLKO w MaterialZrodlowy gdzie alt="Tekst 1" lub "Tekst 2"."""
    folder = ark["folder"]
    prefix = ark["prefix"]
    folder_path = PUBLIC / "jezyk-polski" / folder
    tekst1_exists = (folder_path / "tekst-1.webp").exists()
    tekst2_exists = (folder_path / "tekst-2.webp").exists()

    changed = 0
    for f in sorted(CONTENT.glob(f"jezyk-polski-{ark['id']}-*.mdx")):
        text = f.read_text(encoding="utf-8")
        new_text = text
        if tekst1_exists:
            # Zamien src wewnątrz bloku z alt="Tekst 1..."
            pattern = re.compile(
                rf'(src=")(/arkusze/jezyk-polski/{folder}/){prefix}-(?:04|05|06)\.webp(")([^>]*?alt="Tekst\s*1)',
                re.DOTALL,
            )
            new_text = pattern.sub(rf'\1\2tekst-1.webp\3\4', new_text)
        if tekst2_exists:
            pattern = re.compile(
                rf'(src=")(/arkusze/jezyk-polski/{folder}/){prefix}-(?:04|05|06)\.webp(")([^>]*?alt="Tekst\s*2)',
                re.DOTALL,
            )
            new_text = pattern.sub(rf'\1\2tekst-2.webp\3\4', new_text)
        if new_text != text:
            f.write_text(new_text, encoding="utf-8")
            changed += 1
    print(f"  Update src w {changed} plikach")

def main():
    for ark in ARKUSZE:
        process_arkusz(ark)
        update_meta_src(ark)

if __name__ == "__main__":
    main()
