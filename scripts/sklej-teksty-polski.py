"""
Sklej teksty zrodlowe polskich arkuszy w JEDEN duzy webp: tekst-zrodlowy.webp.

Sklejamy ark-04 + ark-05 + ark-06 (gornia czesc do pierwszego fioletowego naglowka
"Zadanie 1.").

Z1 (Zadanie 1.) detect przez fioletowy band — DZIALA poprawnie.

Wynik: tekst-zrodlowy.webp w folderze arkusza, plus update src w meta wszystkich
zadan polskich ktore linkowaly na ark-04/05/06 jako Tekst 1/Tekst 2.
"""
import re
from pathlib import Path
from PIL import Image
import numpy as np

CONTENT = Path(r"D:\matura-online.pl\src\content\zadania")
PUBLIC = Path(r"D:\matura-online.pl\public\arkusze")

ARKUSZE = [
    {"id": "2023-maj-pp", "folder": "2023-maj-pp", "prefix": "cz1"},
    {"id": "2024-maj-pp", "folder": "2024-maj-pp", "prefix": "cz12"},
    {"id": "2025-maj-pp", "folder": "2025-maj-pp", "prefix": "cz1"},
    {"id": "2026-maj-pp", "folder": "2026-maj-pp-cz1", "prefix": "ark"},
]

def detect_purple_header_y(arr, after_y=0):
    """Znajduje 1szy fioletowy naglowek po y=after_y, wysokosc >= 20px."""
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    purple = (r>=180)&(r<=240)&(g>=170)&(g<=220)&(b>=210)&(b<=250)
    pct = purple.mean(axis=1)
    is_band = pct >= 0.5
    for y in range(after_y, len(is_band)):
        if is_band[y]:
            end = y
            while end < len(is_band) and is_band[end]:
                end += 1
            if end - y >= 20:
                return y
    return None

def sklej_arkusz(ark):
    folder = PUBLIC / "jezyk-polski" / ark["folder"]
    prefix = ark["prefix"]
    print(f"\n=== {ark['id']} ===")

    # Wczytaj strony 04, 05, 06
    pages = {}
    for n in (4, 5, 6):
        p = folder / f"{prefix}-{n:02d}.webp"
        if p.exists():
            pages[n] = Image.open(p).convert("RGB")

    if 4 not in pages or 5 not in pages:
        print(f"  brak stron 04 lub 05")
        return False

    # Z1 (pierwszy "Zadanie 1." fioletowy) — szukamy na stronie 5 i 6
    z1_page = None
    z1_y = None
    for n in (5, 6):
        if n not in pages:
            continue
        arr = np.array(pages[n])
        y = detect_purple_header_y(arr, after_y=100)  # pomijamy gore strony
        if y is not None:
            z1_page = n
            z1_y = y
            print(f"  Z1 znaleziony na str. {n}, y={y}")
            break

    # Sklej fragmenty:
    # - cala strona 04 (od y=120 zeby pominac header strony, do height-100 footer)
    # - cala strona 05 (od y=80 zeby pominac header, do height-100 lub do z1_y jesli Z1 tu)
    # - fragment strony 06 (od y=80 do z1_y) — jesli Z1 jest na str 6
    fragments = []

    # Strona 04
    img4 = pages[4]
    fragments.append(img4.crop((0, 120, img4.width, img4.height - 100)))

    # Strona 05
    img5 = pages[5]
    if z1_page == 5:
        fragments.append(img5.crop((0, 80, img5.width, max(80, z1_y - 10))))
    else:
        fragments.append(img5.crop((0, 80, img5.width, img5.height - 100)))

    # Strona 06 (jesli Z1 tutaj)
    if z1_page == 6 and 6 in pages:
        img6 = pages[6]
        fragments.append(img6.crop((0, 80, img6.width, max(80, z1_y - 10))))

    # Sklej pionowo
    width = max(f.width for f in fragments)
    total_h = sum(f.height for f in fragments)
    out = Image.new("RGB", (width, total_h), (255, 255, 255))
    y = 0
    for f in fragments:
        out.paste(f, (0, y))
        y += f.height

    out_path = folder / "tekst-zrodlowy.webp"
    out.save(out_path, "WEBP", quality=85)
    print(f"  Zapisano {out_path.name}: {out.size} ({len(fragments)} fragment)")
    return True

def update_meta(ark):
    """Zamiana w meta: gdzie alt zawiera "Tekst" — src zostaje na tekst-zrodlowy.webp.
    Plus usun duplikaty (jak Tekst 1 i Tekst 2 byly osobno, scalimy w 1 link)."""
    folder = ark["folder"]
    prefix = ark["prefix"]
    new_src = f'/arkusze/jezyk-polski/{folder}/tekst-zrodlowy.webp'

    # Re: dopasuj caly blok <MaterialZrodlowy ... alt="Tekst..." ... />
    BLOCK_RE = re.compile(
        r'<MaterialZrodlowy[^>]*?alt="[^"]*Tekst[^"]*"[^>]*?/>',
        re.DOTALL,
    )

    changed = 0
    for f in sorted(CONTENT.glob(f"jezyk-polski-{ark['id']}-*.mdx")):
        text = f.read_text(encoding="utf-8")
        blocks = BLOCK_RE.findall(text)
        if not blocks:
            continue
        # Zachowaj TYLKO pierwszy blok i zmien src na tekst-zrodlowy.webp.
        # Usun pozostale.
        first = blocks[0]
        # Zamien src w first
        new_first = re.sub(r'src="[^"]+"', f'src="{new_src}"', first, count=1)
        # Zamien alt+caption na ogolne
        new_first = re.sub(r'alt="[^"]*"', 'alt="Teksty źródłowe z arkusza CKE"', new_first, count=1)
        new_first = re.sub(r'caption="[^"]*"', 'caption="Teksty źródłowe z arkusza CKE (skany oryginalnych stron 4-6)."', new_first, count=1)
        new_first = re.sub(r"caption='[^']*'", "caption='Teksty źródłowe z arkusza CKE (skany oryginalnych stron 4-6).'", new_first, count=1)
        # pdfPage{4} -> {4}
        # Zostaw pdfUrl bez zmian
        new_text = text.replace(first, new_first)
        # Usun pozostale bloki Tekst...
        for blk in blocks[1:]:
            new_text = new_text.replace(blk + "\n\n", "")
            new_text = new_text.replace(blk + "\n", "")
            new_text = new_text.replace(blk, "")
        # Cleanup multiple blank lines
        new_text = re.sub(r"\n{3,}", "\n\n", new_text)
        if new_text != text:
            f.write_text(new_text, encoding="utf-8")
            changed += 1
    print(f"  Update meta w {changed} plikach")

def main():
    for ark in ARKUSZE:
        ok = sklej_arkusz(ark)
        if ok:
            update_meta(ark)

if __name__ == "__main__":
    main()
