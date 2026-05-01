# Lernspiele für Kinder

## Projekt-Kontext

Sammlung kleiner werbefreier Lernspiele für die eigenen Kinder.
**Monorepo:** ein Repository, mehrere Spiele — jedes Spiel ist ein eigener Unterordner mit eigener PWA.

GitHub-Repo: https://github.com/BreuerChristian/Lernspiele
Live (nach Pages-Aktivierung): https://breuerchristian.github.io/Lernspiele/

## Repo-Struktur

```
lernspiele/
├── CLAUDE.md            ← du liest gerade
├── .nojekyll            ← GitHub Pages: kein Jekyll-Processing
├── index.html           ← Landing-Page mit Liste aller Spiele
├── icon.svg             ← Sammlungs-Icon (Favicon der Landing-Page)
└── <spiel>/             ← jedes Spiel als eigenständige PWA
    ├── index.html
    ├── manifest.json    ← scope: "./", start_url: "./"
    ├── service-worker.js
    ├── icon.svg
    └── icon-maskable.svg
```

Aktuell vorhandene Spiele: `buchstaben/`

## Leitprinzipien (NICHT verhandelbar)

- **Keine Werbung.** Nie. Nirgends.
- **Keine Tracker / Analytics / Telemetrie.** Kein GA, kein Plausible, kein Sentry, kein Pixel.
- **Keine externen CDNs.** Keine Google Fonts, kein jsDelivr, kein cdnjs. Alle Assets liegen lokal im Repo. Grund: kein Datenabfluss, vollständige Offline-Fähigkeit, keine Abhängigkeit von Drittparteien die ihrerseits tracken könnten.
- **Keine In-App-Käufe, keine Engagement-Hooks.** Montessori-Ansatz: Spiel endet wenn das Kind fertig ist, nicht wenn der nächste Belohnungs-Loop greift. Keine Streaks, keine Push-Notifications, kein "spiel weiter um X freizuschalten".
- **Lokal-first.** Spielstände (falls überhaupt) im LocalStorage. Kein Account, kein Login, kein Backend.
- **Open Source auf GitHub.** Andere Eltern sollen es nutzen, forken, anpassen können.

## Tech-Stack

- Vanilla HTML/CSS/JS, single-file pro Spiel wo möglich
- Keine Build-Tools, keine npm-Dependencies (jedenfalls nicht in Phase 1)
- Web Audio API für Sounds (keine externen Audio-Libraries)
- LocalStorage für Persistenz
- Pro Spiel: eigener Service Worker mit Scope auf den jeweiligen Unterordner

## Neues Spiel hinzufügen — Checkliste

1. Neuen Unterordner anlegen, z.B. `zahlen/`
2. `index.html` mit Spiel-Logik schreiben (single-file, inline CSS+JS bevorzugt)
3. Im `<head>` einbinden:
   ```html
   <link rel="manifest" href="manifest.json">
   <link rel="icon" type="image/svg+xml" href="icon.svg">
   <link rel="apple-touch-icon" href="icon.svg">
   <meta name="theme-color" content="#764ba2">
   <meta name="apple-mobile-web-app-capable" content="yes">
   <meta name="mobile-web-app-capable" content="yes">
   ```
4. Service Worker am Ende des `<script>`-Blocks registrieren:
   ```js
   if ('serviceWorker' in navigator) {
     window.addEventListener('load', () => {
       navigator.serviceWorker.register('service-worker.js').catch(() => {});
     });
   }
   ```
5. `manifest.json` mit `start_url: "./"`, `scope: "./"`, eigenem Namen + Icon
6. `service-worker.js`: cache-first, ASSETS-Liste mit allen lokalen Dateien, eindeutiger Cache-Name (z.B. `zahlen-spiel-v1`)
7. `icon.svg` + `icon-maskable.svg` (Maskable: 80% Safe-Zone für adaptive Android-Icons)
8. In Root-`index.html` die Spielkarte ergänzen
9. Lokal testen: `python -m http.server 8000` → DevTools → Application prüfen
10. Commit + push

## Roadmap (Phasen)

### Phase 1 — PWA + GitHub Pages (laufend)
- Monorepo-Struktur ✓
- Buchstaben-Spiel als PWA ✓
- GitHub Pages aktivieren → HTTPS-URL
- Auf Kinder-Handy: Browser → "Zum Startbildschirm hinzufügen"

### Phase 2 — Capacitor + F-Droid
- Capacitor wrappt einzelne Spiele in APKs (oder Sammlungs-APK)
- Veröffentlichung auf F-Droid
- **Trigger:** wenn 2-3 Spiele drin sind und Eltern fragen "wie installier ich das richtig?"

### Phase 3 — Play Store (optional, nur wenn echte Reichweite gewünscht)
- $25 Developer-Gebühr einmalig
- "Designed for Families"-Programm: strenge COPPA-/Datenschutz-Regeln
- **Wichtig:** Play Store ≠ Community. Reichweite ja, Eltern-Vernetzung nein. Community-Plattform bleibt GitHub Discussions.

## Inspiration / Referenz-Projekte

- **GCompris** (https://gcompris.net) — größte Open-Source-Lernspielsammlung
- **Blockly Games** (Google, Open Source) — statische Webseite, läuft als PWA
- **Khan Academy Kids** — werbefrei, aber proprietär und native

## Anti-Patterns (was wir NICHT tun)

- Keine "Du hast 7 Tage in Folge gespielt!"-Mechaniken
- Keine Sterne/Coins/Belohnungen die zum Weiterspielen drängen
- Keine Sound-Effekte die manipulativ Dopamin triggern (kein Casino-Sound bei richtiger Antwort)
- Keine Timer / "Schnell!" / Wettbewerbselemente
- Kein "Premium-Modus" — alles oder nichts, immer kostenlos
- Keine externen Schriftarten/Bibliotheken — alles lokal
