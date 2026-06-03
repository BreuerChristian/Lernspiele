#!/usr/bin/env python3
"""
check-spiele.py - Pruefe alle Spiele gegen die globalen Regeln aus CLAUDE.md.

Pro Spiel werden mehrere Checks ausgefuehrt und Findings als Liste ausgegeben.
Severity:
  ERROR   - Leitprinzip-Verletzung (Werbung, Tracker, CDN, externe Fonts)
  WARN    - Standard-Drift (HUD-Klasse fehlt, End-Screen-Wortlaut nicht Standard)
  INFO    - Optional (Hint)
"""
from __future__ import annotations
import re
import sys
from pathlib import Path
from collections import defaultdict

REPO = Path(__file__).resolve().parent.parent

EXCLUDE_DIRS = {'_lib', '_templates', 'scripts', '.git', '.claude', 'node_modules'}


def find_spiele() -> list[str]:
    out = []
    for d in REPO.iterdir():
        if d.is_dir() and d.name not in EXCLUDE_DIRS and not d.name.startswith('.'):
            if (d / 'index.html').exists():
                out.append(d.name)
    return sorted(out)


def check_spiel(spiel: str) -> list[tuple[str, str]]:
    """Returnt Liste (severity, message)."""
    findings = []
    html = REPO / spiel / 'index.html'
    if not html.exists():
        return [('ERROR', 'index.html fehlt')]
    content = html.read_text(encoding='utf-8', errors='replace')

    # ===== Leitprinzipien =====
    # 1. Externe URLs / CDNs / Tracker
    forbidden_hosts = [
        'googletagmanager.com', 'google-analytics.com', 'plausible.io',
        'sentry.io', 'cdn.jsdelivr.net', 'cdnjs.cloudflare.com',
        'unpkg.com', 'fonts.googleapis.com', 'fonts.gstatic.com',
        'facebook.com', 'twitter.com',
    ]
    for host in forbidden_hosts:
        if host in content.lower():
            findings.append(('ERROR', f'Externe URL gefunden: {host}'))

    # Externe <link rel="stylesheet">?
    if re.search(r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']https?://', content):
        findings.append(('ERROR', 'Externes <link rel="stylesheet"> mit http(s)://-URL'))

    # Externe <script src>?
    for m in re.finditer(r'<script[^>]+src=["\']([^"\']+)["\']', content):
        src = m.group(1)
        if src.startswith('http://') or src.startswith('https://'):
            findings.append(('ERROR', f'Externes <script src="{src}">'))
        elif src.startswith('//'):
            findings.append(('ERROR', f'Protocol-relative <script src="{src}">'))

    # 2. Schrift muss Verdana/Tahoma sein
    fonts_in_use = set()
    for m in re.finditer(r"font-family\s*:\s*([^;}\n]+)", content):
        fonts_in_use.add(m.group(1).strip().rstrip(';').strip())
    has_verdana = any('verdana' in f.lower() or 'tahoma' in f.lower() for f in fonts_in_use)
    if not has_verdana and fonts_in_use:
        findings.append(('WARN', f"Keine Verdana/Tahoma-Schrift in font-family. Gefunden: {list(fonts_in_use)[:3]}"))
    forbidden_fonts = ['comic sans', 'chalkboard', 'cursive', 'fantasy']
    for f in fonts_in_use:
        for forb in forbidden_fonts:
            if forb in f.lower():
                findings.append(('ERROR', f"Schnoerkel-/Cursive-Schrift: {f}"))

    # ===== Standard-Patterns =====
    # 3. Theme-Color Meta-Tag
    if not re.search(r'<meta\s+name=["\']theme-color["\']', content):
        findings.append(('WARN', 'theme-color Meta-Tag fehlt'))

    # 4. Manifest verlinkt
    if not re.search(r'<link[^>]+rel=["\']manifest["\']', content):
        findings.append(('WARN', '<link rel="manifest"> fehlt'))

    # 5. Service Worker Registrierung
    if 'navigator.serviceWorker.register' not in content:
        findings.append(('WARN', 'Service Worker wird nicht registriert'))

    # 6. Übersicht-Link
    if not re.search(r'href=["\']\.\.\/["\']', content):
        findings.append(('WARN', 'Kein Link zur Übersicht (href="../")'))

    # 7. HUD-Pattern (nur bei Spielen mit screen-game)
    if 'screen-game' in content:
        if 'class="hud"' not in content:
            findings.append(('WARN', 'HUD-Klasse "hud" fehlt im Game-Screen'))
        if 'id="hud-stage"' not in content:
            findings.append(('WARN', 'HUD-Element id="hud-stage" fehlt'))
        if 'id="hud-progress"' not in content:
            findings.append(('WARN', 'HUD-Element id="hud-progress" fehlt'))
        if 'id="hud-close"' not in content:
            findings.append(('WARN', 'HUD-Element id="hud-close" fehlt'))

    # 8. End-Screen-Buttons-Wortlaut
    if 'screen-end' in content:
        if 'Nochmal spielen' not in content:
            findings.append(('WARN', 'End-Screen ohne "Nochmal spielen"-Button'))
        if 'Andere Stufe' not in content and 'Andere Gruppe' not in content and 'Andere Aufgabe' not in content:
            findings.append(('INFO', 'End-Screen ohne "Andere Stufe"-Button (Wortlaut variiert)'))
        if 'Übersicht' not in content and 'Uebersicht' not in content:
            findings.append(('WARN', 'End-Screen ohne "Zur Übersicht"-Button'))

    # 9. audio.js Einbindung
    has_audio_lib = '../_lib/audio.js' in content
    uses_lernspiele_audio = 'Lernspiele.Audio' in content
    if uses_lernspiele_audio and not has_audio_lib:
        findings.append(('ERROR', 'Lernspiele.Audio wird genutzt, aber audio.js nicht eingebunden'))
    # Eigener Audio-Code statt Lib?
    if not has_audio_lib:
        if re.search(r'createOscillator|new\s+AudioContext|webkitAudioContext', content):
            findings.append(('WARN', 'Eigener Web-Audio-Code statt _lib/audio.js'))

    # 10. CSS-Custom-Properties
    if not re.search(r':root\s*\{[^}]*--color-primary', content):
        findings.append(('WARN', 'Kein --color-primary in :root (CSS-Custom-Properties fehlen)'))

    # 11. prefers-reduced-motion
    if 'prefers-reduced-motion' not in content:
        findings.append(('WARN', 'prefers-reduced-motion-Block fehlt'))

    # 12. Standard-Animationen
    has_correct_pulse = 'correct-pulse' in content
    has_wrong_wiggle = 'wrong-wiggle' in content
    if not has_correct_pulse and 'screen-game' in content:
        findings.append(('INFO', 'Keine correct-pulse Animation'))
    if not has_wrong_wiggle and 'screen-game' in content:
        findings.append(('INFO', 'Keine wrong-wiggle Animation'))

    # 13. LocalStorage-Konvention - nur direkte Aufrufe mit String-Literal
    storage_keys = re.findall(r"localStorage\.(?:setItem|getItem|removeItem)\s*\(\s*['\"]([^'\"]+)['\"]", content)
    for k in storage_keys:
        if k.startswith(spiel) or k.startswith('lernspiele-'):
            continue
        findings.append(('WARN', f'LocalStorage-Key "{k}" hat keinen Spiel-/lernspiele-Präfix'))

    # 14. Aria-Labels auf HUD-Close
    if 'id="hud-close"' in content:
        m = re.search(r'id=["\']hud-close["\'][^>]*', content)
        if m and 'aria-label' not in m.group(0):
            findings.append(('INFO', 'hud-close Button ohne aria-label'))

    # 15. Anti-Pattern: Bewertungs-Sprache im End-Screen
    if 'screen-end' in content or 'group-complete' in content:
        bad_words = [
            'leider falsch', 'X daneben', 'leider nicht', 'verloren',
            'streak', 'verbessere dich', 'kein Glück', 'pech',
        ]
        end_section = content.lower()
        for w in bad_words:
            if w.lower() in end_section:
                findings.append(('WARN', f'Bewertungs-Sprache: "{w}"'))

    # 16. Kein Wettbewerb / Punkte-System
    bad_competitive = ['highscore', 'bestzeit', 'rekord', 'wettlauf', 'gegner']
    for w in bad_competitive:
        if w in content.lower():
            findings.append(('INFO', f'Mögliches Wettbewerbs-Vokabular: "{w}" — bitte pruefen'))

    return findings


def check_sw(spiel: str) -> list[tuple[str, str]]:
    findings = []
    sw = REPO / spiel / 'service-worker.js'
    if not sw.exists():
        return [('WARN', 'service-worker.js fehlt')]
    content = sw.read_text(encoding='utf-8', errors='replace')

    # Cache-Name muss Spiel-Praefix haben
    m = re.search(r"const\s+CACHE\s*=\s*['\"]([^'\"]+)['\"]", content)
    if not m:
        findings.append(('WARN', 'SW: const CACHE = ... fehlt'))
    else:
        cache = m.group(1)
        if not cache.startswith(spiel):
            findings.append(('WARN', f'SW Cache-Name "{cache}" hat keinen Spiel-Präfix'))

    # Cleanup-Filter muss Praefix nutzen
    if 'startsWith' in content:
        for m in re.finditer(r'startsWith\s*\(\s*["\']([^"\']+)["\']', content):
            prefix = m.group(1)
            if not prefix.startswith(spiel) and not prefix.startswith('lernspiele-'):
                findings.append(('WARN', f'SW startsWith-Filter "{prefix}" passt nicht zum Spiel-Praefix'))
    return findings


def check_manifest(spiel: str) -> list[tuple[str, str]]:
    findings = []
    mf = REPO / spiel / 'manifest.json'
    if not mf.exists():
        return [('WARN', 'manifest.json fehlt')]
    import json
    try:
        d = json.loads(mf.read_text(encoding='utf-8'))
    except Exception as e:
        return [('ERROR', f'manifest.json invalid: {e}')]
    if d.get('start_url') != './':
        findings.append(('INFO', f'manifest.start_url = "{d.get("start_url")}" (erwartet "./")'))
    if d.get('scope') != './':
        findings.append(('INFO', f'manifest.scope = "{d.get("scope")}" (erwartet "./")'))
    if d.get('lang') != 'de':
        findings.append(('INFO', f'manifest.lang = "{d.get("lang")}" (erwartet "de")'))
    return findings


def main():
    spiele = find_spiele()
    print(f"Pruefe {len(spiele)} Spiele\n")

    # Pro Spiel ausgeben
    total_err = 0
    total_warn = 0
    total_info = 0
    summary = defaultdict(int)

    for spiel in spiele:
        findings = check_spiel(spiel) + check_sw(spiel) + check_manifest(spiel)
        if not findings:
            continue
        errs = [f for f in findings if f[0] == 'ERROR']
        warns = [f for f in findings if f[0] == 'WARN']
        infos = [f for f in findings if f[0] == 'INFO']
        total_err += len(errs)
        total_warn += len(warns)
        total_info += len(infos)

        print(f"### {spiel}  ({len(errs)} ERROR, {len(warns)} WARN, {len(infos)} INFO)")
        for sev, msg in errs:
            print(f"  ERROR: {msg}")
            summary[msg] += 1
        for sev, msg in warns:
            print(f"  WARN:  {msg}")
            summary[msg] += 1
        for sev, msg in infos:
            print(f"  INFO:  {msg}")
        print()

    print(f"\n{'='*60}")
    print(f"GESAMT: {total_err} ERROR, {total_warn} WARN, {total_info} INFO")
    print(f"{'='*60}\n")

    if summary:
        print("Top haeufigste Issues:")
        for msg, cnt in sorted(summary.items(), key=lambda x: -x[1])[:15]:
            print(f"  {cnt}x  {msg}")

    return 0 if total_err == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
