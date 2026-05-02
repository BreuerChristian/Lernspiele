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
├── README.md
├── LICENSE              ← MIT
├── .nojekyll            ← GitHub Pages: kein Jekyll-Processing
├── index.html           ← Landing (selbst PWA: Sammlung-App)
├── manifest.json        ← Sammlung-PWA, scope: "./" deckt alle Spiele
├── service-worker.js    ← cache-first, filtert Unterordner an Spiel-SWs
├── icon.svg
├── icon-maskable.svg
└── <spiel>/             ← jedes Spiel als eigenständige PWA
    ├── index.html
    ├── manifest.json    ← scope: "./", start_url: "./"
    ├── service-worker.js
    ├── icon.svg
    └── icon-maskable.svg
```

Eltern installieren *eine* App (die Sammlung), beide/alle Spiele sind drin. Die einzelnen Spiel-Manifests bleiben für separate Installierbarkeit.

Aktuell vorhandene Spiele: `buchstaben/`, `zahlen-parade/`, `hauptstaedte-lernen/`

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
- LocalStorage für Persistenz, Keys mit Spielname-Präfix (`zahlen-parade-prefs`)
- Pro Spiel: eigener Service Worker mit Scope auf den jeweiligen Unterordner
- **Schrift:** `'Verdana', 'Tahoma', sans-serif` — kein Comic Sans/Cursive (Kinder die Lesen lernen tun sich mit Schnörkelschriften schwer). Verdana ist auf allen Plattformen verfügbar und für Bildschirm designed.

## Neues Spiel hinzufügen — Checkliste

**0. Vor dem Codieren (Plan-Pitch).** Konzept in 5-7 Sätzen vorstellen + Nutzer-Bestätigung einholen. Modi, Stufen, Steuerung früh klären. Bei Vorbild-Spielen: Anti-Patterns identifizieren (was raus muss um Montessori-konform zu sein — Wettbewerb, Zeitdruck, Belohnungs-Loops, manipulative Sounds).

1. Neuen Unterordner anlegen, z.B. `zahlen/`
2. `index.html` mit Spiel-Logik schreiben (single-file, inline CSS+JS bevorzugt). Schrift `'Verdana', 'Tahoma', sans-serif`. Eigene Theme-Color je Spiel (Buchstaben lila `#764ba2`, Zahlen-Parade grün `#5fa867`).
3. Im `<head>` einbinden:
   ```html
   <link rel="manifest" href="manifest.json">
   <link rel="icon" type="image/svg+xml" href="icon.svg">
   <link rel="apple-touch-icon" href="icon.svg">
   <meta name="theme-color" content="#764ba2">
   <meta name="apple-mobile-web-app-capable" content="yes">
   <meta name="apple-mobile-web-app-status-bar-style" content="default">
   <meta name="mobile-web-app-capable" content="yes">
   ```
4. **"← Übersicht"-Link** auf dem Start-Screen des Spiels (`href="../"`). Nicht im laufenden Spiel — Verwechslungs-Gefahr mit Pause/×.
5. Service Worker am Ende des `<script>`-Blocks registrieren:
   ```js
   if ('serviceWorker' in navigator) {
     window.addEventListener('load', () => {
       navigator.serviceWorker.register('service-worker.js').catch(() => {});
     });
   }
   ```
6. `manifest.json` mit `start_url: "./"`, `scope: "./"`, `lang: "de"`, eigenem Namen + Icon
7. `service-worker.js`: cache-first, ASSETS-Liste mit allen lokalen Dateien, eindeutiger Cache-Name (z.B. `zahlen-spiel-v1`). **Cleanup-Filter im `activate`-Handler MUSS auf eigenen Präfix beschränkt sein:**
   ```js
   keys.filter(key => key !== CACHE && key.startsWith('zahlen-spiel-'))
   ```
   Sonst löscht der SW fremde Caches anderer PWAs auf der gleichen Origin (github.io ist shared origin!).
8. `icon.svg` + `icon-maskable.svg` (Maskable: 80% Safe-Zone — Inhalt zwischen ~10% und 90% beider Achsen, Hintergrund vollflächig ohne `rx`)
9. In Root-`index.html` die Spielkarte ergänzen
10. Lokal testen: `python -m http.server 8000` → DevTools → Application prüfen
11. **Code-Review** (code-reviewer Agent) → Pflicht-Fixes umsetzen → re-review wenn nötig
12. **Bei jeder Code-Änderung am Spiel: SW-Cache-Version bumpen** (v1 → v2 → ...). Sonst zeigt der Browser tagelang die alte Version aus dem Cache.
13. Commit + push. Hard-Reload-Hinweis (`Strg+Shift+R`) wenn jemand schon die alte Version im Browser hat.

## Häufige Fallstricke

Aus echten Reviews aufgetaucht — beim Bauen drauf achten:

- **rAF-Loop-Akkumulation:** mehrfaches `startLoop` ohne `cancelAnimationFrame` → mehrere Loops parallel, State-Korruption. Lösung: `loopHandle`-Variable + `cancelAnimationFrame(loopHandle)` vor neuem rAF, am Loop-Ende `if (state.running) loopHandle = requestAnimationFrame(loop)`.
- **Tap-Race bei verzögerten Aktionen:** zwischen Tap und delayed-State-Mutation kann ein zweiter Tap reinkommen → State doppelt verändert. Lösung: `gate.passed`-Flag *vor* jeder State-Mutation prüfen UND setzen.
- **Fade-Race mit display:none:** wenn ein Element gefadet wird und parallel ein anderer Code-Pfad es auf `display:none` setzt, wird der Fade unsichtbar. Lösung: vorheriges Element nicht sofort verstecken, Fade erst durchlaufen lassen.
- **Sammlung-vs-Spiel-SW-Scope:** Sammlung-SW (Scope `/Lernspiele/`) muss Spiel-Pfade (`/Lernspiele/<spiel>/...`) an die Spiel-SWs delegieren. Filter im fetch-Handler: `if (rel.includes('/')) return;` (rel = pathname nach swScope).
- **Naming `state.running` vs `setRunning`:** wenn beides existiert, leicht zu verwechseln. State-Flag und CSS-Toggle-Funktion klar unterschiedlich benennen (z.B. `state.running` + `setFiguresAnimating`).
- **Belohnungs-Sprache im End-Screen:** "richtig", "geschafft", "X daneben" sind Bewertungssprache. Lieber warm formulieren ohne Wettbewerbs-Vokabular ("genau!", "magst du nochmal probieren?").

## Roadmap (Phasen)

### Phase 1 — PWA + GitHub Pages ✓ (abgeschlossen 2026-05-02)
- Monorepo-Struktur ✓
- Buchstaben-Spiel als PWA ✓
- Zahlen-Parade als PWA ✓
- Sammlung selbst als PWA mit Install-Banner (Android: `beforeinstallprompt`, iOS: Anleitung) ✓
- GitHub Pages live: https://breuerchristian.github.io/Lernspiele/ ✓

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
- Keine Bewertungs-Sprache im End-Screen ("X daneben", "leider falsch") — warm formulieren ohne Wettbewerbs-Vokabular
- Keine Schnörkel-/Cursive-Schriften (Comic Sans, Chalkboard) — Kinder lesen sie schwer
