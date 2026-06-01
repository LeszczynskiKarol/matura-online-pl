"""
Dodaje STANDARDOWE intro CKE do zadan:
  - zamkniete-abcd: "Dokoncz zdanie. Wybierz wlasciwa odpowiedz sposrod podanych."
  - zamkniete-pf:   "Ocen prawdziwosc ponizszych stwierdzen. Wybierz P, jesli stwierdzenie jest prawdziwe, albo F - jesli jest falszywe."
  - zamkniete-dobierz: "Uzupelnij zdanie. Wpisz odpowiednie..."

Dziala tylko jesli intro JESZCZE NIE MA w tresc.
"""
import re
from pathlib import Path

CONTENT = Path(r"D:\matura-online.pl\src\content\zadania")

INTROS = {
    "zamkniete-abcd": "Dokończ zdanie. Wybierz właściwą odpowiedź spośród podanych.",
    "zamkniete-pf": "Oceń prawdziwość poniższych stwierdzeń. Wybierz **P**, jeśli stwierdzenie jest prawdziwe, albo **F** — jeśli jest fałszywe.",
}

# Wzorce ktore JUZ wskazuja na intro CKE (zeby nie duplikowac)
ALREADY_HAS_INTRO = re.compile(
    r"(Dokończ\s+zdanie|Wybierz\s+właściwą|Oceń\s+prawdziwość|Uzupełnij\s+(?:zdanie|tabelę))",
    re.IGNORECASE
)

def add_intro_to_block(text, intro):
    """Dodaje intro jako pierwsza linia bloku tresc: |."""
    # Wzor: tresc: |\n<...>\n
    # Wstawiamy "  {intro}\n\n" po "tresc: |\n"
    pattern = re.compile(r"(^tresc:\s*\|\s*\n)((?:  [^\n]*\n?)+)", re.MULTILINE)
    m = pattern.search(text)
    if not m:
        return text, False
    header = m.group(1)
    body = m.group(2)
    if ALREADY_HAS_INTRO.search(body):
        return text, False
    new_block = f"{header}  {intro}\n\n{body}"
    new_text = text[:m.start()] + new_block + text[m.end():]
    return new_text, True

def main():
    changed = 0
    by_typ = {}
    for f in sorted(CONTENT.glob("*.mdx")):
        text = f.read_text(encoding="utf-8")
        typ_m = re.search(r"^typ:\s+(\S+)\s*$", text, re.MULTILINE)
        if not typ_m:
            continue
        typ = typ_m.group(1)
        if typ not in INTROS:
            continue
        new_text, did = add_intro_to_block(text, INTROS[typ])
        if did:
            f.write_text(new_text, encoding="utf-8")
            changed += 1
            by_typ[typ] = by_typ.get(typ, 0) + 1
    print(f"Dodano intro CKE w {changed} plikach")
    for t, c in by_typ.items():
        print(f"  {t}: {c}")

if __name__ == "__main__":
    main()
