#!/bin/bash
# ============================================================
# Upload MP3 nagrań do rozumienia ze słuchu (jezyk-angielski).
# ============================================================
# MP3 są DUŻE (~140 MB łącznie) — trzymamy je poza gitem (public/audio/
# jest w .gitignore) i wgrywamy osobno na S3, bez --delete.
#
# deploy.sh ma `--exclude "audio/*"` w sync, więc deploy NIE czyści
# tych plików. Trzeba je uploadować tylko gdy:
#   - dochodzi nowy rocznik arkuszy (np. 2026 PP/PR po sesji),
#   - przebudowujemy bucket od zera.
#
# Użycie:
#   ./scripts/upload-audio.sh
#
# Wymaga w .env.deploy:
#   S3_BUCKET            — np. www.matura-online.pl
#   CLOUDFRONT_DIST_ID   — ID dystrybucji www
# ============================================================

set -e

cd "$(dirname "$0")/.."

if [ -f .env.deploy ]; then
  set -a
  # shellcheck disable=SC1091
  source .env.deploy
  set +a
fi

: "${S3_BUCKET:?S3_BUCKET not set (check .env.deploy)}"
: "${CLOUDFRONT_DIST_ID:?CLOUDFRONT_DIST_ID not set (check .env.deploy)}"

if [ ! -d public/audio ]; then
  echo "ERROR: public/audio/ nie istnieje. Skopiuj MP3 z lokalnego archiwum najpierw."
  exit 1
fi

echo ">>> Upload audio → s3://${S3_BUCKET}/audio/ ..."
aws s3 cp public/audio/ "s3://${S3_BUCKET}/audio/" \
  --recursive \
  --content-type "audio/mpeg" \
  --cache-control "public, max-age=31536000, immutable"

echo ""
echo ">>> CloudFront invalidation /audio/* ..."
aws cloudfront create-invalidation \
  --distribution-id "$CLOUDFRONT_DIST_ID" \
  --paths "/audio/*" \
  --query "Invalidation.Id" --output text

echo ""
echo "OK. Test:"
echo "  curl -sIL https://www.${DOMAIN}/audio/jezyk-angielski/2025-maj-pp.mp3 | head -3"
