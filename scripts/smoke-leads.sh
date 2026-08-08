#!/usr/bin/env bash
# Smoke-test Google Apps Script lead collector (GET write path).
set -euo pipefail

SCRIPT_URL="${GOOGLE_SCRIPT_URL:-https://script.google.com/macros/s/AKfycbyXPppJZTHgWtOKAa61_lmtZdkYcYfjmO9YlOpYUWazc3t-wc40NJ7d_lh1KtECByQ/exec}"
SCRIPT_URL="${SCRIPT_URL%/}"
SCRIPT_URL="${SCRIPT_URL%/dev}/exec"
SCRIPT_URL="${SCRIPT_URL%/exec}/exec"

TS="$(date -u +%Y%m%dT%H%M%SZ)"
RESP="$(curl -sS -L --max-time 90 -G "$SCRIPT_URL" \
  --data-urlencode "write=1" \
  --data-urlencode "form_type=consultation" \
  --data-urlencode "name=CI Smoke Lead $TS" \
  --data-urlencode "phone=9000000000" \
  --data-urlencode "email=ci-smoke@example.com" \
  --data-urlencode "message=Automated smoke test $TS" \
  --data-urlencode "source=ci-smoke")"

echo "$RESP" | grep -q '"ok":true'
echo "$RESP" | grep -q '"emailed":true'
echo "Lead smoke OK: $RESP"
