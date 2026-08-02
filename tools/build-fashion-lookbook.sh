#!/usr/bin/env bash
# fashion-lookbook standalone deposunu bu repodaki calisma dizinlerinden yeniden kurar.
# Container yeniden baslarsa /home/user/fashion-lookbook kaybolur; bu betik onu geri getirir.
#
#   ./tools/build-fashion-lookbook.sh [hedef_dizin]
#
# Sonra:
#   cd <hedef> && git remote add origin git@github.com:<owner>/fashion-lookbook.git
#   git push -u origin main

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DST="${1:-/home/user/fashion-lookbook}"

rm -rf "$DST"
mkdir -p "$DST/docs"

for pair in "lookbook:01-waffle-polo" "lookbook2:02-linen-shirt" "lookbook3:03-striped-shirt"; do
  src="${pair%%:*}"; dst="${pair##*:}"
  mkdir -p "$DST/$dst"
  cp "$SRC/$src/run_lookbook.py" "$DST/$dst/"
  cp "$SRC/$src"/*.jpg "$SRC/$src"/*.png "$DST/$dst/" 2>/dev/null || true
  cp "$SRC/$src/qc_report.md" "$DST/$dst/" 2>/dev/null || true
  cp -r "$SRC/$src/out" "$DST/$dst/out"
done

cp "$SRC/lookbook3/stripe_qc.py" "$DST/03-striped-shirt/"
cp "$SRC/docs/fashion-lookbook-README.md" "$DST/README.md"
cp "$SRC/docs/BRIEF.md" "$DST/docs/BRIEF.md" 2>/dev/null || true

# 03 akromatik: renk QC raporu anlamsiz, yerine cizgi olcumu yazilir
rm -f "$DST/03-striped-shirt/qc_report.md"
( cd "$SRC/lookbook3"
  echo "# Cizgi olcum raporu - siyah/kirik beyaz cizgili gomlek"; echo
  echo '```'; python3 stripe_qc.py; echo '```'
) > "$DST/03-striped-shirt/stripe_report.md"

find "$DST" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

cat > "$DST/.gitignore" <<'EOF'
__pycache__/
*.pyc
state.json
logs/
.DS_Store
EOF

cd "$DST"
git init -q
git config user.email noreply@anthropic.com
git config user.name Claude
git add -A
git commit -q -m "Fashion lookbook generator: three product runs

Single-file runner that turns product photography into a ten-frame editorial
lookbook via GPT Image 2 on Kie.ai. Three products are included, each with its
runner, reference imagery, generated frames, contact sheet and measurements."

echo "hazir: $DST"
git -C "$DST" log --oneline
du -sh "$DST"
