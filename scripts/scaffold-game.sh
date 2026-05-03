#!/usr/bin/env bash
#
# scaffold-game.sh — neues Lernspiel anlegen
#
# Verwendung:
#   bash scripts/scaffold-game.sh <game-id> "<Game Name>" "#hex" ["Beschreibung"]
#
# Beispiel:
#   bash scripts/scaffold-game.sh formen-finden "Formen finden" "#7e57c2"
#   bash scripts/scaffold-game.sh kuh-zaehlen   "Kuh-Zaehlen"   "#5fa867" "Mengen-Spiel mit Kuehen"
#
# Was passiert:
#   - kopiert _templates/new-game/ -> <game-id>/
#   - berechnet helle/dunkle Farb-Varianten aus dem Primaer-Hex
#   - ersetzt alle Platzhalter ({{GAME_ID}}, {{COLOR_PRIMARY}}, ...)
#   - gibt Hinweise fuer naechste Schritte aus

set -e

# --- Argumente pruefen ------------------------------------------------------
if [ "$#" -lt 3 ] || [ "$#" -gt 4 ]; then
  echo "Verwendung: bash scripts/scaffold-game.sh <game-id> \"<Game Name>\" \"#hex\" [\"Beschreibung\"]" >&2
  echo "Beispiel:   bash scripts/scaffold-game.sh formen-finden \"Formen finden\" \"#7e57c2\"" >&2
  exit 1
fi

GAME_ID="$1"
GAME_NAME="$2"
COLOR_PRIMARY="$3"
GAME_DESCRIPTION="${4:-Werbefreies Lernspiel}"

# Validierungen
if ! echo "$GAME_ID" | grep -Eq '^[a-z][a-z0-9-]*$'; then
  echo "Fehler: game-id darf nur Kleinbuchstaben, Ziffern und Bindestriche enthalten (Start mit Buchstabe)." >&2
  exit 1
fi
if ! echo "$COLOR_PRIMARY" | grep -Eq '^#[0-9a-fA-F]{6}$'; then
  echo "Fehler: COLOR_PRIMARY muss ein Hex-Wert mit fuehrendem # und 6 Stellen sein (z.B. #764ba2)." >&2
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$REPO_ROOT/_templates/new-game"
DST="$REPO_ROOT/$GAME_ID"

if [ ! -d "$SRC" ]; then
  echo "Fehler: Template-Verzeichnis fehlt: $SRC" >&2
  exit 1
fi
if [ -e "$DST" ]; then
  echo "Fehler: Zielverzeichnis existiert bereits: $DST" >&2
  exit 1
fi

# --- Ableitungen ------------------------------------------------------------

# Erster Buchstabe (uppercase) fuer Platzhalter-Icon
GAME_INITIAL="$(echo "$GAME_NAME" | cut -c1 | tr 'a-z' 'A-Z')"

# Kurzname: maximal 12 Zeichen vom GAME_NAME
GAME_SHORT="$(echo "$GAME_NAME" | cut -c1-12)"

# Hex-Mathematik
hex_to_rgb() {
  local h="${1#\#}"
  printf "%d %d %d" "$((16#${h:0:2}))" "$((16#${h:2:2}))" "$((16#${h:4:2}))"
}

# Heller machen (Mischung mit Weiss)
lighten() {
  local h="${1#\#}"
  local pct="$2"
  local r=$((16#${h:0:2}))
  local g=$((16#${h:2:2}))
  local b=$((16#${h:4:2}))
  r=$((r + (255 - r) * pct / 100))
  g=$((g + (255 - g) * pct / 100))
  b=$((b + (255 - b) * pct / 100))
  printf "#%02x%02x%02x" "$r" "$g" "$b"
}

# Dunkler machen (Mischung mit Schwarz)
darken() {
  local h="${1#\#}"
  local pct="$2"
  local r=$((16#${h:0:2}))
  local g=$((16#${h:2:2}))
  local b=$((16#${h:4:2}))
  r=$((r * (100 - pct) / 100))
  g=$((g * (100 - pct) / 100))
  b=$((b * (100 - pct) / 100))
  printf "#%02x%02x%02x" "$r" "$g" "$b"
}

COLOR_LIGHT="$(lighten "$COLOR_PRIMARY" 60)"
COLOR_DARK="$(darken  "$COLOR_PRIMARY" 35)"
COLOR_BG="$(lighten   "$COLOR_PRIMARY" 88)"

echo ""
echo "Lege neues Spiel an:"
echo "  Pfad:        $DST"
echo "  Name:        $GAME_NAME ($GAME_SHORT)"
echo "  Beschreibung:$GAME_DESCRIPTION"
echo "  Primaer:     $COLOR_PRIMARY"
echo "  Hell:        $COLOR_LIGHT"
echo "  Dunkel:      $COLOR_DARK"
echo "  BG:          $COLOR_BG"
echo "  Initial:     $GAME_INITIAL"
echo ""

# --- Platzhalter ersetzen + kopieren ----------------------------------------
mkdir -p "$DST"

replace_placeholders() {
  local in="$1"
  local out="$2"
  sed \
    -e "s|{{GAME_ID}}|$GAME_ID|g" \
    -e "s|{{GAME_NAME}}|$GAME_NAME|g" \
    -e "s|{{GAME_SHORT}}|$GAME_SHORT|g" \
    -e "s|{{GAME_INITIAL}}|$GAME_INITIAL|g" \
    -e "s|{{GAME_DESCRIPTION}}|$GAME_DESCRIPTION|g" \
    -e "s|{{COLOR_PRIMARY}}|$COLOR_PRIMARY|g" \
    -e "s|{{COLOR_LIGHT}}|$COLOR_LIGHT|g" \
    -e "s|{{COLOR_DARK}}|$COLOR_DARK|g" \
    -e "s|{{COLOR_BG}}|$COLOR_BG|g" \
    "$in" > "$out"
}

for src_file in "$SRC"/*; do
  fname="$(basename "$src_file")"
  replace_placeholders "$src_file" "$DST/$fname"
done

echo "OK Spiel-Dateien angelegt."
echo ""
echo "Naechste Schritte:"
echo "  1. Lokal testen:"
echo "       python -m http.server 8000   (im Repo-Wurzel)"
echo "       http://localhost:8000/$GAME_ID/"
echo "  2. Spiellogik in $GAME_ID/index.html anpassen"
echo "     (das Demo-Spiel 'Tippe auf die richtige Farbe' ersetzen)"
echo "  3. Eigenes Icon zeichnen (icon.svg, icon-maskable.svg)"
echo "  4. Spielkarte in Wurzel-index.html ergaenzen"
echo "  5. Sammlung-service-worker.js: Cache-Version bumpen"
echo ""
