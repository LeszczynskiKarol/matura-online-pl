"""
Crop WOS F2015 — nagłówki "Zadanie N." są BOLD czarnym tekstem na białym
(nie szare paski jak nowa formula). Wykrywamy przez Tesseract OCR z TSV.
"""
import re
import subprocess
import sys
from pathlib import Path
from PIL import Image

TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def find_zadania_y(img):
    """OCR strony, zwraca [(y_orig, zadanie_nr), ...] dla linii zaczynajacych od 'Zadanie N.'"""
    SCALE = 3
    up = img.resize((img.width * SCALE, img.height * SCALE), Image.LANCZOS)
    tmp = Path.cwd() / "_wos_ocr.png"
    up.save(tmp)
    try:
        r = subprocess.run(
            [TESSERACT, str(tmp), "-", "-l", "pol", "tsv"],
            capture_output=True, timeout=120,
        )
        tsv = r.stdout.decode("utf-8", errors="replace")
    finally:
        tmp.unlink(missing_ok=True)

    lines = tsv.replace("\r", "").strip().split("\n")
    if len(lines) < 2: return []
    header = lines[0].split("\t")
    try:
        top_idx = header.index("top")
        text_idx = header.index("text")
        ln_idx = header.index("line_num")
        par_idx = header.index("par_num")
        blk_idx = header.index("block_num")
    except ValueError:
        return []

    grouped = {}
    for ln in lines[1:]:
        parts = ln.split("\t")
        if len(parts) <= text_idx: continue
        txt = parts[text_idx].strip()
        if not txt: continue
        try:
            key = (parts[blk_idx], parts[par_idx], parts[ln_idx])
            top = int(parts[top_idx])
        except (ValueError, IndexError):
            continue
        if key not in grouped:
            grouped[key] = {"top": top, "words": []}
        grouped[key]["words"].append(txt)

    result = []
    for _, info in sorted(grouped.items(), key=lambda kv: kv[1]["top"]):
        line_text = " ".join(info["words"])
        m = re.match(r"^[Zz]adanie\s+(\d+)\.?\s*(?:\([\d\-\s]+\))?", line_text)
        if m:
            result.append((info["top"] // SCALE, int(m.group(1))))
    return result

def main(folder):
    folder = Path(folder)
    files = sorted(folder.glob("ark-*.webp"))
    if not files:
        print(f"Brak ark-*.webp w {folder}")
        return

    # Znajdz wszystkie naglowki w arkuszu
    headers = []  # [(page_idx, y, nr, img)]
    for pi, f in enumerate(files, 1):
        img = Image.open(f).convert("RGB")
        zads = find_zadania_y(img)
        for y, nr in zads:
            headers.append((pi, y, nr, img, f))
            print(f"  {f.name}: y={y} Zadanie {nr}")

    # Crop: kazdy zadanie od jego y do nastepnego (lub end-of-page+continuation)
    print(f"\nWykryto {len(headers)} naglowkow")
    for i, (pi, y, nr, img, f) in enumerate(headers):
        top = max(0, y - 10)
        # Sledz koniec - albo nastepny header na tej samej stronie, albo end-of-page-100
        next_y_same_page = None
        for j in range(i + 1, len(headers)):
            npi, ny, _, _, _ = headers[j]
            if npi == pi:
                next_y_same_page = ny - 10
                break
            else:
                break

        crops = []
        if next_y_same_page:
            crops.append(img.crop((0, top, img.width, next_y_same_page)))
        else:
            crops.append(img.crop((0, top, img.width, img.height - 80)))
            # Continuation: nastepna strona jesli nie ma na niej header w gornych 100px
            if i + 1 < len(headers):
                npi, ny, _, nimg, _ = headers[i + 1]
                if npi == pi + 1 and ny > 100:
                    crops.append(nimg.crop((0, 80, nimg.width, ny - 10)))
            elif pi < len(files):
                # Ostatni zadanie - cala kolejna strona
                next_f = files[pi]  # pi (1-indexed) = index pi-1+1 = pi
                if next_f != f:
                    nimg = Image.open(next_f).convert("RGB")
                    crops.append(nimg.crop((0, 80, nimg.width, nimg.height - 80)))

        if len(crops) == 1:
            out = crops[0]
        else:
            width = max(c.width for c in crops)
            total_h = sum(c.height for c in crops)
            out = Image.new("RGB", (width, total_h), (255, 255, 255))
            yy = 0
            for c in crops:
                out.paste(c, (0, yy))
                yy += c.height

        out_path = folder / f"zad-{nr:02d}.webp"
        out.save(out_path, "WEBP", quality=85)

    print(f"Zapisano zad-*.webp")

if __name__ == "__main__":
    main(sys.argv[1])
