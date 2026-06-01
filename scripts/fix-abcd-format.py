"""
Auto-fix zadan ABCD: konwertuje jednolinijkowe odpowiedzi na multi-line + bold.

Wzorzec do wykrycia w meta tresc (w dowolnym formacie YAML - "...", |, >):
  "...: A. X, B. Y, C. Z, D. W."
albo
  "... A. X B. Y C. Z D. W"

Replace na:
  ... [intro]

  **A.** X     **B.** Y     **C.** Z     **D.** W

Implementacja line-based: jesli linia konczy sie wzorcem ABCD, rozdziela ja.
"""
import re
from pathlib import Path

CONTENT = Path(r"D:\matura-online.pl\src\content\zadania")

# Wzorzec ABCD w jednej linii: szukamy "A." "B." "C." "D." z separatorami
ABCD_INLINE = re.compile(
    r'(?P<intro>.*?)'                       # cokolwiek przed
    r'(?:^|\s|[:;,])\s*A[\.\)]\s*(?P<a>.+?)' # A. X
    r'[,;\s]+B[\.\)]\s*(?P<b>.+?)'          # B. Y
    r'[,;\s]+C[\.\)]\s*(?P<c>.+?)'          # C. Z
    r'[,;\s]+D[\.\)]\s*(?P<d>.+?)\s*\.?$'   # D. W [.]
)

def is_yaml_block_scalar_line(line):
    """Wewnatrz YAML block scalar | linie maja indent (2 spacje)."""
    return line.startswith("  ") and not line.startswith("    ")

def reformat_meta_tresc(text):
    """Znajdz blok tresc: i przebuduj go jesli zawiera ABCD."""
    lines = text.split("\n")
    out = []
    i = 0
    changed = False
    while i < len(lines):
        line = lines[i]
        # Wykryj poczatek tresc:
        if line.startswith("tresc:"):
            # Mode 1: tresc: "..."
            m = re.match(r'^tresc:\s*"(.+)"\s*$', line)
            if m:
                inner = m.group(1)
                am = ABCD_INLINE.match(inner)
                if am:
                    a_start = am.start('a')
                    cut = inner[:a_start]
                    cut = re.sub(r'\s*[:;,]?\s*A[\.\)]\s*$', '', cut)
                    intro = cut.rstrip(":. \t").rstrip()
                    # YAML double-quote escapes (\\\\ -> \\, \\$ -> $)
                    intro = intro.replace('\\\\', '\\').replace('\\"', '"')
                    a = am.group('a').strip().replace('\\\\', '\\')
                    b = am.group('b').strip().replace('\\\\', '\\')
                    c = am.group('c').strip().replace('\\\\', '\\')
                    d = am.group('d').strip().replace('\\\\', '\\')
                    out.append("tresc: |")
                    out.append(f"  {intro}")
                    out.append("")
                    out.append(f"  **A.** {a}     **B.** {b}     **C.** {c}     **D.** {d}")
                    i += 1
                    changed = True
                    continue
            # Mode 2: tresc: |  + content lines
            if re.match(r'^tresc:\s*\|\s*$', line):
                # Zbierz indent-block linijki
                out.append(line)
                i += 1
                block_lines = []
                while i < len(lines) and (lines[i].startswith("  ") or lines[i] == ""):
                    # block scalar konczy sie gdy linia nie jest indented lub jest pusta+nastepna nie-indent
                    if lines[i] == "":
                        # peek dalej - jesli kolejna jest pusta lub nie-indent, koniec bloku
                        if i + 1 >= len(lines) or not lines[i + 1].startswith("  "):
                            break
                        block_lines.append(lines[i])
                        i += 1
                    else:
                        block_lines.append(lines[i])
                        i += 1
                # Sprobuj znalezc linie z ABCD w block_lines
                # Joinujemy wszystkie linie tresc do jednej i probujemy match
                content = "\n".join(l[2:] if l.startswith("  ") else l for l in block_lines)
                # Lokalizuj ABCD na konstrukcji content (moze być na jednej linii)
                am = ABCD_INLINE.search(content)
                if am and am.group('a').strip() and not content.count("**A.**"):
                    # WAZNE: pozycja PRZED grupą 'a' (po "A.") — bo intro w regex
                    # to non-greedy .* od 0, am.start() = 0
                    a_start = am.start('a')
                    # Cofamy do przed "A." (lookbehind 4-6 znaków)
                    cut = content[:a_start]
                    # Usun ostatnie "A." lub "A)" + separator
                    cut = re.sub(r'\s*[:;,]?\s*A[\.\)]\s*$', '', cut)
                    intro = cut.rstrip(":. \t").rstrip()
                    a = am.group('a').strip()
                    b = am.group('b').strip()
                    c = am.group('c').strip()
                    d = am.group('d').strip()
                    # Wpisz przeformatowane linie
                    for il in intro.split("\n"):
                        out.append(f"  {il}" if il else "")
                    out.append("")
                    out.append(f"  **A.** {a}     **B.** {b}     **C.** {c}     **D.** {d}")
                    changed = True
                    continue
                else:
                    # Bez zmian - kopiuj block_lines
                    out.extend(block_lines)
                    continue
        out.append(line)
        i += 1
    return "\n".join(out), changed

def main():
    changed = 0
    for f in sorted(CONTENT.glob("*.mdx")):
        text = f.read_text(encoding="utf-8")
        if "typ: zamkniete-abcd" not in text:
            continue
        new_text, did = reformat_meta_tresc(text)
        if did:
            f.write_text(new_text, encoding="utf-8")
            changed += 1
            print(f"  OK {f.name}")
    print(f"\nZmieniono format ABCD w {changed} plikach")

if __name__ == "__main__":
    main()
