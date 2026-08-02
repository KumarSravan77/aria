#!/usr/bin/env bash
set -euo pipefail
URL=${1:-http://localhost:9000/checkout}
for i in {1..100}; do
  curl -s -o /dev/null -w "%{http_code} %{time_total}\n" "$URL" &
  sleep 0.05
done
wait
