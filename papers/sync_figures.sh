#!/bin/bash
# experiments/figures/*.pdf -> her bildiri klasorunun figures/ altina kopyalar.
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/experiments/figures"
for paper in "$ROOT"/papers/*/; do
  [ -d "$paper" ] || continue
  fig="$paper/figures"
  [ -d "$fig" ] || continue
  cp "$SRC"/*.pdf "$fig"/ 2>/dev/null && echo "kopyalandi -> ${paper}figures/"
done
