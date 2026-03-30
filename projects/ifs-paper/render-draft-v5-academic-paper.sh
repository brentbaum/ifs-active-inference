#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
repo_root="$(cd ../.. && pwd)"

tmp_markdown="$(mktemp)"
trap 'rm -f "$tmp_markdown"' EXIT

tail -n +5 draft-v5.md > "$tmp_markdown"

# Normalize the markdown for LaTeX conversion:
# - remove manual section numbering because LaTeX numbers sections for us
# - strip markdown hard line breaks that force awkward list/item spacing
perl -0pi -e 's/^(#{2,6})\s+\d+(?:\.\d+)*\.?\s+/$1 /mg; s/[ \t]+$//mg' "$tmp_markdown"

pandoc "$tmp_markdown" \
  --from markdown+tex_math_single_backslash \
  --to latex \
  --standalone \
  --shift-heading-level-by=-1 \
  --template=latex/academic-paper-v5-template.tex \
  --lua-filter=latex/inline_figures_v5.lua \
  --metadata title="Self-Energy, Witnessing, and the Revision of Part Beliefs" \
  --metadata subtitle="An Active Inference Account of Internal Family Systems" \
  -o draft-v5-academic-paper.tex

rm -rf ./draft-v5-academic-paper-previews
mkdir -p ./draft-v5-academic-paper-previews

bash "$repo_root/.agents/skills/seminal/latex-document-skill/scripts/compile_latex.sh" \
  draft-v5-academic-paper.tex \
  --engine pdflatex \
  --use-latexmk \
  --preview \
  --preview-dir ./draft-v5-academic-paper-previews
