"""
Final fallback: dla webp gdzie OCR caly None, zidentyfikuj ile plikow mdx
odwoluje sie do tego webp jako src zadania, sortuj po nr zadania, przypisz
bandy w kolejnosci. Tworzy zad-NN.webp + update src.
"""
import re
from pathlib import Path
from PIL import Image
import numpy as np
from collections import defaultdict

CONTENT = Path(r"D:\matura-online.pl\src\content\zadania")
PUBLIC = Path(r"D:\matura-online.pl\public\arkusze")

MATERIAL_RE = re.compile(
    r'<MaterialZrodlowy[^>]*?src="([^"]+)"[^>]*?alt="(Zadanie\s+(\d+)[^"]*)"[^>]*?/>',
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

def main():
    # 1. Zbierz: src_url -> [(mdx_path, zad_nr), ...] dla problematycznych
    refs = defaultdict(list)
    for f in sorted(CONTENT.glob("jezyk-polski-*.mdx")):
        text = f.read_text(encoding="utf-8")
        for m in MATERIAL_RE.finditer(text):
            src_url, alt, zad_nr = m.group(1), m.group(2), int(m.group(3))
            if re.search(r'/(ark|arkusz|cz1|cz2|cz12)-\d+\.webp$', src_url):
                refs[src_url].append((f, zad_nr))

    print(f"Webp z problematycznymi src: {len(refs)}")

    fixed = 0
    for src_url, mdx_list in refs.items():
        # Sortuj po nr zadania
        mdx_list.sort(key=lambda x: x[1])
        local_folder = PUBLIC / src_url.replace("/arkusze/", "").rsplit("/", 1)[0]
        page_filename = src_url.rsplit("/", 1)[1]
        page_path = local_folder / page_filename
        if not page_path.exists():
            continue

        img = Image.open(page_path).convert("RGB")
        arr = np.array(img)
        bands = detect_purple_bands(arr)
        print(f"\n{page_filename}: {len(bands)} bandow, {len(mdx_list)} zadan odwolujacych sie")
        for f, n in mdx_list:
            print(f"  zad {n}: {f.name}")

        if len(bands) == 0:
            # Brak nagłówków = pełna strona = pewnie tekst zrodlowy w meta jako "zadanie"
            # Pomijamy
            continue

        # Przypisz bandy w kolejnosci do mdx_list (pierwszy band = pierwszy zad)
        if len(bands) != len(mdx_list):
            print(f"  WARN: liczba bandow ({len(bands)}) != liczba zadan ({len(mdx_list)})")

        for idx, (f, zad_nr) in enumerate(mdx_list):
            if idx >= len(bands):
                continue
            ys, ye = bands[idx]
            top = max(0, ys - 5)
            if idx + 1 < len(bands):
                bottom = bands[idx + 1][0] - 5
            else:
                bottom = img.height - 100
            zad_path = local_folder / f"zad-{zad_nr:02d}.webp"
            if zad_path.exists():
                # Tylko update src
                pass
            else:
                crop = img.crop((0, top, img.width, bottom))
                crop.save(zad_path, "WEBP", quality=85)
                print(f"  utworzono zad-{zad_nr:02d}.webp ({crop.height}px)")

            # Update src
            text = f.read_text(encoding="utf-8")
            new_url = f"{src_url.rsplit('/', 1)[0]}/zad-{zad_nr:02d}.webp"
            new_text = text.replace(src_url, new_url)
            if new_text != text:
                f.write_text(new_text, encoding="utf-8")
                fixed += 1

    print(f"\nNaprawiono {fixed} src w plikach")

if __name__ == "__main__":
    main()
