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
├── _lib/                ← geteilte Ressourcen (Audio + Icon-Sammlung)
│   ├── audio.js         ← Lernspiele.Audio.{correct,wrong,tap,tone,sequence}
│   ├── icons/           ← Spiel-Icons als Source-of-Truth (.svg-Einzeldateien)
│   ├── icons/INDEX.json ← Auflistung aller Icons mit Kategorie + Verwendung
│   ├── icons-gallery.html ← Browser-Review-Seite
│   └── README.md        ← SVG-Stilrichtlinie + Marker-Pattern
├── _templates/
│   └── new-game/        ← Vorlage fuer neue Spiele (alle Standard-Patterns)
├── scripts/
│   ├── scaffold-game.sh ← bash scripts/scaffold-game.sh <id> "Name" "#hex"
│   ├── update-icons.js  ← (geplant) Icon-Updates in alte Spiele propagieren
│   └── verify-icons.js  ← (geplant) Konsistenz-Check
└── <spiel>/             ← jedes Spiel als eigenständige PWA
    ├── index.html
    ├── manifest.json    ← scope: "./", start_url: "./"
    ├── service-worker.js
    ├── icon.svg
    └── icon-maskable.svg
```

Eltern installieren *eine* App (die Sammlung), beide/alle Spiele sind drin. Einzelne
Spiele werden laut Distributions-Strategie nicht als separate PWAs installiert —
die Sammlung-PWA deckt alles ab.

Aktuell vorhandene Spiele: `buchstaben/`, `zahlen-parade/`, `hauptstaedte-lernen/`, `uhr-lesen/`, `was-passt-nicht/`, `schatten-finden/`, `tier-geraeusche/`, `jahreszeiten-sortieren/`, `muster-fortsetzen/`, `mengen-erfassen/`, `zahlenreihen/`, `symmetrie/`, `farben-mischen/`, `muenzen/`, `plus-tuermchen/`, `silben-klatschen/`, `anlaute/`, `reim-paare/`, `wort-bild/`, `englisch-erste-woerter/`, `bundeslaender/`, `flaggen/`, `planeten/`

## Leitprinzipien (NICHT verhandelbar)

- **Keine Werbung.** Nie. Nirgends.
- **Keine Tracker / Analytics / Telemetrie.** Kein GA, kein Plausible, kein Sentry, kein Pixel.
- **Keine externen CDNs.** Keine Google Fonts, kein jsDelivr, kein cdnjs. Alle Assets liegen lokal im Repo. Grund: kein Datenabfluss, vollständige Offline-Fähigkeit, keine Abhängigkeit von Drittparteien die ihrerseits tracken könnten.
- **Keine In-App-Käufe, keine Engagement-Hooks.** Montessori-Ansatz: Spiel endet wenn das Kind fertig ist, nicht wenn der nächste Belohnungs-Loop greift. Keine Streaks, keine Push-Notifications, kein "spiel weiter um X freizuschalten".
- **Lokal-first.** Spielstände (falls überhaupt) im LocalStorage. Kein Account, kein Login, kein Backend.
- **Open Source auf GitHub.** Andere Eltern sollen es nutzen, forken, anpassen können.

## Tech-Stack

- Vanilla HTML/CSS/JS, single-file pro Spiel wo möglich
- Keine Build-Tools, keine npm-Dependencies
- Web Audio API für Sounds — geteilter Helper unter `_lib/audio.js`
- LocalStorage für Persistenz, Keys mit Spielname-Präfix (z.B. `zahlen-parade-prefs`)
- Pro Spiel: eigener Service Worker mit Scope auf den jeweiligen Unterordner
- **Schrift:** `'Verdana', 'Tahoma', sans-serif` — kein Comic Sans/Cursive (Kinder die Lesen lernen tun sich mit Schnörkelschriften schwer). Verdana ist auf allen Plattformen verfügbar und für Bildschirm designed.

## Standardisierte Patterns (verbindlich für neue Spiele)

Bei den ersten Spielen wurden viele Patterns ad-hoc gebaut. Ab jetzt sind sie
verbindlich, damit über alle Spiele hinweg visuelle und akustische
Wiedererkennung entsteht.

### `_lib/audio.js` — Sound-Vokabular

Statt eigener `tone()`-Funktionen den geteilten Helper nutzen:

```html
<script src="../_lib/audio.js"></script>
<script>
  document.addEventListener('pointerdown', Lernspiele.Audio.ensure, { once: true });
  // ...
  if (richtig) Lernspiele.Audio.correct();
  else         Lernspiele.Audio.wrong();
</script>
```

Verbindliche Sound-Bedeutungen:
- `correct()` — richtige Antwort (660→880 Hz, sine)
- `wrong()` — falsche Antwort (220→180 Hz, triangle)
- `tap()` — generischer Tap-Feedback (440 Hz, 60 ms)

Eigene Töne für Spielmechanik (zählen, stapeln, fliegen) sind erlaubt — über
`Lernspiele.Audio.tone(freq, dur, vol, type)` oder `sequence([...])`.

### `_lib/icons/` — Spiel-Icons als Source-of-Truth

Wiederkehrende Spiel-Inhalte (Tiere, Pflanzen, Haushalt, Verkehr) liegen als
Einzel-`.svg`-Dateien in `_lib/icons/`. Stilrichtlinie und Marker-Pattern siehe
[_lib/README.md](_lib/README.md).

Beim Einbinden in ein Spiel gilt das Marker-Pattern:

```javascript
const ICONS = {
  // ICON:kuh START
  kuh: `<svg viewBox="0 0 200 200">...</svg>`,
  // ICON:kuh END
};
```

Damit kann `scripts/update-icons.js` Icon-Updates in alle nutzenden Spiele
propagieren.

### CSS-Custom-Properties für Theme-Color

Statt Hex-Werte überall im CSS hart zu codieren, im `:root` definieren und
im ganzen Spiel `var(--color-primary)` etc. nutzen:

```css
:root {
  --color-primary: #764ba2;
  --color-light:   #e0d0ed;
  --color-dark:    #4a2a6a;
  --color-bg:      #f7f3fa;
}
```

Manifest-`theme_color` und Meta-Tag müssen mit `--color-primary` übereinstimmen.

### HUD-Layout (Game-Screen)

Drei feste Zonen, Klassen wie unten benannt:

```html
<div class="hud">
  <span class="stage" id="hud-stage">Leicht</span>
  <span class="progress" id="hud-progress">Aufgabe 3/10</span>
  <button class="hud-btn" id="hud-close" aria-label="Spiel beenden">×</button>
</div>
```

- links: Stufe / Modus
- Mitte: Progress als Pill (`Aufgabe X/N`)
- rechts: ×-Button (44×44 px), führt zurück zum Start-Screen

### End-Screen-Buttons (verbindlicher Wortlaut)

- Primary: **„Nochmal spielen"** — gleiche Konfiguration neu starten
- Secondary: **„Andere Stufe"** — zurück zum Start-Screen
- Tertiary: **„Zur Übersicht"** — `<a href="../">`

### Standard-Animationen

```css
@keyframes correct-pulse {
  0%, 100% { transform: scale(1); }
  50%      { transform: scale(1.12); }
}
@keyframes wrong-wiggle {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-6px); } 40% { transform: translateX(6px); }
  60% { transform: translateX(-4px); } 80% { transform: translateX(4px); }
}
@keyframes fade-in { from { opacity: 0; } to { opacity: 1; } }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

### LocalStorage-Konvention

```javascript
const PREFS_KEY = GAME_ID + '-prefs';
function loadPrefs() { try { return JSON.parse(localStorage.getItem(PREFS_KEY)) || {}; } catch (e) { return {}; } }
function savePrefs(p) { try { localStorage.setItem(PREFS_KEY, JSON.stringify(p)); } catch (e) {} }
```

### A11y-Basics

- `aria-label` auf allen Icon-Buttons (×, Pause, Lautsprecher, …)
- Sichtbare Focus-Outline: `button:focus-visible { outline: 3px solid var(--color-primary); outline-offset: 2px; }`
- `prefers-reduced-motion` respektieren (siehe oben)
- Tap-Targets ≥ 44×44 px

## Neues Spiel hinzufügen — Checkliste

**0. Vor dem Codieren (Plan-Pitch).** Konzept in 5-7 Sätzen vorstellen + Nutzer-Bestätigung einholen. Modi, Stufen, Steuerung früh klären. Bei Vorbild-Spielen: Anti-Patterns identifizieren (was raus muss um Montessori-konform zu sein — Wettbewerb, Zeitdruck, Belohnungs-Loops, manipulative Sounds).

1. **Scaffolden:** `bash scripts/scaffold-game.sh <id> "<Game Name>" "#hex"`
   → erzeugt `<id>/` aus `_templates/new-game/` mit allen Standard-Patterns,
   helle/dunkle Farb-Varianten werden aus dem Primär-Hex berechnet.
2. Spiel-Logik im `<script>`-Block am Ende der `index.html` ersetzen
   (das Demo-Spiel "Tippe auf die richtige Farbe" rauswerfen).
3. Eigene Icons (`icon.svg`, `icon-maskable.svg`) zeichnen
   (Maskable: 80% Safe-Zone — Inhalt zwischen ~10% und 90% beider Achsen,
   Hintergrund vollflächig ohne `rx`).
4. Wenn Spiel-Inhalt-Icons gebraucht werden: erst `_lib/icons/` prüfen, dann
   neue per Marker-Pattern (`// ICON:<name> START/END`) einbauen und in
   `_lib/icons/INDEX.json` registrieren. Stil siehe [_lib/README.md](_lib/README.md).
5. In Wurzel-`index.html` die Spielkarte ergänzen.
6. Wurzel-`service-worker.js`: Cache-Version bumpen
   (`lernspiele-landing-vXX` → `vXX+1`), neue `_lib/`-Pfade in `ASSETS` ergänzen
   wenn weitere Lib-Dateien hinzugekommen sind.
7. Lokal testen: `python -m http.server 8000` → DevTools → Application prüfen
   (Manifest erkannt, SW registriert, Audio-Lib geladen).
8. **Code-Review** (code-reviewer Agent) → Pflicht-Fixes umsetzen → re-review
   wenn nötig.
9. Commit + push. Hard-Reload-Hinweis (`Strg+Shift+R`) wenn jemand schon die
   alte Version im Browser hat.

**Bei jeder Code-Änderung am Spiel:** SW-Cache-Version bumpen (v1 → v2 → ...).
Sonst zeigt der Browser tagelang die alte Version aus dem Cache.

## Häufige Fallstricke

Aus echten Reviews aufgetaucht — beim Bauen drauf achten:

- **rAF-Loop-Akkumulation:** mehrfaches `startLoop` ohne `cancelAnimationFrame` → mehrere Loops parallel, State-Korruption. Lösung: `loopHandle`-Variable + `cancelAnimationFrame(loopHandle)` vor neuem rAF, am Loop-Ende `if (state.running) loopHandle = requestAnimationFrame(loop)`.
- **Tap-Race bei verzögerten Aktionen:** zwischen Tap und delayed-State-Mutation kann ein zweiter Tap reinkommen → State doppelt verändert. Lösung: `gate.passed`-Flag *vor* jeder State-Mutation prüfen UND setzen.
- **Fade-Race mit display:none:** wenn ein Element gefadet wird und parallel ein anderer Code-Pfad es auf `display:none` setzt, wird der Fade unsichtbar. Lösung: vorheriges Element nicht sofort verstecken, Fade erst durchlaufen lassen.
- **Sammlung-vs-Spiel-SW-Scope:** Sammlung-SW (Scope `/Lernspiele/`) muss Spiel-Pfade (`/Lernspiele/<spiel>/...`) an die Spiel-SWs delegieren. Filter im fetch-Handler: `if (rel.includes('/')) return;` (rel = pathname nach swScope).
- **Naming `state.running` vs `setRunning`:** wenn beides existiert, leicht zu verwechseln. State-Flag und CSS-Toggle-Funktion klar unterschiedlich benennen (z.B. `state.running` + `setFiguresAnimating`).
- **Belohnungs-Sprache im End-Screen:** "richtig", "geschafft", "X daneben" sind Bewertungssprache. Lieber warm formulieren ohne Wettbewerbs-Vokabular ("genau!", "magst du nochmal probieren?").
- **SVG-Rotation auf `<line>` mit `transform-box: fill-box`:** wackelig in einigen Browsern, weil eine vertikale/horizontale Linie eine Null-Breite/Höhe-Bounding-Box hat und `50% 100%`-Origin dann nicht überall sauber auflöst. Lösung: `transform-box: view-box` + Pixel-Koordinaten im viewBox-System (z.B. `transform-origin: 100px 100px` bei viewBox 0 0 200 200). Gilt analog für `<g>`-Wrapper.

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
