"""
Globalna zamiana linkow CKE -> S3 piszemy.com.pl w meta zadan i arkuszy.

Mapowanie zbudowane z faktycznych URLi w D:/matury-online.pl/frontend/src/data/arkusze.ts.
Klucz: (subject, rok, poziom) -> S3 URL.
"""
import re
from pathlib import Path

S3_BASE = "https://s3.eu-north-1.amazonaws.com/piszemy.com.pl/arkusze-maturalne"

# (subject_slug, rok, poziom) -> filename na S3
MAP = {
    ("matematyka", 2023, "pp"): "matura_matematyka_podstawowy_arkusz_2023_zadania.pdf",
    ("matematyka", 2023, "pr"): "matura_matematyka_rozszerzony_arkusz_2023_zadania.pdf",
    ("matematyka", 2024, "pp"): "matura_matematyka_podstawowy_arkusz_2024_wersja_a.pdf",
    ("matematyka", 2024, "pr"): "matura_matematyka_rozszerzony_arkusz_2024_zadania.pdf",
    ("matematyka", 2025, "pp"): "matura_matematyka_podstawowy_arkusz_2025_wersja_a.pdf",
    ("matematyka", 2025, "pr"): "matura_matematyka_rozszerzony_arkusz_2025_zadania.pdf",
    ("matematyka", 2026, "pp"): "matura_matematyka_arkusz_2026_wersja_a.pdf",

    ("chemia", 2023, "pr"): "matura_chemia_2023_rozszerzony_arkusz_zadania_pytania.pdf",
    ("chemia", 2024, "pr"): "matura_chemia_2024_rozszerzony_arkusz_zadania_pytania.pdf",
    ("chemia", 2025, "pr"): "matura_chemia_2025_rozszerzony_arkusz_zadania_pytania.pdf",

    ("biologia", 2023, "pr"): "matura_biologia_2023_rozszerzony_arkusz_pytania_zadania.pdf",
    ("biologia", 2024, "pr"): "matura_biologia_2024_rozszerzony_arkusz_pytania_zadania.pdf",
    ("biologia", 2025, "pr"): "matura_biologia_2025_rozszerzony_arkusz_pytania_zadania.pdf",

    ("jezyk-angielski", 2023, "pp"): "matura_2023_angielski_podstawowy_arkusz_pytania_zadania.pdf",
    ("jezyk-angielski", 2023, "pr"): "matura_2023_angielski_rozszerzony_arkusz_pytania_zadania.pdf",
    ("jezyk-angielski", 2024, "pp"): "matura_2024_angielski_podstawowy_arkusz_wersja_a_pytania_zadania.pdf",
    ("jezyk-angielski", 2024, "pr"): "matura_2024_angielski_rozszerzony_arkusz_wersja_a_pytania_zadania.pdf",
    ("jezyk-angielski", 2025, "pp"): "matura_2025_angielski_podstawowy_arkusz_wersja_a_pytania_zadania.pdf",
    ("jezyk-angielski", 2025, "pr"): "matura_2025_angielski_rozszerzony_arkusz_wersja_a_pytania_zadania.pdf",
    ("jezyk-angielski", 2026, "pp"): "matura_2026_angielski_podstawowy_arkusz_pytania_zadania.pdf",

    ("geografia", 2023, "pr"): "matura_geografia_rozszerzony_2023_arkusz_pytania_zadania.pdf",
    ("geografia", 2024, "pr"): "matura_geografia_rozszerzony_2024_arkusz_pytania_zadania.pdf",
    ("geografia", 2025, "pr"): "matura_geografia_rozszerzony_2025_arkusz_pytania_zadania.pdf",

    ("jezyk-polski", 2023, "pp"): "arkusz-1-matura-2023-jezyk-polski-poziom-podstawowy-cz-1-i-2.pdf",
    ("jezyk-polski", 2023, "pr"): "arkusz-matura-2023-jezyk-polski-poziom-rozszerzony.pdf",
    ("jezyk-polski", 2024, "pp"): "matura_jezyk_polski_podstawowy_arkusz_zadania_cz_1_2_2024.pdf",
    # polski 2024 PR jest na innym buckecie (maturapolski.s3) — pomijamy mapę, link CKE zostanie
    ("jezyk-polski", 2025, "pp"): "jezyk-polski-2025-maj-matura-podstawowa.pdf",
    ("jezyk-polski", 2025, "pr"): "jezyk-polski-2025-maj-matura-rozszerzona-pytania-testy-zadania.pdf",
    ("jezyk-polski", 2026, "pp"): "matura_jezyk_polski_podstawowy_arkusz_zadania_cz_1_2026.pdf",
}

CONTENT_ROOT = Path(r"D:\matura-online.pl\src\content")

def slug_from_filename(name):
    # np. matematyka-2023-maj-pp-1.mdx -> (matematyka, 2023, maj, pp, 1)
    # ale slug może też być chemia-2024-maj-pr.md (arkusz, bez nr)
    base = name.replace(".mdx", "").replace(".md", "")
    parts = base.split("-")
    # subject może być multi-word: "jezyk-angielski"
    # struktura: <subj>-<rok>-<sesja>-<poziom>[-nr]
    # rozpoznajemy ostatnie 3-4 segmenty
    # Próba: parts[-4..-1] = [rok, sesja, poziom, nr], parts[0..-4] = subject
    if len(parts) >= 4:
        try:
            # Sprawdź czy parts[-4] to rok (4-cyfrowy)
            for i in range(len(parts) - 3):
                rok_candidate = parts[i]
                if re.match(r"^20\d\d$", rok_candidate):
                    subj = "-".join(parts[:i])
                    rok = int(parts[i])
                    sesja = parts[i + 1]
                    poziom = parts[i + 2]
                    nr = parts[i + 3] if i + 3 < len(parts) else None
                    return subj, rok, sesja, poziom, nr
        except (ValueError, IndexError):
            pass
    return None

def main():
    changed = 0
    skipped = 0
    for f in (CONTENT_ROOT / "zadania").glob("*.mdx"):
        info = slug_from_filename(f.name)
        if info is None:
            continue
        subj, rok, sesja, poziom, nr = info
        if (subj, rok, poziom) not in MAP:
            continue
        s3_url = f"{S3_BASE}/{MAP[(subj, rok, poziom)]}"
        text = f.read_text(encoding="utf-8")
        new_text = re.sub(
            r'pdfUrl="https://cke\.gov\.pl/[^"]+"',
            f'pdfUrl="{s3_url}"',
            text,
        )
        if new_text != text:
            f.write_text(new_text, encoding="utf-8")
            changed += 1

    # Także arkusze (.md): pdfArkuszUrl
    for f in (CONTENT_ROOT / "arkusze").glob("*.md"):
        info = slug_from_filename(f.name)
        if info is None:
            continue
        subj, rok, sesja, poziom, _ = info
        if (subj, rok, poziom) not in MAP:
            continue
        s3_url = f"{S3_BASE}/{MAP[(subj, rok, poziom)]}"
        text = f.read_text(encoding="utf-8")
        # pdfArkuszUrl: https://cke...
        new_text = re.sub(
            r'(pdfArkuszUrl:\s+)https://cke\.gov\.pl/[^\s]+',
            rf'\1{s3_url}',
            text,
        )
        if new_text != text:
            f.write_text(new_text, encoding="utf-8")
            changed += 1
    print(f"Zmieniono: {changed} plikow")

if __name__ == "__main__":
    main()
