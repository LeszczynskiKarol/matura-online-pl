#!/bin/bash
# Batch crop wszystkich arkuszy webp -> osobny zad-NN.webp per zadanie.
# Uruchamia scripts/crop-arkusz.py na każdym folderze public/arkusze/<subject>/<arkusz>/.
# Idempotentne: skrypt re-generuje wszystkie zad-*.webp w folderze.

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

for subj_dir in public/arkusze/*/; do
  subj=$(basename "$subj_dir")
  for ark_dir in "${subj_dir}"*/; do
    ark=$(basename "$ark_dir")
    # Akceptujemy ark-, arkusz-, cz1-, cz2- jako prefixy stron
    ark_count=$(ls "${ark_dir}"ark-*.webp "${ark_dir}"arkusz-*.webp "${ark_dir}"cz1-*.webp "${ark_dir}"cz2-*.webp 2>/dev/null | wc -l)
    if [ "$ark_count" -eq 0 ]; then
      echo "[SKIP] ${subj}/${ark}: brak stron arkusza (ark/arkusz/cz1/cz2-*.webp)"
      continue
    fi
    echo ""
    echo "=== ${subj}/${ark} (${ark_count} stron) ==="
    # Usuń poprzednie zad-*.webp (idempotentność)
    rm -f "${ark_dir}"zad-*.webp
    PYTHONIOENCODING=utf-8 python scripts/crop-arkusz.py "${ark_dir}" 2>&1 | tail -3
  done
done

echo ""
echo "Done. Total zad-*.webp:"
find public/arkusze -name "zad-*.webp" | wc -l
