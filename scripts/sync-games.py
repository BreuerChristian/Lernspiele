#!/usr/bin/env python3
"""sync-games.py - Landing, SW-Cache-Version und Spielzahl aus einer Quelle.

Beseitigt die manuellen, konflikttraechtigen Schritte beim Hinzufuegen eines
Spiels. Quelle der Wahrheit ist `games.json` (Kategorien -> Spiele mit Titel,
Beschreibung, Alter). Generiert daraus:
  - die Spielkarten in index.html (zwischen <!-- GAMES:AUTO START/END -->)
  - bumpt die Root-SW-Cache-Version (lernspiele-landing-vNN) bei Aenderung
  - aktualisiert die Spielzahl in README.md und CLAUDE.md

Subkommandos:
  extract   games.json aus dem aktuellen index.html erzeugen + Marker einsetzen
            (einmaliger Bootstrap; danach ist games.json die Quelle)
  apply     games.json -> index.html/SW/Doku schreiben  (Default)
  --check   nur pruefen, ob alles in sync ist (CI). Exit 1 bei Drift.

Workflow neues Spiel:  Ordner scaffolden -> Eintrag in games.json -> `sync-games.py`
"""
import html
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INDEX = REPO / 'index.html'
SW = REPO / 'service-worker.js'
GAMES_JSON = REPO / 'games.json'
README = REPO / 'README.md'
CLAUDE = REPO / 'CLAUDE.md'

MARK_START = '<!-- GAMES:AUTO START -->'
MARK_END = '<!-- GAMES:AUTO END -->'

SECTION_RE = re.compile(r'<section class="cat-section">.*?</section>', re.S)
H2_RE = re.compile(r'<h2 class="cat">(.*?)</h2>', re.S)
CARD_RE = re.compile(
    r'<a class="game-card" href="([^"]+?)/" data-age-min="(\d+)" data-age-max="(\d+)">\s*'
    r'<img class="preview"[^>]*>\s*'
    r'<span class="text">(.*?)\s*<span class="desc">(.*?)</span>\s*</span>\s*</a>',
    re.S,
)


# ---------- extract ----------
def extract():
    content = INDEX.read_text(encoding='utf-8')
    cats = []
    for sec in SECTION_RE.findall(content):
        h2 = H2_RE.search(sec)
        if not h2:
            continue
        name = html.unescape(h2.group(1).strip())
        games = []
        for folder, amin, amax, title, desc in CARD_RE.findall(sec):
            games.append({
                'folder': folder,
                'title': html.unescape(title.strip()),
                'desc': html.unescape(desc.strip()),
                'ageMin': int(amin),
                'ageMax': int(amax),
            })
        cats.append({'name': name, 'games': games})

    total = sum(len(c['games']) for c in cats)
    GAMES_JSON.write_text(json.dumps({'categories': cats}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'games.json geschrieben: {len(cats)} Kategorien, {total} Spiele.')

    # Marker einsetzen, falls noch nicht vorhanden
    if MARK_START not in content:
        secs = list(SECTION_RE.finditer(content))
        if secs:
            first, last = secs[0].start(), secs[-1].end()
            indent = '        '
            new = (content[:first] + MARK_START + '\n' + indent
                   + content[first:last] + '\n' + indent + MARK_END + content[last:])
            INDEX.write_text(new, encoding='utf-8')
            print('Marker in index.html eingesetzt.')
    return 0


# ---------- generieren ----------
def render_cards():
    data = json.loads(GAMES_JSON.read_text(encoding='utf-8'))
    out = []
    for cat in data['categories']:
        out.append('        <section class="cat-section">')
        out.append(f'            <h2 class="cat">{html.escape(cat["name"], quote=False)}</h2>')
        out.append('            <nav class="games">')
        for g in cat['games']:
            title = html.escape(g['title'], quote=False)
            desc = html.escape(g['desc'], quote=False)
            out.append(f'                <a class="game-card" href="{g["folder"]}/" '
                       f'data-age-min="{g["ageMin"]}" data-age-max="{g["ageMax"]}">')
            out.append(f'                    <img class="preview" src="{g["folder"]}/icon.svg" alt="">')
            out.append(f'                    <span class="text">{title}')
            out.append(f'                        <span class="desc">{desc}</span>')
            out.append('                    </span>')
            out.append('                </a>')
        out.append('            </nav>')
        out.append('        </section>')
        out.append('')  # Leerzeile zwischen Kategorien (wie im Original)
    if out and out[-1] == '':
        out.pop()
    return '\n'.join(out)


def total_games():
    data = json.loads(GAMES_JSON.read_text(encoding='utf-8'))
    return sum(len(c['games']) for c in data['categories'])


def build_index():
    content = INDEX.read_text(encoding='utf-8')
    if MARK_START not in content or MARK_END not in content:
        raise SystemExit('FEHLER: Marker fehlen in index.html — erst `sync-games.py extract` ausfuehren.')
    indent = '        '
    # render_cards() bringt die 8-Space-Einrueckung selbst mit — kein Praefix davor.
    block = f'{MARK_START}\n{render_cards()}\n{indent}{MARK_END}'
    return re.sub(re.escape(MARK_START) + r'.*?' + re.escape(MARK_END), lambda m: block, content, flags=re.S)


def bump_sw(current_sw):
    m = re.search(r"lernspiele-landing-v(\d+)", current_sw)
    if not m:
        return current_sw, None
    old = int(m.group(1))
    return re.sub(r"lernspiele-landing-v\d+", f"lernspiele-landing-v{old + 1}", current_sw, count=1), old + 1


def update_counts(text, n):
    # NUR die klar identifizierbaren Zaehler ersetzen — kein blindes "\d+ Spiele"
    # (sonst werden Stellen wie "9 Spiele nutzen das Marker-Pattern" oder
    #  "2-3 Spiele" faelschlich ueberschrieben).
    text = re.sub(r'\b\d+ Spiele, sortiert nach', f'{n} Spiele, sortiert nach', text)
    text = re.sub(r'weitere \d+ Spiele nach gleichem Muster',
                  f'weitere {n - 1} Spiele nach gleichem Muster', text)
    text = re.sub(r'Aktuell \d+ Spiele \(Stand', f'Aktuell {n} Spiele (Stand', text)
    return text


# ---------- apply / check ----------
def apply(check_only=False):
    n = total_games()
    changes = []

    new_index = build_index()
    if new_index != INDEX.read_text(encoding='utf-8'):
        changes.append('index.html (Spielkarten)')
        if not check_only:
            INDEX.write_text(new_index, encoding='utf-8')

    sw = SW.read_text(encoding='utf-8')
    # SW nur bumpen, wenn index.html sich aendert (neuer Inhalt -> Clients refreshen)
    if 'index.html (Spielkarten)' in changes:
        new_sw, ver = bump_sw(sw)
        if new_sw != sw:
            changes.append(f'service-worker.js (Cache -> v{ver})')
            if not check_only:
                SW.write_text(new_sw, encoding='utf-8')

    for path, label in [(README, 'README.md'), (CLAUDE, 'CLAUDE.md')]:
        t = path.read_text(encoding='utf-8')
        nt = update_counts(t, n)
        if nt != t:
            changes.append(f'{label} (Spielzahl -> {n})')
            if not check_only:
                path.write_text(nt, encoding='utf-8')

    if check_only:
        if changes:
            print('NICHT in sync — `python scripts/sync-games.py` ausfuehren:')
            for c in changes:
                print(f'  - {c}')
            return 1
        print(f'In sync ({n} Spiele).')
        return 0

    if changes:
        print(f'Aktualisiert ({n} Spiele):')
        for c in changes:
            print(f'  - {c}')
    else:
        print(f'Bereits in sync ({n} Spiele).')
    return 0


def main():
    args = sys.argv[1:]
    if args and args[0] == 'extract':
        return extract()
    if '--check' in args:
        return apply(check_only=True)
    return apply(check_only=False)


if __name__ == '__main__':
    sys.exit(main())
