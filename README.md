# Lernspiele

Werbefreie, datensparsame Open-Source-Lernspiele für Kinder.

**Live:** https://breuerchristian.github.io/Lernspiele/

## Worum geht's?

Eine Sammlung kleiner Lernspiele, gebaut für die eigenen Kinder — und dann auf GitHub gestellt, damit andere Eltern sie nutzen, forken oder anpassen können. Ohne Werbung, ohne Tracker, ohne Belohnungs-Loops, ohne Account. Pädagogisch am Montessori-Prinzip orientiert: das Spiel endet, wenn das Kind fertig ist — nicht wenn der nächste Dopamin-Hit greift.

## Spiele

| Spiel | Inhalt |
|-------|--------|
| [**Buchstaben-Spiel**](buchstaben/) | Buchstaben hören und erkennen |
| [**Zahlen-Parade**](zahlen-parade/) | Rechnen mit einer wandernden Kindergruppe — Count-Masters-inspiriert, aber ohne Wettbewerb und Zeitdruck |

## Auf dem Handy installieren

Die Sammlung ist als PWA installierbar. Ein Icon auf dem Startbildschirm, beide Spiele drin.

**Android (Chrome / Edge):** [Live-URL](https://breuerchristian.github.io/Lernspiele/) öffnen → der gelbe **Installieren**-Banner oben → tippen.

**iPhone (Safari):** [Live-URL](https://breuerchristian.github.io/Lernspiele/) öffnen → Teilen-Icon unten → **Zum Home-Bildschirm**.

Beide Spiele sind danach offline spielbar.

## Werte (nicht verhandelbar)

- **Keine Werbung** — nie, nirgends.
- **Keine Tracker / Analytics / Telemetrie** — kein GA, kein Plausible, kein Sentry, kein Pixel.
- **Keine externen CDNs** — alle Assets liegen lokal im Repo. Keine Google Fonts, kein jsDelivr.
- **Keine Engagement-Hooks** — keine Streaks, keine Push-Notifications, keine "spiel weiter um X freizuschalten"-Mechanik, keine Casino-Sounds bei richtiger Antwort.
- **Keine In-App-Käufe** — alles oder nichts, immer kostenlos.
- **Lokal-first** — Spielstände (falls überhaupt) im LocalStorage. Kein Account, kein Login, kein Backend.

## Technik

Vanilla HTML/CSS/JS, ein File pro Spiel (inline CSS+JS). Keine Build-Tools, keine npm-Dependencies. Web Audio API für Sounds, LocalStorage für Persistenz, eigener Service Worker pro Spiel mit cache-first Strategie.

```
lernspiele/
├── index.html              ← Landing (Sammlung-PWA)
├── manifest.json
├── service-worker.js
├── icon.svg / icon-maskable.svg
├── buchstaben/             ← Spiel 1 (eigene PWA)
│   ├── index.html
│   ├── manifest.json
│   ├── service-worker.js
│   └── icon*.svg
└── zahlen-parade/          ← Spiel 2 (eigene PWA)
    └── ...
```

## Lokal entwickeln

```sh
python -m http.server 8000
```

Dann http://localhost:8000/ im Browser öffnen. Service Worker und Manifest funktionieren auf `localhost` ohne HTTPS.

## Neues Spiel hinzufügen

Detaillierte Checkliste in [CLAUDE.md](CLAUDE.md). Kurzfassung:

1. Neuen Unterordner anlegen, z.B. `formen/`
2. `index.html`, `manifest.json` (mit `scope: "./"` und eigenem Cache-Namen), `service-worker.js`, `icon.svg`, `icon-maskable.svg` (mit 80% Safe-Zone)
3. Spielkarte in der Root-[`index.html`](index.html) ergänzen
4. Lokal testen, Commit, Push

## Inspiration

- [GCompris](https://gcompris.net) — die größte Open-Source-Lernspielsammlung
- [Blockly Games](https://blockly.games) — statische Webseiten, laufen offline als PWA

## Mitwirken

Issues und Pull Requests willkommen — neue Spielideen, Bugfixes, Übersetzungen, alles. Bitte die Werte oben einhalten: kein Tracking, keine externen Dependencies, keine Engagement-Loops.
