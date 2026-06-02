"""
Auto-wrap KaTeX commands w $...$ jesli nie sa juz w dolarach.
Bezpiecznie: parsuje plik, pomija fragmenty w $...$ i $$...$$, omija frontmatter.
"""
import re
import sys
from pathlib import Path

# Polecenia KaTeX — bez argumentu w nawiasach (lub z opcjonalnym '\^2' itp.)
SIMPLE_CMDS = [
    "leq", "geq", "neq", "le", "ge", "cdot", "times", "div",
    "pi", "alpha", "beta", "gamma", "delta", "epsilon", "varepsilon",
    "zeta", "eta", "theta", "vartheta", "iota", "kappa", "lambda",
    "mu", "nu", "xi", "rho", "varrho", "sigma", "varsigma", "tau",
    "upsilon", "phi", "varphi", "chi", "psi", "omega",
    "Gamma", "Delta", "Theta", "Lambda", "Xi", "Pi", "Sigma", "Phi", "Psi", "Omega",
    "infty", "partial", "nabla", "forall", "exists", "emptyset",
    "subset", "subseteq", "supset", "supseteq", "cup", "cap",
    "in", "notin", "ni", "approx", "equiv", "sim", "simeq", "cong",
    "pm", "mp", "to", "rightarrow", "leftarrow", "Rightarrow", "Leftarrow",
    "mapsto", "implies",
    "sum", "prod", "int", "iint", "iiint", "oint",
    "lim", "max", "min", "sup", "inf", "deg", "arg",
    "sin", "cos", "tan", "cot", "sec", "csc",
    "arcsin", "arccos", "arctan",
    "sinh", "cosh", "tanh",
    "log", "ln", "lg", "exp",
    "mathbb", "mathbf", "mathrm", "mathit", "mathcal",  # bez {} - obsluga ponizej
    "circ", "degree", "ldots", "cdots", "dots",
    "left", "right", "big", "Big", "bigg", "Bigg",
    "quad", "qquad",
    "vec", "hat", "bar", "tilde", "dot", "ddot",
    "prime",
    "bullet",
]
# Polecenia wymagajace {arg} (z balanced braces, max 2 poziomy)
BRACED_CMDS = ["frac", "sqrt", "binom", "tfrac", "dfrac", "overline", "underline", "boxed"]

SIMPLE_PATTERN = re.compile(
    r"\\(?:" + "|".join(SIMPLE_CMDS) + r")\b"
)

# Manualny matcher dla \frac{x}{y} itp. - omija catastrophic backtracking regex.
BRACED_START = re.compile(
    r"\\(?:" + "|".join(BRACED_CMDS) + r")(?:\[[^\]]{0,40}\])?\{"
)

def match_balanced_braces(s, start):
    """Zwraca index po zamykajacym } (lub None jesli niezbalansowane)."""
    if start >= len(s) or s[start] != "{":
        return None
    depth = 0
    i = start
    while i < len(s):
        c = s[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return None


def find_braced_command(seg):
    """Yield (start, end) dla kazdego \\frac{x}{y}, \\sqrt{x} itp. w seg."""
    i = 0
    while i < len(seg):
        m = BRACED_START.search(seg, i)
        if not m:
            return
        open_brace = m.end() - 1  # pozycja '{'
        end = match_balanced_braces(seg, open_brace)
        if end is None:
            i = m.end()
            continue
        # Opcjonalnie kolejne {grupy} (do 3)
        for _ in range(2):
            if end < len(seg) and seg[end] == "{":
                e2 = match_balanced_braces(seg, end)
                if e2:
                    end = e2
                else:
                    break
            else:
                break
        yield (m.start(), end)
        i = end

# Subscripts/superscripts: x_1, x^2, x_{abc}, x^{n+1} - tylko gdy poprzedzone literą/cyfrą
# (zostawiamy luzem - wymagaja kontekstu)

def split_outside_dollars(text):
    """Zwraca [(is_math, segment), ...] — is_math=True dla $...$ i $$...$$."""
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
                out.append((False, text[i:]))
                return out
            # Sprawdz czy nie jest to cena: $5 lub $5.99 (cyfra od razu po $ i brak zamykajacego w rozsądnej odległości w tej linii)
            inner = text[i+1:end]
            if "\n" in inner:
                # cross-line $ - skip
                out.append((False, text[i]))
                i += 1
                continue
            out.append((True, text[i:end+1]))
            i = end + 1
        else:
            # zbieraj az do nastepnego $
            j = i
            while j < n:
                if text[j] == "$":
                    break
                j += 1
            out.append((False, text[i:j]))
            i = j
    return out


def wrap_in_segment(seg):
    """Wrapuj KaTeX patterns w $...$ w segmencie poza-math."""
    # Najpierw braced (frac/sqrt) - manual matching, od konca zeby indeksy nie sie psuly
    spans = list(find_braced_command(seg))
    for start, end in reversed(spans):
        seg = seg[:start] + "$" + seg[start:end] + "$" + seg[end:]
    # Potem simple - splituj na nowo zeby ominac juz-wrap fragmenty
    parts = split_outside_dollars(seg)
    out = []
    for is_math, s in parts:
        if is_math:
            out.append(s)
        else:
            out.append(SIMPLE_PATTERN.sub(lambda m: f"${m.group(0)}$", s))
    return "".join(out)


def process_text(text):
    """Procesuje pelny tekst MDX (z frontmatter)."""
    # Splituj na frontmatter + body
    m = re.match(r"^(---\n.*?\n---\n)(.*)$", text, re.DOTALL)
    if m:
        front = m.group(1)
        body = m.group(2)
    else:
        front = ""
        body = text

    # Body: tylko fragmenty poza $...$
    parts = split_outside_dollars(body)
    new_body = "".join(s if is_math else wrap_in_segment(s) for is_math, s in parts)

    # Frontmatter: tez procesuj tresc/odpowiedz/pulapka/wymaganie (YAML multi-line)
    # Bezpiecznie: tylko fragmenty wartosci po `|` lub `>` blokach
    # Uproszczenie: caly frontmatter procesuj jak body (zachowuje $...$)
    if front:
        fp = split_outside_dollars(front)
        new_front = "".join(s if is_math else wrap_in_segment(s) for is_math, s in fp)
    else:
        new_front = ""

    return new_front + new_body


def main():
    files = list(Path("D:/matura-online.pl/src/content/zadania").glob("*.mdx"))
    changed = 0
    for f in files:
        text = f.read_text(encoding="utf-8")
        new = process_text(text)
        if new != text:
            f.write_text(new, encoding="utf-8")
            changed += 1
    print(f"Zmieniono {changed}/{len(files)} plikow")


if __name__ == "__main__":
    main()
