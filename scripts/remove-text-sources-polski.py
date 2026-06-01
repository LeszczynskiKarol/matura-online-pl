"""Cofa masowo dodane sekcje '## Teksty zrodlowe' w polskich zadaniach."""
import re
from pathlib import Path

CONTENT = Path(r"D:\matura-online.pl\src\content\zadania")

# Wzorzec: sekcja "## Teksty zrodlowe" + 2 MaterialZrodlowy
SECTION_RE = re.compile(
    r"## Teksty źródłowe \(arkusz CKE\)\s*\n\n"
    r"<MaterialZrodlowy[^>]*?/>\s*\n\n"
    r"<MaterialZrodlowy[^>]*?/>\s*\n+",
    re.DOTALL,
)

def main():
    changed = 0
    for f in CONTENT.glob("jezyk-polski-*.mdx"):
        text = f.read_text(encoding="utf-8")
        new_text = SECTION_RE.sub("", text)
        if new_text != text:
            f.write_text(new_text, encoding="utf-8")
            changed += 1
    print(f"Usunieto masowe sekcje w {changed} plikach")

if __name__ == "__main__":
    main()
