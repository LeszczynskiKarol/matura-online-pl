"""
Dodaje audioUrl: do meta zadan angielskich (-1, -2, -3) dla wszystkich
arkuszy ktorych pociac sie udalo (boundaries.json wpis kompletny).

Insertion point: pod linia 'hasAudio: true' w frontmatter YAML.
Idempotentne - jesli juz jest audioUrl, pomija.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
BOUNDARIES = ROOT / "boundaries.json"
ZADANIA_DIR = Path(r"D:\matura-online.pl\src\content\zadania")
BASE_URL = "https://www.matura-online.pl/audio/jezyk-angielski"

def main():
    with open(BOUNDARIES, encoding="utf-8") as f:
        bnd = json.load(f)

    touched = 0
    for key, b in bnd.items():
        if not all(b.get(k) is not None for k in ("z1", "z2", "z3")):
            print(f"[SKIP] {key}: niekompletne granice")
            continue
        for nr in (1, 2, 3):
            meta_file = ZADANIA_DIR / f"jezyk-angielski-{key}-{nr}.mdx"
            if not meta_file.exists():
                print(f"[SKIP] {meta_file.name}: nie ma pliku")
                continue
            text = meta_file.read_text(encoding="utf-8")
            url = f"{BASE_URL}/{key}-{nr}.mp3"

            if "audioUrl:" in text.split("---", 2)[1]:
                # juz jest - zaktualizuj wartosc
                new_text = re.sub(
                    r'^audioUrl:.*$',
                    f'audioUrl: {url}',
                    text,
                    count=1,
                    flags=re.MULTILINE,
                )
            elif "hasAudio: true" in text:
                new_text = text.replace(
                    "hasAudio: true",
                    f"hasAudio: true\naudioUrl: {url}",
                    1,
                )
            else:
                print(f"[WARN] {meta_file.name}: brak hasAudio:true, pomijam")
                continue

            if new_text != text:
                meta_file.write_text(new_text, encoding="utf-8")
                print(f"  OK {meta_file.name}: audioUrl -> {url}")
                touched += 1
            else:
                print(f"  -- {meta_file.name}: bez zmian")

    print(f"\nZmieniono: {touched} plikow")

if __name__ == "__main__":
    main()
