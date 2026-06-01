"""
Auto-crop arkuszy CKE webp: kazda strona PDF zawiera 1-3 zadania,
generujemy osobne webp per zadanie.

Algorytm:
  1. W kazdym ark-XX.webp wykrywamy fioletowe paski naglowkow zadan
     (height >= 20px, kolor RGB w zakresie). Cienkie paski 1px to ramki Brudnopis.
  2. Z OCR (tesseract pol, x3 upscale) odczytujemy numer zadania.
  3. Tnie kazdy webp od y_naglowka do y_naglowek_next_na_tej_samej_stronie
     (lub do konca strony minus stopka).
  4. Jesli strona N+1 NIE zaczyna sie od naglowka, doklejamy jej fragment
     (od y=0 do pierwszego naglowka lub konca-stopki) do zadania z N.
  5. Zapisujemy zad-NN.webp.

Usage: python crop-arkusz.py <folder>
  python crop-arkusz.py public/arkusze/matematyka/2026-maj-pp/
"""
import sys
import re
import subprocess
from pathlib import Path
from PIL import Image
import numpy as np

PURPLE_R = (180, 240)
PURPLE_G = (170, 220)
PURPLE_B = (210, 250)
MIN_HEADER_HEIGHT = 20  # px
MIN_PURPLE_PCT = 0.6  # naglowki "Zadanie N." rozciagaja sie na pelna szerokosc (>60% wiersza fioletowe). Slupki wykresow zajmuja ~30% - filtr je odrzuca.
FOOTER_PX = 100         # ostatnie 100px to stopka CKE (page number + watermark)
TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def detect_header_bands(img_arr):
    """Zwroc liste (y_start, y_end) bandow fioletowych o wysokosci >= MIN_HEADER_HEIGHT."""
    r, g, b = img_arr[:, :, 0], img_arr[:, :, 1], img_arr[:, :, 2]
    purple = (
        (r >= PURPLE_R[0]) & (r <= PURPLE_R[1]) &
        (g >= PURPLE_G[0]) & (g <= PURPLE_G[1]) &
        (b >= PURPLE_B[0]) & (b <= PURPLE_B[1])
    )
    pct = purple.mean(axis=1)
    is_band = pct >= MIN_PURPLE_PCT
    bands = []
    start = None
    for y, h in enumerate(is_band):
        if h and start is None:
            start = y
        elif not h and start is not None:
            if y - start >= MIN_HEADER_HEIGHT:
                bands.append((start, y))
            start = None
    if start is not None and len(is_band) - start >= MIN_HEADER_HEIGHT:
        bands.append((start, len(is_band)))
    return bands

def ocr_zadanie_nr(img_pil, y_start, y_end):
    """OCR fragmentu naglowka, zwraca numer zadania (int) lub None.
    Probuje wielu PSM-ow do skutku - niektore arkusze (geografia, polski) maja
    inny layout naglowka i jeden psm nie wystarcza."""
    # Crop pasek 5px wyzej + 10px nizej (niektore literki "g","y" wystaja)
    crop = img_pil.crop((0, max(0, y_start - 5), img_pil.width, y_end + 10))
    # Upscale x4 + grayscale + lekki binaryzator dla lepszego OCR
    crop_up = crop.resize((crop.width * 4, crop.height * 4), Image.LANCZOS).convert("L")
    # Binaryzacja: piksele < 128 -> czarny, reszta bialy. Daje wyraziste literki.
    crop_bin = crop_up.point(lambda p: 0 if p < 128 else 255)
    tmp = Path.cwd() / "_ocr_tmp.png"
    crop_bin.save(tmp)
    try:
        # Probujemy psm 7 (linia), potem 6 (blok), potem 11 (sparse text)
        for psm in ("7", "6", "11"):
            out_bytes = subprocess.run(
                [TESSERACT, str(tmp), "-", "-l", "pol", "--psm", psm],
                capture_output=True, timeout=30,
            ).stdout
            out = out_bytes.decode("utf-8", errors="replace")
            m = re.search(r"[Zz]adanie\s*(\d+)", out)
            if m:
                return int(m.group(1))
    except Exception as e:
        print(f"  OCR error: {e}")
        return None
    finally:
        tmp.unlink(missing_ok=True)
    return None

def process_folder(folder: Path):
    # Akceptujemy rozne konwencje nazw stron: ark-XX.webp (mat/chem/bio/ang),
    # arkusz-XX.webp (geografia), cz1-XX.webp + cz2-XX.webp (polski dwuczesciowy).
    patterns = ["ark-*.webp", "arkusz-*.webp", "cz1-*.webp", "cz2-*.webp", "cz12-*.webp", "cz3-*.webp"]
    files = sorted({p for pat in patterns for p in folder.glob(pat)})
    if not files:
        print(f"Brak ark/arkusz/cz-*.webp w {folder}")
        return

    # Wykryj wszystkie naglowki: [(page_idx, y_start, y_end, file_path, image, height_total, zad_nr)]
    pages = []  # list per page: (file, image, headers=[(y_start, y_end, nr)])
    for f in files:
        img = Image.open(f).convert("RGB")
        arr = np.array(img)
        bands = detect_header_bands(arr)
        headers = []
        for ys, ye in bands:
            nr = ocr_zadanie_nr(img, ys, ye)
            headers.append((ys, ye, nr))
            print(f"  {f.name}: naglowek y={ys}-{ye} -> Zadanie {nr}")
        if not bands:
            print(f"  {f.name}: brak naglowkow (kontynuacja poprzedniego zadania albo cover/spis tresci)")
        pages.append({"file": f, "image": img, "headers": headers, "h": img.height})

    # Zbieramy fragmenty per zadanie
    # zad[N] = lista (page_idx, y_top, y_bottom)
    # Continuation: tylko 1 strona maks. Strony BRUDNOPIS (puste z siatka) nie powinny
    # sie sklejac — ograniczamy do najwyzej 1 next-page continuation per zadanie.
    zad = {}
    pi_last_continuation = -10  # ostatni page_idx ktory zostal uznany za continuation
    for pi, page in enumerate(pages):
        headers = page["headers"]
        h_max = page["h"] - FOOTER_PX
        first_header_y = headers[0][0] if headers else None

        # Continuation gora: jesli strona NIE zaczyna od naglowka, doklejamy gore poprzedniemu zadaniu.
        # ALE: tylko jesli poprzednia strona miala naglowek (= zadanie nadal trwa) i pi-1 nie byla juz continuation.
        # To zapobiega skleceniu BRUDNOPIS (strona 34) -> kontynuacja zadania 33 (strona 33).
        if (first_header_y is None or first_header_y > 80) and pi > 0:
            prev_had_header = pages[pi - 1]["headers"]
            if prev_had_header and pi - 1 != pi_last_continuation:
                prev_zadanie = prev_had_header[-1][2]
                if prev_zadanie is not None:
                    top = 0
                    bottom = first_header_y - 5 if first_header_y else h_max
                    zad.setdefault(prev_zadanie, []).append((pi, top, bottom))
                    pi_last_continuation = pi

        # 3) Kazdy header zaczyna fragment do nastepnego headera (na tej samej stronie) lub do h_max
        for hi, (ys, ye, nr) in enumerate(headers):
            if nr is None:
                continue
            top = max(0, ys - 5)
            next_y = headers[hi + 1][0] - 5 if hi + 1 < len(headers) else h_max
            zad.setdefault(nr, []).append((pi, top, next_y))

    # Zapisz fragmenty
    print(f"\nWykryto {len(zad)} zadan. Generuje crop'y...")
    for nr in sorted(zad.keys()):
        fragments = zad[nr]
        # Sklej pionowo wszystkie fragmenty
        crops = []
        for pi, top, bottom in fragments:
            img = pages[pi]["image"]
            crops.append(img.crop((0, top, img.width, bottom)))
        if len(crops) == 1:
            final = crops[0]
        else:
            width = max(c.width for c in crops)
            total_h = sum(c.height for c in crops)
            final = Image.new("RGB", (width, total_h), (255, 255, 255))
            y = 0
            for c in crops:
                final.paste(c, (0, y))
                y += c.height
        out = folder / f"zad-{nr:02d}.webp"
        final.save(out, "WEBP", quality=85)
        print(f"  zad-{nr:02d}.webp: {len(fragments)} fragment(ow), {final.height}px")

if __name__ == "__main__":
    folder = Path(sys.argv[1]).resolve()
    process_folder(folder)
