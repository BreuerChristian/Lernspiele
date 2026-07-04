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
├── IDEEN.md             ← Spiel-Ideen-Backlog ([ ] offen, [x] live, [-] verworfen)
├── LICENSE              ← MIT
├── .nojekyll            ← GitHub Pages: kein Jekyll-Processing
├── index.html           ← Landing (selbst PWA: Sammlung-App)
├── manifest.json        ← Sammlung-PWA, scope: "./" deckt alle Spiele
├── service-worker.js    ← cache-first, filtert Unterordner an Spiel-SWs
├── icon.svg
├── icon-maskable.svg
├── _lib/                ← geteilte Ressourcen (Audio + Icon-Sammlung)
│   ├── audio.js         ← Lernspiele.Audio.{correct,wrong,tap,tone,sequence}
│   ├── icons/           ← 178 Spiel-Icons (ueberw. OpenMoji CC-BY-SA 4.0)
│   ├── icons/INDEX.json ← Auflistung mit Kategorie + Quelle + verwendet-in
│   ├── icons/NOTICE.md  ← Attribution + Codepoint-Tabelle
│   ├── icons/LICENSE-OPENMOJI.md ← Lizenz-Erklaerung
│   ├── icons-gallery.html ← Browser-Review-Seite (Filter + 24/64/128px + Schatten)
│   └── README.md        ← SVG-Stilrichtlinie + Marker-Pattern
├── _templates/
│   └── new-game/        ← Vorlage fuer neue Spiele (alle Standard-Patterns)
├── scripts/
│   ├── scaffold-game.sh ← bash scripts/scaffold-game.sh <id> "Name" "#hex"
│   ├── check-spiele.py  ← Linter: alle Spiele gegen die Regeln hier pruefen
│   ├── icons.py         ← Subkommandos: extract / discover / update / verify
│   ├── download-openmoji.py ← OpenMoji-SVGs nach _lib/icons/ holen
│   ├── cleanup-icons.py ← One-Shot-Aufraeumen (Englisch->Deutsch, etc.)
│   ├── extract-manifest.json    ← Welche SVGs aus welchen Spielen ziehen
│   ├── openmoji-manifest.json   ← Welche Codepoints in die Lib
│   └── discover-manifest.json   ← Auto-generiert von `discover --write-manifest`
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

Aktuell 49 Spiele (Stand 2026-07): jeder Wurzel-Ordner außer `_lib/`, `_templates/`
und `scripts/` ist ein Spiel. Vollständige, aktuelle Liste: `python scripts/check-spiele.py`
(erste Zeile) oder Blick in die Kategorien der Wurzel-`index.html`. Der Backlog mit
Live-Status pro Idee liegt in [IDEEN.md](IDEEN.md).

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

Bei den ersten Spielen wurden viele Patterns ad-hoc gebaut; inzwischen sind die
Altbestände per Standards-Migration nachgezogen (CSS-Vars, a11y, `_lib/audio.js`).
Für alle Spiele verbindlich, damit über die Sammlung hinweg visuelle und
akustische Wiedererkennung entsteht — `scripts/check-spiele.py` prueft das
automatisch (siehe unten).

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

178 Icons in `_lib/icons/`, ueberwiegend aus **OpenMoji** (CC-BY-SA 4.0,
siehe [_lib/icons/NOTICE.md](_lib/icons/NOTICE.md)). 9 Spiele nutzen bereits
das Marker-Pattern: anlaute, was-passt-nicht, jahreszeiten-sortieren,
englisch-erste-woerter, reim-paare, flaggen, wort-bild, schatten-finden,
oberbegriffe. Welche Spiele Marker haben: `grep -l "ICON:" */index.html`.

**Galerie-Browser:** `python -m http.server 8000` im Repo-Wurzel, dann
http://localhost:8000/_lib/icons-gallery.html — zeigt alle Icons mit
Filter, 24/64/128 px + Silhouette, Such-Feld.

**Marker-Pattern in Spielen:**

```javascript
const ICONS = {
  // ICON:kuh START
  kuh: `<svg viewBox="0 0 72 72">...</svg>`,
  // ICON:kuh END
};
```

**Workflow:**

| Aufgabe | Befehl |
|---|---|
| Icon-Inhalt in der Lib aendern und in alle nutzenden Spiele propagieren | `python scripts/icons.py update` (bumpt SW-Cache automatisch) |
| Konsistenz pruefen (Marker-Paare, fehlende Lib-Files, INDEX vs FS) | `python scripts/icons.py verify` |
| Neue Spiele scannen, Icon-Kandidaten finden | `python scripts/icons.py discover --write-manifest` |
| Icons aus existierenden Spielen extrahieren (4 Patterns A/B/C/D) | `python scripts/icons.py extract --manifest <pfad>` |
| OpenMoji-Codepoints nachladen | `python scripts/download-openmoji.py` |

**Lizenz-Hinweis:** Bei Modifikation eines OpenMoji-Icons im SVG-Header
einen Kommentar setzen (`<!-- Modified from OpenMoji XXXX (CC BY-SA 4.0) -->`)
und das geaenderte Icon bleibt unter CC BY-SA 4.0. Der Repo-Code ist MIT
und davon unbeeinflusst (siehe [_lib/icons/LICENSE-OPENMOJI.md](_lib/icons/LICENSE-OPENMOJI.md)).

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

### `scripts/check-spiele.py` — Regel-Linter

Prueft alle Spiele automatisch gegen die Regeln in dieser Datei:

```bash
python scripts/check-spiele.py
```

- **ERROR** = Leitprinzip-Verletzung (externe URLs/CDNs, Tracker, Cursive-Fonts,
  `Lernspiele.Audio` ohne eingebundene Lib) → Exit-Code 1, muss gefixt werden
- **WARN** = Standard-Drift (HUD-Klassen fehlen, End-Screen-Wortlaut, kein
  `--color-primary`, LocalStorage-Key ohne Praefix, SW-Cache-Name ohne Spiel-Praefix)
- **INFO** = optional (fehlende Standard-Animationen, Wortlaut-Varianten)

Vor jedem Commit laufen lassen; neue ERRORs sind nicht verhandelbar.

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
4. Wenn Spiel-Inhalt-Icons gebraucht werden: erst Galerie ansehen
   (`http://localhost:8000/_lib/icons-gallery.html`). Wenn das passende Icon
   schon da ist → mit `// ICON:<name> START/END` umrahmen und SVG-Inhalt aus
   `_lib/icons/<name>.svg` einsetzen. Wenn nicht da → entweder neuen
   OpenMoji-Codepoint in `scripts/openmoji-manifest.json` ergänzen und
   `python scripts/download-openmoji.py` laufen lassen, oder eigenes SVG
   anlegen + INDEX.json-Eintrag (Stil siehe [_lib/README.md](_lib/README.md)).
   Konsistenz prüfen: `python scripts/icons.py verify`.
5. In Wurzel-`index.html` die Spielkarte in der passenden Kategorie ergänzen —
   Markup: `<a class="game-card" href="<id>/" data-age-min="X" data-age-max="Y">`
   mit `<img class="preview" src="<id>/icon.svg" alt="">` + Name + `<span class="desc">`.
   Die `data-age-*`-Attribute speisen den Altersfilter der Landing.
6. Wurzel-`service-worker.js`: Cache-Version bumpen
   (`lernspiele-landing-vXX` → `vXX+1`), neue `_lib/`-Pfade in `ASSETS` ergänzen
   wenn weitere Lib-Dateien hinzugekommen sind.
7. Lokal testen: `python -m http.server 8000` → DevTools → Application prüfen
   (Manifest erkannt, SW registriert, Audio-Lib geladen).
8. **Linter:** `python scripts/check-spiele.py` — keine neuen ERRORs, WARNs im
   neuen Spiel fixen.
9. **Code-Review** (code-reviewer Agent) → Pflicht-Fixes umsetzen → re-review
   wenn nötig.
10. In `IDEEN.md` die Idee auf `[x]` setzen (bzw. eintragen falls sie dort fehlt).
11. Commit + push. Hard-Reload-Hinweis (`Strg+Shift+R`) wenn jemand schon die
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
