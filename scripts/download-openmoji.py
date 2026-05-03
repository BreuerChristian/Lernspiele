#!/usr/bin/env python3
"""
download-openmoji.py - laedt OpenMoji-SVGs in _lib/icons/.

Liest scripts/openmoji-manifest.json und holt die farbigen SVGs aus dem
GitHub-Repo hfg-gmuend/openmoji (master/color/svg/<codepoint>.svg).
Ueberschreibt existierende _lib/icons/<name>.svg, aktualisiert INDEX.json.

Verwendung:
  python scripts/download-openmoji.py
  python scripts/download-openmoji.py --dry-run
"""
from __future__ import annotations
import argparse
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ICONS_DIR = REPO_ROOT / "_lib" / "icons"
INDEX_FILE = ICONS_DIR / "INDEX.json"
MANIFEST = REPO_ROOT / "scripts" / "openmoji-manifest.json"
BASE_URL = "https://raw.githubusercontent.com/hfg-gmuend/openmoji/master/color/svg"


def fetch_svg(codepoint: str) -> bytes | None:
    url = f"{BASE_URL}/{codepoint}.svg"
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            if r.status != 200:
                return None
            return r.read()
    except urllib.error.HTTPError as e:
        print(f"    HTTP {e.code}: {url}", file=sys.stderr)
        return None
    except urllib.error.URLError as e:
        print(f"    URLError: {e}", file=sys.stderr)
        return None


def update_index(updates: dict[str, dict], dry_run: bool) -> None:
    """
    Merget Aktualisierungen in INDEX.json. updates = {name: {kategorie, quelle}}.
    """
    if INDEX_FILE.exists():
        d = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    else:
        d = {"_comment": "", "icons": []}

    by_name = {e["name"]: e for e in d.get("icons", [])}
    for name, fields in updates.items():
        if name in by_name:
            by_name[name].update(fields)
        else:
            entry = {"name": name, "verwendet-in": []}
            entry.update(fields)
            by_name[name] = entry
    d["icons"] = sorted(by_name.values(), key=lambda e: e["name"])

    if dry_run:
        print(f"\n[DRY] INDEX.json haette {len(d['icons'])} Eintraege.")
    else:
        INDEX_FILE.write_text(
            json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"\nINDEX.json: {len(d['icons'])} Eintraege")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--manifest", default=str(MANIFEST))
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"Manifest fehlt: {manifest_path}", file=sys.stderr)
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not manifest:
        print("Manifest leer.")
        return 0

    print(f"Lade {len(manifest)} Icons aus OpenMoji ({BASE_URL})\n")
    ICONS_DIR.mkdir(parents=True, exist_ok=True)

    ok = 0
    fail = 0
    index_updates: dict[str, dict] = {}

    for entry in manifest:
        name = entry["name"]
        cp = entry["codepoint"]
        kategorie = entry.get("kategorie", "sonstige")

        out = ICONS_DIR / f"{name}.svg"
        print(f"[{name}] {cp}.svg  ", end="")
        svg = fetch_svg(cp)
        if not svg:
            print("FEHLER")
            fail += 1
            continue

        if args.dry_run:
            print(f"DRY ({len(svg)} bytes)")
        else:
            out.write_bytes(svg)
            print(f"OK ({len(svg)} bytes)")
        ok += 1
        index_updates[name] = {
            "kategorie": kategorie,
            "quelle": f"OpenMoji {cp} (CC-BY-SA 4.0)",
        }

    update_index(index_updates, dry_run=args.dry_run)

    print(f"\nZusammenfassung: {ok} OK, {fail} Fehler")
    if args.dry_run:
        print("(DRY-RUN, nichts geschrieben)")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
