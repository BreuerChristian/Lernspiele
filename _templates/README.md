# `_templates/` — Scaffold-Vorlagen

## `new-game/` — Vorlage für ein neues Spiel

Das Verzeichnis enthält ein lauffähiges Mini-Spiel ("Tippe auf die richtige Farbe"),
das alle Standard-Patterns demonstriert:

- HTML-Boilerplate mit Theme-Color, Manifest, Apple-Meta-Tags
- CSS-Custom-Properties für Farb-Theme (`--color-primary`, `--color-light`, ...)
- HUD-Layout (links Stufe | Mitte Aufgabe X/N | rechts ×-Button)
- Start-Screen mit Card, Übersicht-Link, Stufen-Auswahl, LocalStorage-Persistenz
- End-Screen mit "Nochmal spielen / Andere Stufe / Zur Übersicht"
- Standard-Animationen (`correct-pulse`, `wrong-wiggle`, `fade-in`)
- A11y: ARIA-Labels, sichtbare Focus-Outlines, `prefers-reduced-motion`
- Audio-Lib-Einbindung (`../_lib/audio.js`)
- Service-Worker mit korrektem Cache-Präfix

## Platzhalter

Das Scaffold-Skript (`scripts/scaffold-game.sh`) ersetzt diese Tokens:

| Platzhalter | Beispiel | Wo |
|---|---|---|
| `{{GAME_ID}}` | `mein-spiel` | Ordnername, Cache-Präfix, LocalStorage-Key |
| `{{GAME_NAME}}` | `Mein Spiel` | Titel, Manifest-Name, Apple-Meta-Title |
| `{{GAME_SHORT}}` | `Mein` | Manifest-`short_name` (max ~12 Zeichen) |
| `{{GAME_INITIAL}}` | `M` | Erster Buchstabe für Platzhalter-Icon |
| `{{GAME_DESCRIPTION}}` | `Werbefreies Lernspiel für ...` | Manifest-Description, Untertitel |
| `{{COLOR_PRIMARY}}` | `#764ba2` | Theme-Color (Manifest, Meta, CSS) |
| `{{COLOR_LIGHT}}` | `#e0d0ed` | Hintergrund hover, Card-Akzent |
| `{{COLOR_DARK}}` | `#4a2a6a` | Text auf hellem Hintergrund |
| `{{COLOR_BG}}` | `#f7f3fa` | Body-Hintergrund, Manifest-Background |

## Workflow

```bash
bash scripts/scaffold-game.sh mein-spiel "Mein Spiel" "#764ba2"
```

→ Erzeugt `mein-spiel/` mit allen Platzhaltern ersetzt. Helle/dunkle Farb-Varianten
werden aus `COLOR_PRIMARY` automatisch berechnet (heller / dunkler je 25%).

Danach:
1. `python -m http.server 8000` im Repo-Wurzel
2. `http://localhost:8000/mein-spiel/` öffnen
3. Spiellogik im `<script>`-Block am Ende der `index.html` ersetzen
4. Eigenes Icon (`icon.svg`, `icon-maskable.svg`) zeichnen
5. Spielkarte in der Wurzel-`index.html` ergänzen
6. Sammlung-`service-worker.js`: Cache-Version bumpen
