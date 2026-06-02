"""
W tresc/odpowiedz frontmatter: wstrzyknij pusta linie przed kazdym **N.M.** /
**N.M** markerem podpunktu, by markdown renderowal go jako osobny paragraf.
"""
import re
from pathlib import Path

SUB_RE = re.compile(r"\*\*(\d+\.\d+)\.?\*\*")


def fix_yaml_block(value: str, indent: str = "  ") -> str:
    lines = value.split("\n")
    out = []
    for ln in lines:
        stripped = ln[len(indent):] if ln.startswith(indent) else ln
        matches = list(SUB_RE.finditer(stripped))
        if len(matches) < 2:
            # 0 albo 1 marker - rozdziel od poprzedniej linii pusta jesli marker na poczatku
            if matches and matches[0].start() == 0 and out and out[-1].strip() != "":
                out.append("")
            out.append(ln)
            continue
        # >= 2 markery w jednej linii - rozbij
        # Prefix przed pierwszym markerem
        prefix = stripped[:matches[0].start()].rstrip()
        if prefix:
            if out and out[-1].strip() != "":
                out.append("")  # opcjonalnie pusta przed prefixem? Nie, zostaw kontekst.
            out.append(indent + prefix)
        # Kazdy marker jako osobny paragraf
        for i, m in enumerate(matches):
            seg_start = m.start()
            seg_end = matches[i+1].start() if i+1 < len(matches) else len(stripped)
            chunk = stripped[seg_start:seg_end].strip()
            if out and out[-1].strip() != "":
                out.append("")
            out.append(indent + chunk)
    return "\n".join(out)


def process(text):
    m = re.match(r"^(---\n)(.*?)(\n---\n)(.*)$", text, re.DOTALL)
    if not m:
        return text
    fm_open, fm, fm_close, body = m.groups()

    def fix_field(field_name, fm_text):
        pat = re.compile(
            rf"^({field_name}:\s*\|[^\n]*\n)((?:  .*(?:\n|$))+)",
            re.MULTILINE,
        )
        def repl(mm):
            return mm.group(1) + fix_yaml_block(mm.group(2).rstrip("\n")) + "\n"
        return pat.sub(repl, fm_text)

    new_fm = fm
    for fld in ["tresc", "odpowiedz", "pulapka"]:
        new_fm = fix_field(fld, new_fm)

    return fm_open + new_fm + fm_close + body


def main():
    files = list(Path("D:/matura-online.pl/src/content/zadania").glob("*.mdx"))
    changed = 0
    for f in files:
        text = f.read_text(encoding="utf-8")
        new = process(text)
        if new != text:
            f.write_text(new, encoding="utf-8")
            changed += 1
    print(f"Zmieniono {changed}/{len(files)} plikow")


if __name__ == "__main__":
    main()
