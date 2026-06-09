"""
Konwersja plików zadań angielskiego do czystego układu:
  - <MaterialZrodlowy> z treści -> pola frontmatter (zrodloImg/Alt/Caption/PdfPage),
    bo szablon renderuje obraz TUŻ POD linią "Źródło", NAD odpowiedziami.
  - usuwa zepsuty 2. <AudioPlayer> (pełny mp3 arkusza, nieobecny na S3) + "## Nagranie",
  - usuwa pusty nagłówek "## Klucz odpowiedzi...",
  - usuwa "## Strona arkusza CKE..." (obraz idzie teraz przez szablon),
  - usuwa osierocone importy MaterialZrodlowy / AudioPlayer.

Idempotentne: jeśli frontmatter ma już zrodloImg, plik pomijany.
Usage: python scripts/fix-angielski-layout.py [--dry]
"""
import re
import sys
from pathlib import Path

ZAD = Path(__file__).parent.parent / "src" / "content" / "zadania"


def attr(block, name):
    # name="..." lub name={123}
    m = re.search(rf'{name}=\{{([^}}]*)\}}', block)
    if m:
        return m.group(1).strip()
    m = re.search(rf'{name}="([^"]*)"', block)
    return m.group(1).strip() if m else None


def yaml_str(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def convert(text):
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, "brak frontmatter"
    fm = parts[1]
    body = parts[2]

    if "zrodloImg:" in fm:
        return None, "już skonwertowany"

    mz = re.search(r'<MaterialZrodlowy\b.*?/>', body, re.DOTALL)
    if not mz:
        return None, "brak MaterialZrodlowy"
    block = mz.group(0)
    src = attr(block, "src")
    alt = attr(block, "alt")
    caption = attr(block, "caption")
    page = attr(block, "pdfPage")
    if not src:
        return None, "brak src w MaterialZrodlowy"

    # 1) frontmatter: wstaw pola po linii audioUrl: (albo po hasAudio:)
    add = [f"zrodloImg: {yaml_str(src)}"]
    if alt:
        add.append(f"zrodloImgAlt: {yaml_str(alt)}")
    if caption:
        add.append(f"zrodloImgCaption: {yaml_str(caption)}")
    if page and re.fullmatch(r"\d+", page):
        add.append(f"zrodloPdfPage: {page}")
    add_block = "\n".join(add)

    if re.search(r'^audioUrl:.*$', fm, re.MULTILINE):
        fm = re.sub(r'^(audioUrl:.*)$', r'\1\n' + add_block.replace('\\', r'\\'),
                    fm, count=1, flags=re.MULTILINE)
    else:
        fm = re.sub(r'^(hasAudio:.*)$', r'\1\n' + add_block.replace('\\', r'\\'),
                    fm, count=1, flags=re.MULTILINE)

    # 2) body: usuń bloki i nagłówki
    body = re.sub(r'<MaterialZrodlowy\b.*?/>\s*', '', body, flags=re.DOTALL)
    body = re.sub(r'<AudioPlayer\b.*?/>\s*', '', body, flags=re.DOTALL)
    body = re.sub(r'^\s*import\s+MaterialZrodlowy.*$\n?', '', body, flags=re.MULTILINE)
    body = re.sub(r'^\s*import\s+AudioPlayer.*$\n?', '', body, flags=re.MULTILINE)
    body = re.sub(r'^##\s*Strona arkusza CKE.*$\n?', '', body, flags=re.MULTILINE)
    body = re.sub(r'^##\s*Nagranie\s*$\n?', '', body, flags=re.MULTILINE)
    body = re.sub(r'^##\s*Klucz odpowiedzi.*$\n?', '', body, flags=re.MULTILINE)
    # collapse 3+ puste linie do 1 pustej
    body = re.sub(r'\n{3,}', '\n\n', body)
    body = body.lstrip('\n')

    return f"---{fm}---\n\n{body}", None


def main():
    dry = "--dry" in sys.argv
    changed = skipped = 0
    for f in sorted(ZAD.glob("jezyk-angielski-*.mdx")):
        text = f.read_text(encoding="utf-8")
        new, reason = convert(text)
        if new is None:
            print(f"  [skip] {f.name}: {reason}")
            skipped += 1
            continue
        if not dry:
            f.write_text(new, encoding="utf-8")
        print(f"  [ok]   {f.name}")
        changed += 1
    print(f"\nZmienione: {changed}, pominięte: {skipped}")


if __name__ == "__main__":
    main()
