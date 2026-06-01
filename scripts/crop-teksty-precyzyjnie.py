"""
Wycina OSOBNE teksty zrodlowe polskich arkuszy:
- tekst-1.webp (Tekst 1 — od paska "Tekst 1." do paska "Tekst 2.")
- tekst-2.webp (Tekst 2 — od paska "Tekst 2." do fioletowego "Zadanie 1.")

Detekcja paska "Tekst N." przez kolor: szary pasek o tle ~RGB(225-240), bold czarne litery.
Z1 (fioletowy "Zadanie 1.") - juz dziala.

Update src per zadanie:
- jesli MaterialZrodlowy ma alt zawierajacy "Tekst 1" -> src=tekst-1.webp
- jesli alt zawiera "Tekst 2" -> src=tekst-2.webp
- inne (plakat, obraz) -> bez zmian
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

def detect_gray_bands(arr, min_h=20):
    """Wykryj poziome paski jasnoszare (RGB ~ 220-245, kolory zbliżone do siebie)."""
    r, g, b = arr[:,:,0].astype(int), arr[:,:,1].astype(int), arr[:,:,2].astype(int)
    # Jasnoszary: kazdy kanal 215-245, kanaly podobne (|diff| < 8)
    gray = ((r >= 215) & (r <= 245) & (g >= 215) & (g <= 245) & (b >= 215) & (b <= 245)
            & (abs(r - g) < 8) & (abs(g - b) < 8))
    pct = gray.mean(axis=1)
    is_band = pct >= 0.4
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

def detect_purple_header_y(arr, after_y=0):
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
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

def find_tekst_paski(pages):
    """Dla kazdej strony 04,05,06 znajdz JASNOSZARE paski.
    Zakladamy: 1szy pasek na ark-04 = Tekst 1, 1szy pasek na ark-05 = Tekst 2.
    Tekst 1 jest zawsze przed Tekst 2."""
    out = {}
    for n, img in pages.items():
        arr = np.array(img)
        bands = detect_gray_bands(arr, min_h=20)
        # Pomijamy banded ktore sa BARDZO blisko gory/dolu strony (header/footer)
        bands = [(s,e) for s,e in bands if s > 50 and e < img.height - 50]
        out[n] = bands
        print(f"  str {n}: {len(bands)} szare paski")
        for s, e in bands[:5]:
            print(f"    y={s}-{e} (h={e-s})")
    return out

def crop_pages_vertical(crops):
    if len(crops) == 1: return crops[0]
    width = max(c.width for c in crops)
    total_h = sum(c.height for c in crops)
    out = Image.new("RGB", (width, total_h), (255, 255, 255))
    y = 0
    for c in crops:
        out.paste(c, (0, y))
        y += c.height
    return out

def find_split_t1_t2(img5):
    """Na stronie 5 znajdz Y gdzie konczy sie Tekst 1 i zaczyna Tekst 2.
    Heurystyka: szukamy 'pasa horyzontalnego' o cieniem CIEMNOSZARYM (kolor ~140-200).
    Pasek 'Tekst N.' ma cienka linie ~30-40px gdzie srednia kolor jest ~150-200
    (zmieszany tekst+tlo)."""
    arr = np.array(img5)
    h = arr.shape[0]
    # Srednia jasnosc per rzad
    gray = arr.mean(axis=2)  # RGB->szary
    row_mean = gray.mean(axis=1)
    # Bialy rzad: ~250, szary pasek: ~200-230, ciemna linia tekstu: ~150-200
    # Pasek "Tekst N." to zwykle 2-3 ciemne linie z odstepami
    # Szukamy: rzedy ktore sa CIEMNIEJSZE niz typowe biale (<240)
    is_text = row_mean < 235
    # Klastry ciemnych rzedow
    bands = []
    start = None
    for y, t in enumerate(is_text):
        if t and start is None:
            start = y
        elif not t and start is not None:
            if y - start >= 4:  # tekst ma kilka pikseli wysokosci
                bands.append((start, y, row_mean[start:y].mean()))
            start = None
    # Filtruj: szukamy bandow w 1/4 - 1/2 strony
    candidates = [(s, e, m) for s, e, m in bands if h * 0.1 < s < h * 0.6 and e - s >= 20]
    if not candidates:
        return None
    # Wybieramy band ktory jest najgrubszy (paski naglowkowe maja czesto ~25-50px)
    candidates.sort(key=lambda x: -(x[1] - x[0]))
    return candidates[0][0]

def process_arkusz(ark):
    folder = PUBLIC / "jezyk-polski" / ark["folder"]
    prefix = ark["prefix"]
    print(f"\n=== {ark['id']} ===")

    pages = {}
    for n in (4, 5, 6):
        p = folder / f"{prefix}-{n:02d}.webp"
        if p.exists():
            pages[n] = Image.open(p).convert("RGB")

    if 4 not in pages or 5 not in pages:
        print(f"  brak pages 04/05")
        return

    # Z1 na str 5 lub 6
    z1_page = None
    z1_y = None
    for n in (5, 6):
        if n not in pages: continue
        arr = np.array(pages[n])
        y = detect_purple_header_y(arr, after_y=200)
        if y is not None:
            z1_page, z1_y = n, y
            break
    print(f"  Z1: str {z1_page} y={z1_y}")

    if not z1_page:
        print(f"  POMIJAM - brak Z1")
        return

    # T1/T2 split na stronie 5: szukamy pasek "Tekst 2."
    img5 = pages[5]
    t2_y_on_p5 = find_split_t1_t2(img5)
    print(f"  T2 start na str 5: y={t2_y_on_p5}")

    if t2_y_on_p5 is None:
        # Fallback: srodek strony 5
        t2_y_on_p5 = img5.height // 4
        print(f"  fallback T2 = h//4 = {t2_y_on_p5}")

    # CROP Tekst 1: cala strona 4 + góra strony 5 do t2_y_on_p5
    img4 = pages[4]
    t1_crops = [
        img4.crop((0, 120, img4.width, img4.height - 100)),
        img5.crop((0, 80, img5.width, t2_y_on_p5 - 5)),
    ]
    t1_out = crop_pages_vertical(t1_crops)
    t1_out.save(folder / "tekst-1.webp", "WEBP", quality=85)
    print(f"  tekst-1.webp: {t1_out.size} ({len(t1_crops)} fragment)")

    # CROP Tekst 2: od t2_y_on_p5 na str 5 do Z1
    t2_crops = []
    if z1_page == 5:
        t2_crops.append(img5.crop((0, max(0, t2_y_on_p5 - 5), img5.width, z1_y - 5)))
    else:
        t2_crops.append(img5.crop((0, max(0, t2_y_on_p5 - 5), img5.width, img5.height - 100)))
        if z1_page == 6 and 6 in pages:
            img6 = pages[6]
            t2_crops.append(img6.crop((0, 80, img6.width, z1_y - 5)))

    t2_out = crop_pages_vertical(t2_crops)
    t2_out.save(folder / "tekst-2.webp", "WEBP", quality=85)
    print(f"  tekst-2.webp: {t2_out.size} ({len(t2_crops)} fragment)")

def update_meta(ark):
    """Update src per blok MaterialZrodlowy:
    - alt zawiera "Tekst 1" lub "Krzeminsk" lub "Sagan" -> tekst-1.webp
    - alt zawiera "Tekst 2" lub "Szewczyk" -> tekst-2.webp
    - alt zaczyna "Teksty zrodlowe" (po moim ostatnim skrypcie) -> tekst-1.webp DOMYSLNIE
      ale lepiej cofnac do per-zadanie. Sprawdzimy tresc zadania."""
    folder = ark["folder"]

    BLOCK_RE = re.compile(r'<MaterialZrodlowy[^>]*?/>', re.DOTALL)

    changed = 0
    for f in sorted(CONTENT.glob(f"jezyk-polski-{ark['id']}-*.mdx")):
        text = f.read_text(encoding="utf-8")
        # Wczytaj tresc zeby zidentyfikowac ktory tekst zadanie uzywa
        m_tresc = re.search(r'tresc:\s*\|\s*\n((?:  [^\n]*\n)+)', text)
        tresc = m_tresc.group(1) if m_tresc else ""
        tl = tresc.lower()

        needs_t1 = any(k in tl for k in ["tekst 1", "tekst pierwsz", "krzemińs", "krzemins", "agnieszk", "sagan", "carla sag"])
        needs_t2 = any(k in tl for k in ["tekst 2", "tekst drug", "szewczyk", "olafa", "trepczyń", "trepczyn"])
        needs_both = "obu tekst" in tl or "każdego z teks" in tl or "kazdego z teks" in tl or "obydwu tekst" in tl or (needs_t1 and needs_t2)

        new_blocks = []
        # Znajdz wszystkie MaterialZrodlowy
        blocks = BLOCK_RE.findall(text)
        first_text_block = None  # ten z alt zawierającym "Tekst" lub "Teksty"

        # Mapuj kazdy blok na docelowy src (None = usun, str = zmien)
        block_actions = {}
        for blk in blocks:
            alt_m = re.search(r'alt="([^"]+)"', blk)
            if not alt_m:
                block_actions[blk] = blk  # zostaw
                continue
            alt = alt_m.group(1).lower()
            if "teksty źródłowe" in alt or "tekst 1" in alt or "tekst 2" in alt or "krzemiń" in alt or "szewczyk" in alt or "sagan" in alt:
                # To blok teksty zrodlowe - decyduj na bazie polecenia
                if first_text_block is None:
                    first_text_block = blk
                else:
                    # Drugi blok - usuwamy (zachowujemy tylko 1)
                    block_actions[blk] = ""
                    continue
                # Pierwszy text block - ustal src
                if needs_both:
                    # Trzeba pokazac OBA - sklejony plik (sklej-teksty-polski.py utworzyl tekst-zrodlowy.webp jako oba)
                    # Albo zachowaj jako 2 osobne bloki
                    # Zachowamy 1 link wskazujacy na tekst-zrodlowy.webp (oba teksty razem)
                    new_blk = re.sub(r'src="[^"]+"', f'src="/arkusze/jezyk-polski/{folder}/tekst-zrodlowy.webp"', blk, count=1)
                    new_blk = re.sub(r'alt="[^"]+"', 'alt="Teksty źródłowe (Tekst 1 i Tekst 2)"', new_blk, count=1)
                    new_blk = re.sub(r"caption='[^']*'", "caption='Teksty 1 i 2 z arkusza CKE.'", new_blk, count=1)
                    new_blk = re.sub(r'caption="[^"]*"', 'caption="Teksty 1 i 2 z arkusza CKE."', new_blk, count=1)
                    block_actions[blk] = new_blk
                elif needs_t1:
                    new_blk = re.sub(r'src="[^"]+"', f'src="/arkusze/jezyk-polski/{folder}/tekst-1.webp"', blk, count=1)
                    new_blk = re.sub(r'alt="[^"]+"', 'alt="Tekst 1 z arkusza CKE"', new_blk, count=1)
                    new_blk = re.sub(r"caption='[^']*'", "caption='Tekst 1 z arkusza CKE.'", new_blk, count=1)
                    new_blk = re.sub(r'caption="[^"]*"', 'caption="Tekst 1 z arkusza CKE."', new_blk, count=1)
                    block_actions[blk] = new_blk
                elif needs_t2:
                    new_blk = re.sub(r'src="[^"]+"', f'src="/arkusze/jezyk-polski/{folder}/tekst-2.webp"', blk, count=1)
                    new_blk = re.sub(r'alt="[^"]+"', 'alt="Tekst 2 z arkusza CKE"', new_blk, count=1)
                    new_blk = re.sub(r"caption='[^']*'", "caption='Tekst 2 z arkusza CKE.'", new_blk, count=1)
                    new_blk = re.sub(r'caption="[^"]*"', 'caption="Tekst 2 z arkusza CKE."', new_blk, count=1)
                    block_actions[blk] = new_blk
                else:
                    # Zadanie nie odnosi sie do tekstow zrodlowych - usun
                    block_actions[blk] = ""
            else:
                block_actions[blk] = blk  # zostaw bez zmian (np. plakat, zad-NN.webp)

        new_text = text
        for blk, action in block_actions.items():
            if action == "":
                # Usun blok + okoliczne puste linie
                new_text = new_text.replace(blk + "\n\n", "")
                new_text = new_text.replace(blk + "\n", "")
                new_text = new_text.replace(blk, "")
            elif action != blk:
                new_text = new_text.replace(blk, action, 1)

        # Cleanup
        new_text = re.sub(r"\n{3,}", "\n\n", new_text)
        if new_text != text:
            f.write_text(new_text, encoding="utf-8")
            changed += 1
    print(f"  Update meta w {changed} plikach")

def main():
    for ark in ARKUSZE:
        process_arkusz(ark)
        update_meta(ark)

if __name__ == "__main__":
    main()
