#!/bin/bash
# ============================================================
# Naprawia CloudFront CustomErrorResponses dla maturalnie.pl:
#   - 403 → /404.html (status 404)   ← NOWE; S3 zwraca 403 dla missing obj
#   - 404 → /404.html (status 404)   ← już istnieje
#
# Bez tego każda nieistniejąca ścieżka serwuje surowy AWS XML 403.
#
# Uruchom: ./scripts/fix-cf-error-responses.sh
# Wymaga: aws CLI + jq + CLOUDFRONT_DIST_ID w .env.deploy
#
# Idempotentne — można uruchamiać wielokrotnie.
# ============================================================

set -e

if [ -f .env.deploy ]; then
  set -a
  # shellcheck disable=SC1091
  source .env.deploy
  set +a
fi

: "${CLOUDFRONT_DIST_ID:?CLOUDFRONT_DIST_ID not set (sprawdź .env.deploy)}"

TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

echo ">>> Pobieram aktualną konfigurację dystrybucji $CLOUDFRONT_DIST_ID..."
aws cloudfront get-distribution-config --id "$CLOUDFRONT_DIST_ID" > "$TMPDIR/raw.json"
ETAG=$(jq -r '.ETag' "$TMPDIR/raw.json")
jq '.DistributionConfig' "$TMPDIR/raw.json" > "$TMPDIR/config.json"

echo "    ETag: $ETAG"
echo "    Obecne CustomErrorResponses:"
jq '.CustomErrorResponses' "$TMPDIR/config.json"

echo ""
echo ">>> Patchuję CustomErrorResponses (403 + 404 → /404.html, ResponseCode 404, TTL 60s)..."
jq '.CustomErrorResponses = {
  "Quantity": 2,
  "Items": [
    { "ErrorCode": 403, "ResponsePagePath": "/404.html", "ResponseCode": "404", "ErrorCachingMinTTL": 60 },
    { "ErrorCode": 404, "ResponsePagePath": "/404.html", "ResponseCode": "404", "ErrorCachingMinTTL": 60 }
  ]
}' "$TMPDIR/config.json" > "$TMPDIR/config-patched.json"

echo "    Nowe CustomErrorResponses:"
jq '.CustomErrorResponses' "$TMPDIR/config-patched.json"

echo ""
echo ">>> Wysyłam update-distribution..."
aws cloudfront update-distribution \
  --id "$CLOUDFRONT_DIST_ID" \
  --if-match "$ETAG" \
  --distribution-config "file://$TMPDIR/config-patched.json" \
  > "$TMPDIR/update-result.json"

NEW_STATUS=$(jq -r '.Distribution.Status' "$TMPDIR/update-result.json")
NEW_ETAG=$(jq -r '.ETag' "$TMPDIR/update-result.json")
echo "    Status: $NEW_STATUS   (InProgress → Deployed za ~3-5 min)"
echo "    Nowy ETag: $NEW_ETAG"

echo ""
echo ">>> Invalidate 404.html w cache:"
aws cloudfront create-invalidation \
  --distribution-id "$CLOUDFRONT_DIST_ID" \
  --paths "/404.html" \
  --query "Invalidation.Id" --output text

echo ""
echo "Done. Walidacja za ~5 min:"
echo "  curl -sI https://www.maturalnie.pl/no-such-page/   # MUSI być HTTP/1.1 404 (nie 403)"
echo "  curl -sI https://www.maturalnie.pl/404.html        # 200"
