#!/usr/bin/env bash
set -euo pipefail
command -v docker >/dev/null || { echo "Docker is required"; exit 1; }
command -v python3 >/dev/null || { echo "Python3 is required"; exit 1; }
make local-up
sleep 8
make ingest
make sample-investigation
