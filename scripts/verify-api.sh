#!/usr/bin/env bash
# Verify: health → submit form → appear in backend admin-data
set -euo pipefail
BASE="${1:-${FG_API_BASE:-http://127.0.0.1:8000}}"
BASE="${BASE%/}"
TOKEN="${ADMIN_TOKEN:-fitnessgurukul}"
NAME="Verify API $(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo "API: $BASE"
echo "1) Health"
curl -fsS --max-time 60 "$BASE/api/health"
echo
echo "2) Submit"
SUBMIT=$(curl -fsS --max-time 60 -X POST "$BASE/api/submit" \
  -H "Content-Type: application/json" \
  -d "{\"form_type\":\"consultation\",\"name\":\"$NAME\",\"phone\":\"9876543210\",\"email\":\"verify@fitnessgurukul.local\",\"program\":\"Strength Training\",\"goal\":\"Deploy checklist\",\"message\":\"scripts/verify-api.sh\"}")
echo "$SUBMIT"
echo "3) Backend admin-data"
ADMIN=$(curl -fsS --max-time 60 "$BASE/api/admin-data" -H "X-Admin-Token: $TOKEN")
python3 - "$SUBMIT" "$ADMIN" "$NAME" <<'PY'
import json, sys
submit = json.loads(sys.argv[1])
admin = json.loads(sys.argv[2])
name = sys.argv[3]
sid = submit.get("id")
rows = admin.get("submissions") or []
hit = [r for r in rows if r.get("id") == sid or r.get("name") == name]
assert submit.get("ok"), "submit failed"
assert hit, "Lead not found in backend admin-data"
print("OK — lead confirmed in backend.html data:")
print(json.dumps({k: hit[0].get(k) for k in ["id", "name", "phone", "program", "goal", "status"]}, indent=2))
PY
echo "Done."
