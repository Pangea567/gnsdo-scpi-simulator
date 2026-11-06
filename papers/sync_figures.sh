#!/bin/bash
# experiments/figures/*.pdf -> her bildiri klasorunun figures/ altina kopyalar.
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/experiments/figures"
shopt -s nullglob
pdfs=("$SRC"/*.pdf)
if [ ${#pdfs[@]} -eq 0 ]; then
  echo "Kaynak grafik bulunamadı; mevcut figures/ dosyaları kullanılacak." >&2
  exit 0
fi
for paper in "$ROOT"/papers/*/; do
  [ -f "$paper/main.tex" ] || continue
  fig="$paper/figures"
  mkdir -p "$fig"
  cp "${pdfs[@]}" "$fig/"
  echo "kopyalandi -> ${paper}figures/"
done
