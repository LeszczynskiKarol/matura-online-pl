"""
Globalna zamiana src="...ark-XX.webp" / arkusz-XX.webp / czN-XX.webp -> zad-NN.webp
w meta zadan.

Mapowanie: zadanie nr N w pliku <subj>-<rok>-<sesja>-<poziom>-N.mdx uzywa
zad-NN.webp z folderu ktory referuje meta (src=). Wykrywamy folder z aktualnego src,
zamieniamy nazwe pliku na zad-NN.webp jesli zad-NN.webp ISTNIEJE w tym folderze.

Obslugujemy 2 konwencje folderow:
  - <subj>/<rok>-<sesja>-<poziom>/  (matematyka, chemia, biologia, angielski, polski)
  - <subj>/<rok>/                    (geografia bez poziomu w sciezce)

Plus rozne prefixy plikow: ark-, arkusz-, cz1-, cz2-.
"""
import re
from pathlib import Path

CONTENT = Path(r"D:\matura-online.pl\src\content\zadania")
PUBLIC = Path(r"D:\matura-online.pl\public\arkusze")

def slug_parts(name):
    base = name.replace(".mdx", "").replace(".md", "")
    parts = base.split("-")
    for i in range(len(parts) - 3):
        if re.match(r"^20\d\d$", parts[i]):
            subj = "-".join(parts[:i])
            rok = parts[i]
            sesja = parts[i + 1]
            poziom = parts[i + 2]
            nr_parts = parts[i + 3:]
            nr_str = "-".join(nr_parts)
            try:
                nr = int(nr_str)
            except ValueError:
                return None
            return subj, rok, sesja, poziom, nr
    return None

# Wzorzec wszystkich nazw stron arkuszow ktore mozemy zamienic
PAGE_PATTERN = re.compile(
    r'src="(/arkusze/[^"]+/)(ark|arkusz|cz1|cz2|cz12)-\d+\.webp"'
)
# Nie zamieniaj jesli MaterialZrodlowy ma alt zaczynajacy sie od "Tekst" albo
# komentarz/sekcja wskazuje na zrodlo literackie. Sprawdzamy 200 znakow przed
# dopasowaniem.
TEXT_SOURCE_HINTS = re.compile(r"(Tekst\s+\d|tekst\s+źródłow|źródłowy|literack|Sagan|fragment)")

def main():
    changed = 0
    skipped_no_zad = 0
    for f in CONTENT.glob("*.mdx"):
        info = slug_parts(f.name)
        if info is None:
            continue
        subj, rok, sesja, poziom, nr = info
        zad_filename = f"zad-{nr:02d}.webp"
        text = f.read_text(encoding="utf-8")

        def replacer(m):
            nonlocal skipped_no_zad
            folder_url = m.group(1)  # np. "/arkusze/geografia/2023/"
            # Heurystyka: sprawdz 300 znakow PRZED dopasowaniem czy to MaterialZrodlowy
            # dla tekstu zrodlowego (alt="Tekst...", sekcja "Tekst zrodlowy", "fragment").
            ctx_before = text[max(0, m.start() - 300):m.start()]
            if TEXT_SOURCE_HINTS.search(ctx_before):
                return m.group(0)  # nie zmieniaj — to tekst zrodlowy
            # PUBLIC path z tego URL
            local_folder = PUBLIC / folder_url.replace("/arkusze/", "").rstrip("/")
            zad_path = local_folder / zad_filename
            if not zad_path.exists():
                skipped_no_zad += 1
                return m.group(0)  # bez zmiany
            return f'src="{folder_url}{zad_filename}"'

        new_text = PAGE_PATTERN.sub(replacer, text)
        if new_text != text:
            f.write_text(new_text, encoding="utf-8")
            changed += 1
    print(f"Zmieniono src w {changed} plikach")
    print(f"Pominieto (brak zad-NN.webp): {skipped_no_zad} src")

if __name__ == "__main__":
    main()
