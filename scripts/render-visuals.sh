#!/usr/bin/env bash
# Regenera los SVG de assets/src/ y los renderiza a PNG.
#
#   ./scripts/render-visuals.sh            renderiza todo
#   ./scripts/render-visuals.sh 04         renderiza solo lo que coincida con "04"
#   ./scripts/render-visuals.sh poster     renderiza solo el poster
#
# Requiere: python3 y rsvg-convert (librsvg2-tools / librsvg2-bin).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/assets/src"
FILTER="${1:-}"

command -v rsvg-convert >/dev/null 2>&1 || {
  echo "error: falta rsvg-convert. Instalar librsvg2-tools (Fedora) o librsvg2-bin (Debian)." >&2
  exit 1
}

echo "Generando SVG..."
python3 "$ROOT/scripts/build_visuals.py" "$SRC"

mkdir -p "$ROOT/assets/diagrams" "$ROOT/assets/poster"

echo "Renderizando PNG..."
shopt -s nullglob
for svg in "$SRC"/*.svg; do
  name="$(basename "$svg" .svg)"
  [ -n "$FILTER" ] && [[ "$name" != *"$FILTER"* ]] && continue

  if [[ "$name" == poster* ]]; then
    dest="$ROOT/assets/poster/$name.png"
    width=2480                       # A2 a 150 dpi
  else
    dest="$ROOT/assets/diagrams/$name.png"
    width=3200                       # 2x para pantallas de alta densidad
  fi

  rsvg-convert -w "$width" "$svg" -o "$dest"
  printf "  png  %-52s %s\n" "${dest#$ROOT/}" "$(identify -format '%wx%h' "$dest" 2>/dev/null || echo '')"
done

echo "Listo."
