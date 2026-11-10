#!/usr/bin/env bash
# Build all formats from the shared TikZ source. Optional output root is isolated.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
out="${1:-$root}"
mkdir -p "$out/report/figures" "$out/docs/figures"
out="$(cd "$out" && pwd)"
build="$(mktemp -d)"
trap 'rm -rf "$build"' EXIT
cp "$root/report/figures/ssc_two_graph_pipeline."{tex,tikz} "$build/"
(cd "$build" && pdflatex -interaction=nonstopmode -halt-on-error ssc_two_graph_pipeline.tex > build.log) || { cat "$build/build.log"; exit 1; }
pdf="$out/report/figures/ssc_two_graph_pipeline.pdf"
cp "$build/ssc_two_graph_pipeline.pdf" "$pdf"
pdftocairo -svg "$pdf" "$out/docs/figures/ssc_two_graph_pipeline.svg"
pdftocairo -png -singlefile -r 220 "$pdf" "$out/docs/figures/ssc_two_graph_pipeline"
