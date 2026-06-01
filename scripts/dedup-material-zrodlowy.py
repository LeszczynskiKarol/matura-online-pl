"""
Usuwa duplikaty <MaterialZrodlowy ... src="X" /> w plikach mdx — zachowuje
tylko pierwsze wystapienie kazdego unikalnego src.
"""
import re
from pathlib import Path

CONTENT = Path(r"D:\matura-online.pl\src\content\zadania")

# Pattern dla pelnego komponentu <MaterialZrodlowy ... /> (multilinijkowy, samozamykajacy)
COMP_RE = re.compile(
    r'<MaterialZrodlowy\b[^>]*?/>',
    re.DOTALL
)
SRC_RE = re.compile(r'src="([^"]+)"')

def main():
    changed = 0
    for f in sorted(CONTENT.glob("*.mdx")):
        text = f.read_text(encoding="utf-8")
        matches = list(COMP_RE.finditer(text))
        if len(matches) < 2:
            continue
        seen_srcs = set()
        to_remove = []  # spans (start, end) of duplicates
        for m in matches:
            src_m = SRC_RE.search(m.group(0))
            if not src_m:
                continue
            src = src_m.group(1)
            if src in seen_srcs:
                to_remove.append((m.start(), m.end()))
            else:
                seen_srcs.add(src)
        if not to_remove:
            continue
        # Usun w odwrotnej kolejnosci (zeby offsety zostaly zachowane)
        new_text = text
        for start, end in reversed(to_remove):
            # Usun rowniez puste linie wokol
            before = new_text[:start].rstrip("\n ") + "\n"
            after_chunk = new_text[end:].lstrip("\n ")
            new_text = before + "\n" + after_chunk
        # Cleanup wielu pustych linii z rzedu
        new_text = re.sub(r"\n{3,}", "\n\n", new_text)
        f.write_text(new_text, encoding="utf-8")
        changed += 1
        print(f"  OK {f.name}: usunieto {len(to_remove)} duplikat(ow)")
    print(f"\nUsunieto duplikaty MaterialZrodlowy w {changed} plikach")

if __name__ == "__main__":
    main()
