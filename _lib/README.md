# `_lib/` — Geteilte Ressourcen für alle Lernspiele

Dieses Verzeichnis enthält Code und Assets, die über mehrere Spiele hinweg
genutzt werden. Ziel: **visuelle Wiedererkennung** (ein Kuh-Icon sieht in jedem
Spiel gleich aus) und **weniger Boilerplate** beim Bauen neuer Spiele.

## Inhalt

| Datei | Zweck |
|---|---|
| `audio.js` | Web Audio Helper (`Lernspiele.Audio.correct/wrong/tap/tone/sequence`) |
| `icons/*.svg` | Spiel-Icons als Source-of-Truth (eine Datei pro Icon) |
| `icons/INDEX.json` | Auflistung aller Icons mit Kategorie + Verwendung |
| `icons-gallery.html` | Browser-Review-Seite zum Sichten aller Icons |
| `README.md` | dieses Dokument |

## Audio-Helper

```html
<script src="../_lib/audio.js"></script>
<script>
  document.addEventListener('pointerdown', Lernspiele.Audio.ensure, { once: true });
  // …
  if (richtig) Lernspiele.Audio.correct();
  else         Lernspiele.Audio.wrong();
</script>
```

Sound-Vokabular (verbindlich):

- `correct()` — 660→880 Hz, sine, ~0.4 s. Wird bei jeder richtigen Antwort gespielt.
- `wrong()` — 220→180 Hz, triangle, ~0.4 s. Wird bei jeder falschen Antwort gespielt.
- `tap()` — 440 Hz, 60 ms, sine. Generischer Tap-Feedback-Ton.

Eigene Töne für Spielmechanik (zählen, stapeln, fliegen) sind erlaubt — über
`Lernspiele.Audio.tone(freq, dur, vol, type)` oder `sequence([...])`.

## SVG-Icons — Stilrichtlinie

Alle Icons in `_lib/icons/` folgen denselben Regeln, damit sie im Spiel beliebig
kombinierbar sind und in `schatten-finden` als Silhouette funktionieren.

### Pflicht-Regeln

1. **ViewBox** einheitlich `0 0 200 200`.
2. **Outline-Stil** mit `stroke-width: 3` für Hauptkonturen, `stroke-width: 1.5` für Details.
3. **Farbflächen mit klarer Kante** — kein `<linearGradient>`, kein `<radialGradient>`.
   Grund: Silhouetten-Konvertierung in `schatten-finden` (CSS-Filter setzt alles
   auf eine Farbe) bricht bei Verläufen optisch.
4. **Keine `<defs>`-IDs** im SVG. Wenn mehrere Icons inline auf der gleichen
   Seite landen, kollidieren IDs. Stattdessen direkt auf den Pfaden definieren.
5. **Keine externen Referenzen** (kein `xlink:href` zu externen Dateien).
6. **Datei-Namen**: deutsche Bezeichnung, lowercase, **ohne Umlaute**:
   - `kuh.svg`, `apfel.svg`, `baer.svg` (nicht `bär.svg`)
   - `tier-haus.svg` (Bindestrich für mehrteilige Namen)

### Empfohlen

- Außenkontur deckend gefüllt, keine ausgesparten Innenflächen — sonst sieht
  die Silhouette löchrig aus.
- Augen / Münder / Details als separate Pfade *innerhalb* der Außenkontur.
- Farb-Palette: warm und kindgerecht. Vermeide Neon-Farben und reines Schwarz
  (`#1a1a1a` statt `#000` für Linien wirkt weicher).
- Maximal ~6 Pfade pro Icon (für Dateigröße + Render-Performance).

### Minimal-Beispiel

```svg
<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <!-- Apfel-Korpus -->
  <path d="M100 60 C 70 60 50 80 50 110 C 50 150 80 180 100 180
           C 120 180 150 150 150 110 C 150 80 130 60 100 60 Z"
        fill="#e74c3c" stroke="#a83227" stroke-width="3"/>
  <!-- Stiel -->
  <path d="M100 60 C 100 40 110 28 124 26"
        fill="none" stroke="#7d4f1d" stroke-width="5" stroke-linecap="round"/>
  <!-- Blatt -->
  <ellipse cx="115" cy="38" rx="14" ry="9"
           fill="#5fa867" stroke="#3d7a3d" stroke-width="1.5"
           transform="rotate(-25 115 38)"/>
</svg>
```

## Marker-Pattern in Spielen

Damit `scripts/update-icons.js` ein Icon-Update in alle nutzenden Spiele
propagieren kann, muss jedes inline eingebettete Icon mit Markern umrahmt sein:

```javascript
const ICONS = {
  // ICON:kuh START
  kuh: `<svg viewBox="0 0 200 200">…</svg>`,
  // ICON:kuh END

  // ICON:hund START
  hund: `<svg viewBox="0 0 200 200">…</svg>`,
  // ICON:hund END
};
```

Das Update-Skript scannt rekursiv alle `index.html`-Dateien, findet die
Marker-Paare, ersetzt den Inhalt mit dem aktuellen Stand aus
`_lib/icons/<name>.svg`, und bumpt anschließend die Cache-Version aller
betroffenen `service-worker.js`-Dateien.

**Wichtig:** Marker müssen exakt diesem Format folgen — `// ICON:<name> START`
und `// ICON:<name> END`. Kein Leerzeichen vor oder hinter dem Doppelpunkt.

## Service-Worker-Caching

`_lib/audio.js` und `_lib/icons/*.svg` werden vom **Sammlung-Service-Worker**
(Wurzel-`service-worker.js`) gecacht — nicht von den einzelnen Spiel-SWs, weil
diese nur ihren eigenen Unterordner abdecken können.

Bei Änderungen an `_lib/` immer:
1. neue Pfade in der Wurzel-`service-worker.js` zu `ASSETS` hinzufügen
2. dort den Cache-Namen bumpen (`lernspiele-landing-v13` → `v14`)

Einzelne Spiele werden laut Distributions-Strategie nur über die Sammlung-PWA
installiert — die Sammlung-SW deckt also alles ab.
