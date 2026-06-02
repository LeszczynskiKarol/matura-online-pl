"""
Zamien `<N` / `>N` (cyfra po <) na `&lt;N` / `&gt;N` w MDX poza math mode.
Powod: MDX 2/3 interpretuje `<7` jako otwarcie tagu i wywala build.
"""
import re
import os
from pathlib import Path


def split_outside_dollars(text):
    out = []
    i = 0
    n = len(text)
    while i < n:
        if text[i:i+2] == "$$":
            end = text.find("$$", i + 2)
            if end == -1:
                out.append((False, text[i:]))
                return out
            out.append((True, text[i:end+2]))
            i = end + 2
        elif text[i] == "$" and (i == 0 or text[i-1] != "\\"):
            end = text.find("$", i + 1)
            if end == -1:
                out.append((False, text[i]))
                i += 1
                continue
            inner = text[i+1:end]
            if "\n" in inner or len(inner) > 200:
                out.append((False, text[i]))
                i += 1
                continue
            out.append((True, text[i:end+1]))
            i = end + 1
        else:
            j = i
            while j < n and text[j] != "$":
                j += 1
            out.append((False, text[i:j]))
            i = j
    return out


# `<` poprzedzony bialym znakiem/poczatkiem/`(`/`*` + nastepujaca cyfra/spacja-cyfra
LT_BAD = re.compile(r"(?<=[\s\(\|\*>])<(?=\d|\s*\d|\s)")
GT_BAD = re.compile(r"(?<=[\s\(\|\*])>(?=\d|\s*\d)")
# Tez na poczatku linii
LT_LINESTART = re.compile(r"(?<=^)<(?=\d|\s*\d)", re.MULTILINE)


def fix_segment(s):
    s = LT_BAD.sub("&lt;", s)
    s = GT_BAD.sub("&gt;", s)
    s = LT_LINESTART.sub("&lt;", s)
    return s


def process(text):
    # Split frontmatter
    m = re.match(r"^(---\n.*?\n---\n)(.*)$", text, re.DOTALL)
    if m:
        front = m.group(1)
        body = m.group(2)
    else:
        front = ""
        body = text

    # Body: tylko poza-math; uwaga: NIE ruszaj zawartosci JSX import-line
    parts = split_outside_dollars(body)
    new_body = "".join(s if is_math else fix_segment(s) for is_math, s in parts)

    # Frontmatter (yaml) zostaje surowy - tam < jest legalne
    return front + new_body


def main():
    files = list(Path("D:/matura-online.pl/src/content/zadania").glob("*.mdx"))
    changed = 0
    for f in files:
        text = f.read_text(encoding="utf-8")
        new = process(text)
        if new != text:
            f.write_text(new, encoding="utf-8")
            changed += 1
            print(f"  {f.name}")
    print(f"Zmieniono {changed}/{len(files)} plikow")


if __name__ == "__main__":
    main()
