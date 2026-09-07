# -*- coding: utf-8 -*-
"""PDF arkusza CKE -> strony ark-NN.webp w public/arkusze/<przedmiot>/<arkusz>/.

Brakujące ogniwo pipeline'u: crop-arkusz.py oczekuje gotowych stron webp,
a te powstawały dotąd poza repozytorium. Bez tego kroku nie da się odtworzyć
łańcucha PDF -> strony -> wycinki per zadanie.

Rozdzielczość dobrana tak, żeby wyjść na ~1447x2047 px, czyli tyle, ile mają
istniejące strony (A4 przy ok. 175 DPI). Zmiana tej wartości rozjedzie
wykrywanie pasków nagłówków w crop-arkusz.py, które operuje na progach w px.

Użycie:
  python scripts/pdf-to-webp.py <plik.pdf> <katalog-docelowy> [--prefix ark]
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image

DPI = 175
QUALITY = 82


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pdf')
    ap.add_argument('outdir')
    ap.add_argument('--prefix', default='ark')
    ap.add_argument('--dpi', type=int, default=DPI)
    ap.add_argument('--quality', type=int, default=QUALITY)
    a = ap.parse_args()

    if not os.path.exists(a.pdf):
        print('BLAD: brak pliku %s' % a.pdf)
        return 1
    os.makedirs(a.outdir, exist_ok=True)

    tmp = tempfile.mkdtemp(prefix='pdf2webp-')
    try:
        # pdftoppm sam numeruje strony i dopisuje rozszerzenie
        subprocess.run(['pdftoppm', '-png', '-r', str(a.dpi),
                        a.pdf, os.path.join(tmp, 'page')],
                       check=True, capture_output=True)
        pages = sorted(f for f in os.listdir(tmp) if f.endswith('.png'))
        if not pages:
            print('BLAD: pdftoppm nie wygenerowal stron')
            return 1

        for i, name in enumerate(pages, start=1):
            im = Image.open(os.path.join(tmp, name)).convert('RGB')
            out = os.path.join(a.outdir, '%s-%02d.webp' % (a.prefix, i))
            im.save(out, 'WEBP', quality=a.quality, method=5)

        first = Image.open(os.path.join(a.outdir, '%s-01.webp' % a.prefix))
        total_kb = sum(
            os.path.getsize(os.path.join(a.outdir, f))
            for f in os.listdir(a.outdir) if f.startswith(a.prefix + '-')
        ) / 1024
        print('  %s -> %d stron, %dx%d px, razem %d KB'
              % (os.path.basename(a.pdf), len(pages), first.size[0], first.size[1], total_kb))
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
