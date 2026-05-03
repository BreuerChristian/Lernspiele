#!/usr/bin/env python3
"""
cleanup-icons.py - One-Shot-Aufraeumen der Icon-Bibliothek.

1) Normalisiert GROSSBUCHSTABEN-Dateinamen zu lowercase.
   - Wenn lowercase-Pendant existiert: GROSS-Datei loeschen.
   - Sonst: GROSS umbenennen zu lowercase.
2) Mapped englische Begriffe (englisch-erste-woerter) auf deutsche Icons:
   - Wenn deutsches Pendant existiert: SVG-Inhalt kopieren.
   - Sonst: OpenMoji-Codepoint laden.
3) INDEX.json synchronisieren.
"""
from __future__ import annotations
import json
import shutil
import urllib.request
import urllib.error
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
ICONS_DIR = REPO_ROOT / "_lib" / "icons"
INDEX_FILE = ICONS_DIR / "INDEX.json"
OPENMOJI_BASE = "https://raw.githubusercontent.com/hfg-gmuend/openmoji/master/color/svg"

# Englisch -> Deutsch (Lib hat das deutsche Pendant)
EN_TO_DE = {
    "apple":  "apfel",
    "banana": "banane",
    "bird":   "vogel",
    "bread":  "brot",
    "cat":    "katze",
    "cow":    "kuh",
    "dog":    "hund",
    "fish":   "fisch",
    "frog":   "frosch",
    "horse":  "pferd",
    "milk":   "milch",
    "mouse":  "maus",
    "pig":    "schwein",
    "rabbit": "hase",
    "sheep":  "schaf",
    "water":  "wasser",
}

# Englisch -> OpenMoji-Codepoint (kein deutsches Pendant in Lib)
EN_TO_OPENMOJI = {
    "baby":    "1F476",  # Baby
    "black":   "2B1B",   # Black Large Square
    "blue":    "1F7E6",  # Blue Large Square
    "brother": "1F466",  # Boy
    "cheese":  "1F9C0",  # Cheese Wedge
    "father":  "1F468",  # Man
    "green":   "1F7E9",  # Green Large Square
    "mother":  "1F469",  # Woman
    "red":     "1F7E5",  # Red Large Square
    "sister":  "1F467",  # Girl
    "white":   "2B1C",   # White Large Square
    "yellow":  "1F7E8",  # Yellow Large Square
}

CATEGORY_FOR_EN = {
    # Tier-Mapping erbt von DE
    "apple": "essen",   "banana": "essen",     "bread": "essen",
    "milk": "essen",    "cheese": "essen",     "water": "natur",
    "bird": "tiere",    "cat": "tiere",        "cow": "tiere",
    "dog": "tiere",     "fish": "tiere",       "frog": "tiere",
    "horse": "tiere",   "mouse": "tiere",      "pig": "tiere",
    "rabbit": "tiere",  "sheep": "tiere",
    "baby": "menschen", "brother": "menschen", "father": "menschen",
    "mother": "menschen", "sister": "menschen",
    "black": "farben",  "blue": "farben",      "green": "farben",
    "red": "farben",    "white": "farben",     "yellow": "farben",
}


def fetch_openmoji(codepoint: str) -> bytes | None:
    url = f"{OPENMOJI_BASE}/{codepoint}.svg"
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return r.read() if r.status == 200 else None
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        print(f"    Fehler {url}: {e}", file=sys.stderr)
        return None


def normalize_uppercase() -> tuple[int, int]:
    """Returnt (umbenannt, geloescht)."""
    renamed = 0
    deleted = 0
    for f in list(ICONS_DIR.glob("*.svg")):
        if f.stem.isupper() and f.stem.isalpha():
            target = ICONS_DIR / f"{f.stem.lower()}.svg"
            if target.exists():
                print(f"  loesche {f.name} (lowercase {target.name} existiert schon)")
                f.unlink()
                deleted += 1
            else:
                print(f"  benenne {f.name} -> {target.name}")
                f.rename(target)
                renamed += 1
    return renamed, deleted


def update_index_for_uppercase(d: dict) -> None:
    """Entferne UPPERCASE-Eintraege, fuege lowercase falls noetig hinzu."""
    icons = d.get("icons", [])
    new_icons = []
    by_lower = {i["name"]: i for i in icons if not i["name"].isupper()}
    for icon in icons:
        if icon["name"].isupper():
            lower = icon["name"].lower()
            if lower in by_lower:
                # lowercase-Eintrag bleibt, UPPER weg
                continue
            # UPPER zu lower konvertieren
            icon["name"] = lower
            by_lower[lower] = icon
        else:
            pass  # bereits in by_lower
    d["icons"] = sorted(by_lower.values(), key=lambda x: x["name"])


def map_english(d: dict) -> tuple[int, int, int]:
    """Returnt (kopiert_aus_de, geladen_aus_openmoji, fehler)."""
    by_name = {i["name"]: i for i in d["icons"]}
    copied = 0
    loaded = 0
    errors = 0

    # Pass 1: Englisch -> Deutsch (Datei kopieren)
    for en, de in EN_TO_DE.items():
        de_path = ICONS_DIR / f"{de}.svg"
        en_path = ICONS_DIR / f"{en}.svg"
        if not de_path.exists():
            print(f"  [WARN] {de}.svg fehlt, kann {en} nicht mappen")
            errors += 1
            continue
        shutil.copyfile(de_path, en_path)
        print(f"  {en}.svg <- {de}.svg (kopiert)")
        copied += 1
        # Index-Eintrag aktualisieren
        by_name[en] = {
            "name": en,
            "kategorie": CATEGORY_FOR_EN.get(en, "englisch"),
            "quelle": f"Kopie von {de}.svg (englisch-erste-woerter Mapping)",
            "verwendet-in": [],
        }

    # Pass 2: Englisch -> OpenMoji (laden)
    for en, cp in EN_TO_OPENMOJI.items():
        en_path = ICONS_DIR / f"{en}.svg"
        svg = fetch_openmoji(cp)
        if not svg:
            print(f"  [FEHLER] OpenMoji {cp} fuer {en} nicht ladbar")
            errors += 1
            continue
        en_path.write_bytes(svg)
        print(f"  {en}.svg <- OpenMoji {cp}")
        loaded += 1
        by_name[en] = {
            "name": en,
            "kategorie": CATEGORY_FOR_EN.get(en, "englisch"),
            "quelle": f"OpenMoji {cp} (CC-BY-SA 4.0)",
            "verwendet-in": [],
        }

    d["icons"] = sorted(by_name.values(), key=lambda x: x["name"])
    return copied, loaded, errors


def remove_orphans(d: dict) -> int:
    """Entfernt INDEX-Eintraege ohne SVG-Datei."""
    have = {p.stem for p in ICONS_DIR.glob("*.svg")}
    before = len(d["icons"])
    d["icons"] = [i for i in d["icons"] if i["name"] in have]
    return before - len(d["icons"])


def main() -> int:
    print("== 1) GROSSBUCHSTABEN normalisieren ==")
    renamed, deleted = normalize_uppercase()
    print(f"   {renamed} umbenannt, {deleted} geloescht\n")

    # INDEX.json laden
    d = json.loads(INDEX_FILE.read_text(encoding="utf-8"))

    print("== 2) INDEX.json fuer GROSSBUCHSTABEN bereinigen ==")
    update_index_for_uppercase(d)

    print("\n== 3) Englisch -> Deutsch / OpenMoji ==")
    copied, loaded, en_errors = map_english(d)
    print(f"\n   {copied} kopiert (DE-Pendant), {loaded} aus OpenMoji geladen, {en_errors} Fehler\n")

    print("== 4) Verwaiste INDEX-Eintraege ohne SVG entfernen ==")
    orphans = remove_orphans(d)
    print(f"   {orphans} Eintraege entfernt\n")

    INDEX_FILE.write_text(
        json.dumps(d, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    n_files = len(list(ICONS_DIR.glob("*.svg")))
    print(f"== Fertig: {n_files} SVG-Dateien, {len(d['icons'])} INDEX-Eintraege ==")
    return 0 if en_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
