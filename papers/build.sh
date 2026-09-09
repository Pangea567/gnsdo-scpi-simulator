#!/bin/bash
# Bir bildiriyi derler: figurleri senkronlar, tectonic ile PDF uretir.
# Kullanim: ./papers/build.sh draft-en
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAPER="${1:-draft-en}"
"$ROOT/papers/sync_figures.sh" >/dev/null
cd "$ROOT/papers/$PAPER"
tectonic main.tex
echo "PDF: papers/$PAPER/main.pdf"
