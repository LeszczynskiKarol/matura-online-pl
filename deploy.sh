#!/bin/bash
# ============================================================
# One-shot deploy: git → S3 → CloudFront
# ============================================================
# Użycie:
#   ./deploy.sh                       # auto commit message
#   ./deploy.sh "fix: hero copy"      # ręczny commit message
#
# Co robi po kolei:
#   1) jeśli są niecommitowane zmiany → git add + commit + push
#   2) npm ci + npm run build
#   3) aws s3 sync (assets long-cache + HTML no-cache, osobno)
#   4) cloudfront create-invalidation /*
#
# Wymaga w .env.deploy (gitignored) lub w env:
#   S3_BUCKET            — np. www.foo.pl
#   CLOUDFRONT_DIST_ID   — ID dystrybucji www
#   PUBLIC_API_BASE_URL  — (opcjonalnie) URL API Gateway dla formularza
# ============================================================

set -e

if [ -f .env.deploy ]; then
  set -a
  # shellcheck disable=SC1091
  source .env.deploy
  set +a
fi

: "${S3_BUCKET:?S3_BUCKET not set (check .env.deploy)}"
: "${CLOUDFRONT_DIST_ID:?CLOUDFRONT_DIST_ID not set (check .env.deploy)}"

COMMIT_MSG="${1:-}"

# ── 1. Git: commit + push tylko jeśli są zmiany ────────────
echo ">>> [1/4] git status"

if [ -d .git ]; then
  # Wyklucz pliki ignorowane — sprawdzamy tylko tracked + nowe nieignorowane.
  if [ -n "$(git status --porcelain)" ]; then
    echo "    Niecommitowane zmiany — zapisuję..."

    git add .

    if [ -z "$COMMIT_MSG" ]; then
      # Auto-commit: lista zmienionych plików (max 10) w treści
      CHANGED=$(git diff --cached --name-only | head -10 | sed 's/^/  - /')
      COMMIT_MSG="chore: deploy $(date +%Y-%m-%d)

Zmiany w tym deployu:
$CHANGED"
    fi

    git commit -m "$COMMIT_MSG"

    # Push tylko jeśli jest remote 'origin'
    if git remote get-url origin >/dev/null 2>&1; then
      CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
      echo "    Pushuję $CURRENT_BRANCH → origin..."
      git push origin "$CURRENT_BRANCH"
    else
      echo "    Brak remote 'origin' — pomijam push."
    fi
  else
    echo "    Brak zmian w git — pomijam commit/push."
  fi
else
  echo "    Brak .git/ — pomijam git step (lokalne repo nie zainicjalizowane)."
fi

# ── 2. Build ───────────────────────────────────────────────
echo ""
echo ">>> [2/4] Build Astro..."

# Instaluj deps tylko jeśli node_modules nie istnieje albo package-lock zmienił się
if [ ! -d node_modules ] || [ package-lock.json -nt node_modules ]; then
  npm ci
fi

npm run build

# Manifest zdeployowanego commita. Pozwala w 2 sekundy zweryfikować co jest na
# prodzie: `curl https://www.<domain>/_commit.txt`. Jeśli `short=` na live nie
# zgadza się z `git rev-parse --short HEAD` → masz drift, odpal deploy.sh.
if [ -d .git ]; then
  DEPLOY_SHA=$(git rev-parse HEAD)
  DEPLOY_SHORT=$(git rev-parse --short HEAD)
  DEPLOY_SUBJ=$(git log -1 --format=%s)
  DEPLOY_TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  cat > dist/_commit.txt <<EOF
sha=$DEPLOY_SHA
short=$DEPLOY_SHORT
ts=$DEPLOY_TS
subject=$DEPLOY_SUBJ
EOF
  echo "    Manifest: dist/_commit.txt (HEAD=$DEPLOY_SHORT)"
fi

# ── 3. S3 sync ─────────────────────────────────────────────
echo ""
echo ">>> [3/4] S3 sync s3://${S3_BUCKET}/ ..."

# Assets (everything except HTML/robots/sitemap) — immutable, long cache
aws s3 sync dist/ "s3://${S3_BUCKET}/" \
  --delete \
  --cache-control "public, max-age=31536000, immutable" \
  --exclude "*.html" \
  --exclude "robots.txt" \
  --exclude "sitemap*.xml"

# HTML + robots + sitemap + _commit.txt — no cache, must revalidate
aws s3 sync dist/ "s3://${S3_BUCKET}/" \
  --cache-control "public, max-age=0, must-revalidate" \
  --exclude "*" \
  --include "*.html" \
  --include "robots.txt" \
  --include "sitemap*.xml" \
  --include "_commit.txt"

# ── 4. CloudFront invalidation ─────────────────────────────
echo ""
echo ">>> [4/4] CloudFront invalidation..."

INV_ID=$(aws cloudfront create-invalidation \
  --distribution-id "$CLOUDFRONT_DIST_ID" \
  --paths "/*" \
  --query "Invalidation.Id" --output text)

echo "    Invalidation: $INV_ID (zwykle gotowe w 1-3 min)"

# ── Done ───────────────────────────────────────────────────
DOMAIN_FROM_BUCKET="${S3_BUCKET#www.}"
echo ""
echo "Done."
echo "  https://www.${DOMAIN_FROM_BUCKET}"
echo "  https://${DOMAIN_FROM_BUCKET} (301 → www)"
if [ -n "${DEPLOY_SHORT:-}" ]; then
  CURRENT_HEAD=$(git rev-parse --short HEAD 2>/dev/null || echo "?")
  echo ""
  echo "  Zdeployowany commit: $DEPLOY_SHORT — \"$DEPLOY_SUBJ\""
  if [ "$DEPLOY_SHORT" != "$CURRENT_HEAD" ] && [ "$CURRENT_HEAD" != "?" ]; then
    echo "  ⚠ UWAGA: lokalny HEAD ($CURRENT_HEAD) przesunął się podczas deployu — re-run skryptu."
  fi
  echo "  Weryfikacja: curl https://www.${DOMAIN_FROM_BUCKET}/_commit.txt"
fi
