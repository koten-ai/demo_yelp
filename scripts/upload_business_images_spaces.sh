#!/usr/bin/env bash
# Upload frontend/public/business-images → DigitalOcean Space (public + CDN).
#
# Mirrors on-disk layout:
#   business-images/biz:<id>/{1,2,3}.png
#   business-images/manifest.json
#
# Prerequisites:
#   - AWS CLI v2
#   - Spaces access key with write to the photos bucket
#   - CDN enabled on the Space (DO control panel)
#
# Env:
#   DO_SPACES_KEY / DO_SPACES_SECRET   (required)
#   DO_SPACES_PHOTOS_BUCKET           default: koten-yelp-demo-photos
#   DO_SPACES_PHOTOS_REGION           default: nyc3
#   DO_SPACES_PHOTOS_ENDPOINT         default: https://<region>.digitaloceanspaces.com
#   DO_SPACES_PHOTOS_PREFIX           default: business-images
#   BUSINESS_IMAGES_DIR               default: <repo>/frontend/public/business-images
#   BUSINESS_IMAGES_BASE_URL          optional; printed after upload for finalize
#   DRY_RUN=1                         list actions only
#
# Example:
#   export DO_SPACES_KEY=... DO_SPACES_SECRET=...
#   ./scripts/upload_business_images_spaces.sh
#   export BUSINESS_IMAGES_BASE_URL=https://koten-yelp-demo-photos.nyc3.cdn.digitaloceanspaces.com/business-images
#   FINALIZE_SKIP_COUCHBASE=1 python3 scripts/finalize_business_images.py   # rebuild manifest with CDN URLs
#   python3 scripts/finalize_business_images.py                            # stamp CB
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Load sibling koten_remote_deployment .env if present (optional convenience).
if [[ -f "${KOTEN_REMOTE_ENV:-}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$KOTEN_REMOTE_ENV"
  set +a
elif [[ -f "$ROOT/../koten_remote_deployment/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/../koten_remote_deployment/.env"
  set +a
fi

: "${DO_SPACES_KEY:?Set DO_SPACES_KEY (Spaces access key)}"
: "${DO_SPACES_SECRET:?Set DO_SPACES_SECRET}"

BUCKET="${DO_SPACES_PHOTOS_BUCKET:-koten-yelp-demo-photos}"
REGION="${DO_SPACES_PHOTOS_REGION:-${DO_SPACES_REGION:-nyc3}}"
ENDPOINT="${DO_SPACES_PHOTOS_ENDPOINT:-https://${REGION}.digitaloceanspaces.com}"
PREFIX="${DO_SPACES_PHOTOS_PREFIX:-business-images}"
PREFIX="${PREFIX#/}"
PREFIX="${PREFIX%/}"
SRC="${BUSINESS_IMAGES_DIR:-$ROOT/frontend/public/business-images}"
DRY_RUN="${DRY_RUN:-0}"

if [[ ! -d "$SRC" ]]; then
  echo "error: BUSINESS_IMAGES_DIR not a directory: $SRC" >&2
  exit 1
fi

if ! command -v aws >/dev/null 2>&1; then
  echo "error: aws CLI required (AWS CLI v2 works with DO Spaces)" >&2
  exit 1
fi

export AWS_ACCESS_KEY_ID="$DO_SPACES_KEY"
export AWS_SECRET_ACCESS_KEY="$DO_SPACES_SECRET"
export AWS_DEFAULT_REGION="$REGION"

DEST="s3://${BUCKET}/${PREFIX}/"
CDN_BASE="${BUSINESS_IMAGES_BASE_URL:-https://${BUCKET}.${REGION}.cdn.digitaloceanspaces.com/${PREFIX}}"
CDN_BASE="${CDN_BASE%/}"

echo "==> source  $SRC"
echo "==> dest    $DEST"
echo "==> endpoint $ENDPOINT"
echo "==> CDN base (for BUSINESS_IMAGES_BASE_URL): $CDN_BASE"

if [[ "$DRY_RUN" == "1" ]]; then
  aws s3 sync "$SRC/" "$DEST" \
    --endpoint-url "$ENDPOINT" \
    --exclude ".*" \
    --dryrun
  exit 0
fi

# Ensure bucket exists (idempotent-ish).
if ! aws s3api head-bucket --bucket "$BUCKET" --endpoint-url "$ENDPOINT" 2>/dev/null; then
  echo "==> creating Space $BUCKET in $REGION"
  aws s3api create-bucket \
    --bucket "$BUCKET" \
    --region "$REGION" \
    --endpoint-url "$ENDPOINT" \
    --create-bucket-configuration LocationConstraint="$REGION" || true
fi

# Sync images + tree (keeps biz: directory names). Public-read for CDN <img>.
aws s3 sync "$SRC/" "$DEST" \
  --endpoint-url "$ENDPOINT" \
  --acl public-read \
  --exclude ".*" \
  --exclude "manifest.json"

if [[ -f "$SRC/manifest.json" ]]; then
  aws s3 cp "$SRC/manifest.json" "${DEST}manifest.json" \
    --endpoint-url "$ENDPOINT" \
    --acl public-read \
    --content-type application/json \
    --metadata-directive REPLACE
fi

# Spot-check: first PNG under a biz:* dir
sample="$(find "$SRC" -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.webp' \) | head -n 1 || true)"

if [[ -n "$sample" ]]; then
  rel="${sample#"$SRC"/}"
  probe_path="${PREFIX}/${rel}"
  probe_url="https://${BUCKET}.${REGION}.cdn.digitaloceanspaces.com/${probe_path}"
  echo "==> probe $probe_url"
  code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 20 -L "$probe_url" || true)"
  echo "==> probe HTTP $code"
  if [[ "$code" != "200" ]]; then
    origin="https://${BUCKET}.${REGION}.digitaloceanspaces.com/${probe_path}"
    code2="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 20 -L "$origin" || true)"
    echo "==> origin probe HTTP $code2 ($origin)"
    if [[ "$code2" != "200" ]]; then
      echo "warn: public GET failed — enable CDN + public-read / bucket policy in DO UI" >&2
    fi
  fi
fi

count="$(find "$SRC" -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' -o -name '*.webp' \) | wc -l | tr -d ' ')"
echo "==> upload complete ($count image files under prefix ${PREFIX}/)"
echo
echo "Next:"
echo "  export BUSINESS_IMAGES_BASE_URL=${CDN_BASE}"
echo "  # rebuild manifest + stamp CB with absolute CDN URLs:"
echo "  python3 scripts/finalize_business_images.py"
echo "  # or manifest only:"
echo "  FINALIZE_SKIP_COUCHBASE=1 python3 scripts/finalize_business_images.py"
echo
echo "App runtime: set the same BUSINESS_IMAGES_BASE_URL so catalog URLs match CDN."
