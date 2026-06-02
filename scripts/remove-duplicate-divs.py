"""
Usun <div class="odpowiedz">...</div> i <div class="pulapka">...</div> z body MDX
- te beda teraz renderowane przez page z pol frontmatter.
Balanced div matching: depth counter.
"""
import re
from pathlib import Path


def remove_balanced_div(text, class_name):
    """Usun wszystkie <div class="X">...</div> z balanced depth."""
    pat_open = re.compile(rf'<div\s+class="{re.escape(class_name)}"[^>]*>')
    out = []
    cursor = 0
    while cursor < len(text):
        m = pat_open.search(text, cursor)
        if not m:
            out.append(text[cursor:])
            break
        out.append(text[cursor:m.start()])
        # Znajdz balanced </div>
        depth = 1
        i = m.end()
        n = len(text)
        while i < n and depth > 0:
            o = text.find("<div", i)
            c = text.find("</div>", i)
            if c == -1:
                break
            if o != -1 and o < c:
                depth += 1
                i = o + 4
            else:
                depth -= 1
                i = c + 6
        # i wskazuje pozycje po </div>
        cursor = i
        # Pomin trailing newline(s)
        while cursor < n and text[cursor] == "\n":
            cursor += 1
    return "".join(out)


def process(text):
    # Tylko body (po frontmatter)
    m = re.match(r"^(---\n.*?\n---\n)(.*)$", text, re.DOTALL)
    if not m:
        return text
    front, body = m.group(1), m.group(2)
    new_body = remove_balanced_div(body, "odpowiedz")
    new_body = remove_balanced_div(new_body, "pulapka")
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
    print(f"Zmieniono {changed}/{len(files)} plikow")


if __name__ == "__main__":
    main()
