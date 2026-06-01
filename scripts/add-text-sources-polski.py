"""
Dla kazdego zadania w 4 polskich arkuszach (2023, 2024, 2025, 2026 PP)
dodaje 2 MaterialZrodlowy PRZED istniejacym MaterialZrodlowy dla zadania:
- Tekst 1 (link do webp ze strona 4 arkusza)
- Tekst 2 (link do webp ze strona 5 arkusza)

To linki do skanow arkusza CKE (dokument panstwowy publiczny) - student
widzi co bylo na arkuszu bez koniecznosci otwierania PDF.

Idempotentne: pomija jesli juz istnieje sekcja "Tekst 1" lub "Tekst 2".
"""
import re
from pathlib import Path

CONTENT = Path(r"D:\matura-online.pl\src\content\zadania")

# Mapowanie arkuszy -> (folder, prefix, pdfFile)
ARKUSZE = {
    "2023-maj-pp": {
        "folder": "2023-maj-pp",
        "prefix": "cz1",
        "pdf": "arkusz-1-matura-2023-jezyk-polski-poziom-podstawowy-cz-1-i-2.pdf",
    },
    "2024-maj-pp": {
        "folder": "2024-maj-pp",
        "prefix": "cz12",
        "pdf": "matura_jezyk_polski_podstawowy_arkusz_zadania_cz_1_2_2024.pdf",
    },
    "2025-maj-pp": {
        "folder": "2025-maj-pp",
        "prefix": "cz1",
        "pdf": "jezyk-polski-2025-maj-matura-podstawowa.pdf",
    },
    "2026-maj-pp": {
        "folder": "2026-maj-pp-cz1",
        "prefix": "ark",
        "pdf": "matura_jezyk_polski_podstawowy_arkusz_zadania_cz_1_2026.pdf",
    },
}

S3_BASE = "https://s3.eu-north-1.amazonaws.com/piszemy.com.pl/arkusze-maturalne"

def build_blocks(ark_id: str) -> str:
    info = ARKUSZE[ark_id]
    folder = info["folder"]
    prefix = info["prefix"]
    pdf_url = f"{S3_BASE}/{info['pdf']}"
    return f"""## Teksty źródłowe (arkusz CKE)

<MaterialZrodlowy
  src="/arkusze/jezyk-polski/{folder}/{prefix}-04.webp"
  alt="Tekst 1 - strona 4 arkusza CKE"
  caption='Tekst 1 z arkusza CKE — strona 4 (skan oryginalnego arkusza).'
  zrodlo="CKE — arkusz, strona 4"
  pdfUrl="{pdf_url}"
  pdfPage={{4}}
/>

<MaterialZrodlowy
  src="/arkusze/jezyk-polski/{folder}/{prefix}-05.webp"
  alt="Tekst 2 - strona 5 arkusza CKE"
  caption='Tekst 2 z arkusza CKE — strona 5 (skan oryginalnego arkusza).'
  zrodlo="CKE — arkusz, strona 5"
  pdfUrl="{pdf_url}"
  pdfPage={{5}}
/>

"""

# Wzorzec: znajdz "## Strona arkusza CKE..." LUB "<MaterialZrodlowy" jako pierwszy header
INSERT_BEFORE = re.compile(
    r"(^## [^\n]*(?:[Ss]trona arkusza|[Ss]trony arkusza|[Tt]rescia zadania|[Tt]reścią zadania)[^\n]*\n)",
    re.MULTILINE,
)

def main():
    changed = 0
    for ark_id in ARKUSZE:
        files = sorted(CONTENT.glob(f"jezyk-polski-{ark_id}-*.mdx"))
        for f in files:
            text = f.read_text(encoding="utf-8")
            # Pomijamy jesli juz istnieje sekcja Tekst 1/2 (heurystyka)
            if "## Teksty źródłowe" in text or "Tekst 1 -" in text:
                continue
            blocks = build_blocks(ark_id)
            m = INSERT_BEFORE.search(text)
            if m:
                # Wstaw przed wykrytym headerem
                new_text = text[:m.start()] + blocks + text[m.start():]
            else:
                # Fallback: wstaw po imporcie MaterialZrodlowy
                imp_re = re.compile(r"^(import MaterialZrodlowy[^\n]*\n)", re.MULTILINE)
                im = imp_re.search(text)
                if im:
                    new_text = text[:im.end()] + "\n" + blocks + text[im.end():]
                else:
                    print(f"  [SKIP] {f.name}: brak miejsca do wstawienia")
                    continue
            f.write_text(new_text, encoding="utf-8")
            changed += 1
    print(f"\nDodano teksty zrodlowe w {changed} plikach")

if __name__ == "__main__":
    main()
