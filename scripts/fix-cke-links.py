"""
Jednorazowy fix: martwe linki cke.gov.pl/images/... -> piszemy.com.pl S3.
1) Weryfikuje, ze kazdy docelowy plik S3 zwraca 200 (HEAD).
2) Podmienia URL w plikach src/content (dokladne dopasowanie stringa).
Tylko URL-e potwierdzone jako martwe (404) sa w mapie.

Usage:
  python scripts/fix-cke-links.py --check   # tylko weryfikacja S3, bez zmian
  python scripts/fix-cke-links.py           # weryfikacja + podmiana
"""
import sys
import urllib.request
from pathlib import Path

CONTENT = Path(__file__).parent.parent / "src" / "content"
CKE = "https://cke.gov.pl/images/_EGZAMIN_MATURALNY_OD_2023/Arkusze_egzaminacyjne/"
S3 = "https://s3.eu-north-1.amazonaws.com/piszemy.com.pl/arkusze-maturalne/"

# cke_path (po CKE) -> s3 filename (po S3)
MAP = {
    "2023/geografia/MGEP-R0-100-2305-arkusz.pdf": "matura_geografia_rozszerzony_2023_arkusz_pytania_zadania.pdf",
    "2023/geografia/zasady_oceniania/MGEP-R0-100-2305-zasady.pdf": "matura_geografia_rozszerzony_2023_zasady_oceniania_odpowiedzi.pdf",
    "2023/Jezyk_angielski/poziom_rozszerzony/MJAP-R0-100-A-2305-arkusz.pdf": "matura_2023_angielski_rozszerzony_arkusz_pytania_zadania.pdf",
    "2023/matematyka/MMAP-P0-100-2305-arkusz.pdf": "matura_matematyka_podstawowy_arkusz_2023_zadania.pdf",
    "2023/matematyka/MMAP-R0-100-2305-arkusz.pdf": "matura_matematyka_rozszerzony_arkusz_2023_zadania.pdf",
    "2023/matematyka/zasady_oceniania/MMAP-P0-100-2305-zasady.pdf": "matura_matematyka_podstawowy_arkusz_2023_zasady_rozwiazywania_zadan_odpowiedzi.pdf",
    "2023/matematyka/zasady_oceniania/MMAP-R0-100-2305-zasady.pdf": "matura_matematyka_rozszerzony_arkusz_2023_zasady_rozwiazywania_zadan_odpowiedzi.pdf",
    "2023/transkrypcje/MJAP-P0-100-2305-transkrypcja.pdf": "matura_2023_angielski_podstawowy_transkrypcja_nagran.pdf",
    "2023/transkrypcje/MJAP-R0-100-2305-transkrypcja.pdf": "matura_2023_angielski_rozszerzony_transkrypcja_nagran.pdf",
    "2023/zasady_oceniania/MJAP-P0-100-2305-zasady.pdf": "matura_2023_angielski_podstawowy_zasady_oceniania_odpowiedzi.pdf",
    "2023/zasady_oceniania/MJAP-R0-100-2305-zasady.pdf": "matura_2023_angielski_rozszerzony_zasady_oceniania_odpowiedzi.pdf",
    "2024/geografia/MGEP-R0-100-2405-arkusz.pdf": "matura_geografia_rozszerzony_2024_arkusz_pytania_zadania.pdf",
    "2024/geografia/zasady_oceniania/MGEP-R0-100-2405-zasady.pdf": "matura_geografia_rozszerzony_2024_zasady_oceniania_odpowiedzi.pdf",
    "2024/matematyka/MMAP-P0-100-2405.pdf": "matura_matematyka_podstawowy_arkusz_2024_wersja_a.pdf",
    "2024/matematyka/MMAP-P0-100-2405_zasady.pdf": "matura_matematyka_podstawowy_arkusz_2024_zasady_rozwiazywania_zadan_odpowiedzi.pdf",
    "2024/matematyka/MMAR-R0-100-2405.pdf": "matura_matematyka_rozszerzony_arkusz_2024_zadania.pdf",
    "2024/matematyka/MMAR-R0-100-2405_zasady.pdf": "matura_matematyka_rozszerzony_arkusz_2024_zasady_rozwiazywania_zadan_odpowiedzi.pdf",
    "2024/transkrypcje/MJAP-P0-100-2405-transkrypcja.pdf": "matura_2024_angielski_podstawowy_transkrypcja_nagran.pdf",
    "2024/transkrypcje/MJAP-R0-100-2405-transkrypcja.pdf": "matura_2024_angielski_rozszerzony_transkrypcja_nagran.pdf",
    "2024/zasady_oceniania/MBIP-R0-100-2405-zasady.pdf": "matura_biologia_2024_rozszerzony_zasady_oceniania_odpowiedzi.pdf",
    "2024/zasady_oceniania/MJAP-P0-100-2405-zasady.pdf": "matura_2024_angielski_podstawowy_zasady_oceniania_odpowiedzi.pdf",
    "2024/zasady_oceniania/MJAP-R0-100-2405-zasady.pdf": "matura_2024_angielski_rozszerzony_zasady_oceniania_odpowiedzi.pdf",
    "2025/Geografia/MGEP-R0-100-2505-arkusz.pdf": "matura_geografia_rozszerzony_2025_arkusz_pytania_zadania.pdf",
    "2025/matematyka/MMAP-P0-100-2505.pdf": "matura_matematyka_podstawowy_arkusz_2025_wersja_a.pdf",
    "2025/matematyka/MMAP-P0-100-2505_zasady.pdf": "matura_matematyka_podstawowy_arkusz_2025_zasady_rozwiazywania_zadan_odpowiedzi.pdf",
    "2025/matematyka/MMAR-R0-100-2505.pdf": "matura_matematyka_rozszerzony_arkusz_2025_zadania.pdf",
    "2025/matematyka/MMAR-R0-100-2505_zasady.pdf": "matura_matematyka_rozszerzony_arkusz_2025_zasady_rozwiazywania_zadan_odpowiedzi.pdf",
    "2025/transkrypcje/MJAP-R0-100-2505-transkrypcja.pdf": "matura_2025_angielski_rozszerzony_transkrypcja_nagran.pdf",
    "2025/zasady_oceniania/MJAP-P0-100-2505-zasady.pdf": "matura_2025_angielski_podstawowy_zasady_oceniania_odpowiedzi.pdf",
    "2025/zasady_oceniania/MJAP-R0-100-2505-zasady.pdf": "matura_2025_angielski_rozszerzony_zasady_oceniania_odpowiedzi.pdf",
    "2026/jezyk-polski/MPOP-P1-100-2605-arkusz.pdf": "matura_jezyk_polski_podstawowy_arkusz_zadania_cz_1_2026.pdf",
}


def head_ok(url):
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200
    except Exception as e:
        return False


def main():
    check_only = "--check" in sys.argv

    # 1) Weryfikacja S3
    print(">>> Weryfikacja docelowych plikow S3 (HEAD)...")
    bad = []
    pairs = {}
    for cke_path, s3_file in MAP.items():
        s3_url = S3 + s3_file
        ok = head_ok(s3_url)
        print(f"  {'OK  ' if ok else 'FAIL'} {s3_file}")
        if not ok:
            bad.append(s3_file)
        pairs[CKE + cke_path] = s3_url
    if bad:
        print(f"\n[STOP] {len(bad)} docelowych plikow S3 NIE istnieje — przerwij i popraw mape:")
        for b in bad:
            print(f"  - {b}")
        sys.exit(1)
    print(f"\nWszystkie {len(pairs)} celow S3 OK.")
    if check_only:
        return

    # 2) Podmiana w plikach
    print("\n>>> Podmiana URL w src/content ...")
    total = 0
    for f in CONTENT.rglob("*"):
        if f.suffix not in (".md", ".mdx"):
            continue
        text = f.read_text(encoding="utf-8")
        orig = text
        n = 0
        for old, new in pairs.items():
            if old in text:
                c = text.count(old)
                text = text.replace(old, new)
                n += c
        if text != orig:
            f.write_text(text, encoding="utf-8")
            print(f"  {f.relative_to(CONTENT)}: {n} podmian")
            total += n
    print(f"\nRazem podmian: {total}")


if __name__ == "__main__":
    main()
