"""
Naprawa po błędnej konwersji: pliki angielskiego BEZ pola zrodloImg
(zadania nie-słuchaniowe — bez hasAudio/audioUrl) straciły obraz arkusza.
Odzyskuje <MaterialZrodlowy> z commita 3bb95c8 (przed konwersją) i wstawia
pola zrodloImg* do frontmatter PO linii `subject:` (zawsze obecnej).

Usage: python scripts/recover-zrodloimg.py [--dry]
"""
import re
import subprocess
import sys
from pathlib import Path

ZAD = Path(__file__).parent.parent / "src" / "content" / "zadania"
BASE_COMMIT = "3bb95c8"


def attr(block, name):
    m = re.search(rf'{name}=\{{([^}}]*)\}}', block)
    if m:
        return m.group(1).strip()
    m = re.search(rf'{name}="([^"]*)"', block)
    return m.group(1).strip() if m else None


def yaml_str(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def git_original(relpath):
    try:
        return subprocess.run(
            ["git", "show", f"{BASE_COMMIT}:{relpath}"],
            capture_output=True, text=True, check=True, encoding="utf-8",
        ).stdout
    except subprocess.CalledProcessError:
        return None


def main():
    dry = "--dry" in sys.argv
    fixed = skipped = failed = 0
    for f in sorted(ZAD.glob("jezyk-angielski-*.mdx")):
        text = f.read_text(encoding="utf-8")
        if "zrodloImg:" in text.split("---", 2)[1]:
            skipped += 1
            continue
        rel = f"src/content/zadania/{f.name}"
        orig = git_original(rel)
        if not orig:
            print(f"  [FAIL] {f.name}: brak oryginału w gicie")
            failed += 1
            continue
        mz = re.search(r'<MaterialZrodlowy\b.*?/>', orig, re.DOTALL)
        if not mz:
            print(f"  [FAIL] {f.name}: brak MaterialZrodlowy w oryginale")
            failed += 1
            continue
        block = mz.group(0)
        src = attr(block, "src")
        if not src:
            print(f"  [FAIL] {f.name}: brak src")
            failed += 1
            continue
        alt = attr(block, "alt")
        caption = attr(block, "caption")
        page = attr(block, "pdfPage")

        lines = [f"zrodloImg: {yaml_str(src)}"]
        if alt:
            lines.append(f"zrodloImgAlt: {yaml_str(alt)}")
        if caption:
            lines.append(f"zrodloImgCaption: {yaml_str(caption)}")
        if page and re.fullmatch(r"\d+", page):
            lines.append(f"zrodloPdfPage: {page}")
        add = "\n".join(lines)

        new = re.sub(r'^(subject:.*)$', lambda m: m.group(1) + "\n" + add,
                     text, count=1, flags=re.MULTILINE)
        if new == text:
            print(f"  [FAIL] {f.name}: nie znaleziono linii subject:")
            failed += 1
            continue
        if not dry:
            f.write_text(new, encoding="utf-8")
        print(f"  [ok]   {f.name}: zrodloImg -> {src}")
        fixed += 1

    print(f"\nNaprawione: {fixed}, pominięte(ok): {skipped}, błędy: {failed}")


if __name__ == "__main__":
    main()
