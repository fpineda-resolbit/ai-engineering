#!/usr/bin/env bash
# Envía una transcripción (archivo de texto) al endpoint de estimación.
# Uso: scripts/estimate.sh transcripts/landing-hubspot.txt [http://localhost:8000]
set -euo pipefail
file="${1:?Uso: $0 <archivo-transcripcion> [base-url]}"
base_url="${2:-http://localhost:8000}"
python3 -c 'import json,sys; print(json.dumps({"transcription": open(sys.argv[1]).read()}))' "$file" \
  | curl -sS -X POST "$base_url/api/v1/estimate" -H 'Content-Type: application/json' -d @- \
  | python3 -c 'import json,sys
d = json.load(sys.stdin)
if "estimation" not in d:
    sys.exit("Error: " + str(d.get("detail", d)))
print(d["estimation"])
print("\n---", {k: v for k, v in d.items() if k != "estimation"})'
