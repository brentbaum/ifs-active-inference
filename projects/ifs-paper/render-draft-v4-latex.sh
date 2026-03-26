#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

tmp_markdown="$(mktemp)"
trap 'rm -f "$tmp_markdown"' EXIT

tail -n +5 draft-v4.md > "$tmp_markdown"

pandoc "$tmp_markdown" \
  --from markdown \
  --to latex \
  --standalone \
  --shift-heading-level-by=-1 \
  --metadata title="Self-Energy, Witnessing, and the Revision of Part Beliefs: An Active Inference Account of Internal Family Systems" \
  --metadata date="Draft v4 working paper" \
  --template=latex/article-template.tex \
  --lua-filter=latex/inline_figures.lua \
  -o draft-v4-inline-figures.tex

awk -f latex/postprocess_tables.awk draft-v4-inline-figures.tex > draft-v4-inline-figures.tmp.tex
mv draft-v4-inline-figures.tmp.tex draft-v4-inline-figures.tex

pandoc "$tmp_markdown" \
  --from markdown \
  --to html \
  --standalone \
  --shift-heading-level-by=-1 \
  --metadata title="Self-Energy, Witnessing, and the Revision of Part Beliefs: An Active Inference Account of Internal Family Systems" \
  --metadata date="Draft v4 working paper" \
  --template=latex/article-template.html \
  --lua-filter=latex/inline_figures.lua \
  -o draft-v4-inline-figures.html

if tectonic -C draft-v4-inline-figures.tex; then
  exit 0
fi

xhtml2pdf_python="/Users/brentbaum/.local/share/uv/python/cpython-3.11.11-macos-aarch64-none/bin/python3.11"
xhtml2pdf_site="/Users/brentbaum/.cache/uv/archive-v0/H0uLe5xtoqxnpdQQoP7S1/lib/python3.11/site-packages"
chrome_bin="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

if [[ -x "$xhtml2pdf_python" && -d "$xhtml2pdf_site" ]]; then
  if PYTHONPATH="$xhtml2pdf_site" "$xhtml2pdf_python" -c "from pathlib import Path; from xhtml2pdf import pisa; src = Path('draft-v4-inline-figures.html'); html = src.read_text(encoding='utf-8'); out = Path('draft-v4-inline-figures.pdf'); out.write_bytes(b''); result = None
with out.open('wb') as f:
    result = pisa.CreatePDF(html, dest=f, path=str(src.resolve()))
raise SystemExit(0 if not result.err else 1)"; then
    exit 0
  fi
fi

if [[ -x "$chrome_bin" ]]; then
  "$chrome_bin" \
    --headless \
    --disable-gpu \
    --allow-file-access-from-files \
    --print-to-pdf="$(pwd)/draft-v4-inline-figures.pdf" \
    "file://$(pwd)/draft-v4-inline-figures.html"
  exit 0
fi

echo "No working PDF renderer found." >&2
exit 1
