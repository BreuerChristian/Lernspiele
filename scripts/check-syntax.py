#!/usr/bin/env python3
"""check-syntax.py - JS-Syntaxpruefung aller Spiele.

Extrahiert jeden inline-<script>-Block (ohne src=) aus <spiel>/index.html und
laesst `node --check` darueber laufen. Faengt Tippfehler/Klammer-Fehler, die den
statischen Regel-Linter (check-spiele.py) nicht sieht.

Exit-Code 0 = alles ok, 1 = mindestens ein Syntaxfehler. Braucht `node` im PATH.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXCLUDE_DIRS = {'_lib', '_templates', 'scripts', '.git', '.claude', 'node_modules'}
# inline <script> ohne src-Attribut
SCRIPT_RE = re.compile(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', re.S | re.I)


def find_spiele():
    out = []
    for d in sorted(REPO.iterdir()):
        if d.is_dir() and d.name not in EXCLUDE_DIRS and not d.name.startswith('.'):
            if (d / 'index.html').exists():
                out.append(d.name)
    return out


def check_node_available():
    try:
        subprocess.run(['node', '--version'], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def check_spiel(spiel):
    """Returnt Liste Fehlermeldungen (leer = ok)."""
    errors = []
    content = (REPO / spiel / 'index.html').read_text(encoding='utf-8', errors='replace')
    blocks = SCRIPT_RE.findall(content)
    for idx, code in enumerate(blocks):
        if not code.strip():
            continue
        with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
            f.write(code)
            tmp = f.name
        try:
            res = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
            if res.returncode != 0:
                msg = (res.stderr or res.stdout).strip().splitlines()
                head = msg[0] if msg else 'unbekannter Syntaxfehler'
                errors.append(f'Script-Block #{idx + 1}: {head}')
        finally:
            Path(tmp).unlink(missing_ok=True)
    return errors


def main():
    if not check_node_available():
        print('FEHLER: node nicht gefunden — Syntaxpruefung nicht moeglich.', file=sys.stderr)
        return 2

    total_err = 0
    for spiel in find_spiele():
        errors = check_spiel(spiel)
        if errors:
            total_err += len(errors)
            print(f'### {spiel}')
            for e in errors:
                print(f'  SYNTAXFEHLER: {e}')

    print(f'\n{"=" * 60}')
    if total_err:
        print(f'{total_err} Syntaxfehler gefunden.')
    else:
        print('Alle Spiele syntaktisch ok.')
    print(f'{"=" * 60}')
    return 0 if total_err == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
