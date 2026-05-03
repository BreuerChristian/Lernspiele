#!/usr/bin/env python3
"""
icons.py - Werkzeug fuer die _lib/icons/-Sammlung.

Subkommandos:
  extract   Extrahiert SVG-Definitionen aus existierenden Spielen in _lib/icons/.
  update    (geplant) Propagiert _lib/icons/<name>.svg in Spiele mit Marker-Pattern.
  verify    (geplant) Konsistenz-Check (alle Marker haben Pendants, alle SVGs valide).

Verwendung:
  python scripts/icons.py extract                 # liest scripts/extract-manifest.json
  python scripts/icons.py extract --dry-run       # zeigt was geschehen wuerde, schreibt nichts
  python scripts/icons.py extract --manifest <p>  # alternatives Manifest

Manifest-Format (JSON):
  [
    { "spiel": "anlaute",         "name": "ananas" },
    { "spiel": "anlaute",         "name": "esel",   "kategorie": "tiere" },
    { "spiel": "jahreszeiten-sortieren", "name": "blatt", "ausgabe": "blatt-herbst" }
  ]

Pflichtfelder: spiel, name. Optional: kategorie (default "sonstige"), ausgabe
(default = name).

Erkannte SVG-Definitions-Patterns:
  A) <name>: `<svg ...>...</svg>`             (anlaute, jahreszeiten-sortieren)
  B) <name>: () => `<svg ...>...</svg>`       (was-passt-nicht)
  C) <name>: `<inner-svg-content>`            (reim-paare — ohne <svg>-Wrapper)
                                              wird mit viewBox 0 0 100 100 gewrappt
  D) <name>: { ..., paths: [ {d, fill}, ... ] }   (schatten-finden — Tier-Definitionen)
                                              wird zu <svg viewBox="0 0 200 200">
                                              mit <path d=… fill=…/> Elementen

Stilrichtlinie + Marker-Pattern siehe _lib/README.md.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ICONS_DIR = REPO_ROOT / "_lib" / "icons"
INDEX_FILE = ICONS_DIR / "INDEX.json"
DEFAULT_MANIFEST = REPO_ROOT / "scripts" / "extract-manifest.json"

# Patterns die wir erkennen koennen, in Reihenfolge der Spezifitaet.
# Jedes Pattern hat einen Capture-Group der den SVG-Inhalt liefert.
# {NAME} wird vor der Kompilierung durch re.escape(name) ersetzt.
PATTERNS = [
    # A) Klassisches Template-Literal mit <svg>-Wrapper
    #    apfel: `<svg viewBox="0 0 200 200">...</svg>`,
    {
        "name": "template-literal-with-svg",
        "regex": r"\b{NAME}\s*:\s*`(<svg[^`]+?</svg>)`",
        "wrap": False,
    },
    # B) Function-Style mit <svg>-Wrapper
    #    sonne: () => `<svg viewBox="0 0 100 100">...</svg>`,
    {
        "name": "function-style-with-svg",
        "regex": r"\b{NAME}\s*:\s*\(\s*\)\s*=>\s*`(\s*<svg[^`]+?</svg>)\s*`",
        "wrap": False,
    },
    # C) Template-Literal NUR Inner-Content (z.B. reim-paare).
    #    sonne: `<circle .../><g>...</g>`,
    #    Wird mit <svg viewBox="0 0 100 100" xmlns="..."> gewrappt.
    {
        "name": "template-literal-inner-only",
        "regex": r"\b{NAME}\s*:\s*`([^`]+?)`",
        "wrap": True,
    },
    # D) Object-Style mit paths-Array (z.B. schatten-finden Tier-Definitionen).
    #    kuh: { name: '...', group: '...', paths: [ { d: '...', fill: '#...' }, ... ] },
    #    Wird zu <svg viewBox="0 0 200 200"> mit <path>-Elementen pro Eintrag.
    {
        "name": "paths-object",
        "regex": r"\b{NAME}\s*:\s*\{[\s\S]*?paths\s*:\s*\[([\s\S]*?)\]\s*,?\s*\n\s*\}",
        "wrap": False,  # eigene Transform-Funktion, siehe extract_one
    },
]


def paths_array_to_svg(paths_body: str, viewbox: str = "0 0 200 200") -> str:
    """
    Wandelt einen JS-paths-Array-Body in vollstaendiges SVG.
    Iteriert ueber jedes { d: '...', fill: '#...' } Element.
    """
    item_re = re.compile(
        r"""\{\s*d\s*:\s*['"]([^'"]+)['"][^}]*?fill\s*:\s*['"]([^'"]+)['"][^}]*?\}""",
        re.DOTALL,
    )
    items = item_re.findall(paths_body)
    if not items:
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}">\n</svg>\n'
    body = "\n".join(f'  <path d="{d}" fill="{fill}"/>' for d, fill in items)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}">\n{body}\n</svg>\n'


def load_manifest(path: Path) -> list[dict]:
    if not path.exists():
        print(f"[FEHLER] Manifest fehlt: {path}", file=sys.stderr)
        sys.exit(1)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[FEHLER] Manifest ist kein gueltiges JSON: {e}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(data, list):
        print(f"[FEHLER] Manifest muss eine Liste sein.", file=sys.stderr)
        sys.exit(1)
    return data


def normalize_svg(svg_text: str, *, wrap: bool, viewbox_default: str = "0 0 100 100") -> str:
    """
    Sorgt dafuer dass das SVG einen xmlns hat und (falls wrap=True) in <svg>
    eingewickelt wird. Entfernt aria-label aus dem <svg>-Tag, weil es im
    Lib-Kontext irrelevant ist (das Spiel setzt eigene aria-Labels).
    Schoenheits-Whitespace wird beibehalten.
    """
    text = svg_text.strip()
    if wrap:
        # Inner-only -> wrap in vollstaendiges SVG
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox_default}">\n'
            f'{text}\n'
            f'</svg>\n'
        )
    # mit <svg>-Wrapper - xmlns ggf. ergaenzen
    if "xmlns=" not in text[:200]:
        text = re.sub(r"<svg(\s|>)", r'<svg xmlns="http://www.w3.org/2000/svg"\1', text, count=1)
    # aria-label aus dem <svg>-Tag rauswerfen
    text = re.sub(r'\s+aria-label="[^"]*"', "", text, count=1)
    if not text.endswith("\n"):
        text += "\n"
    return text


def extract_one(spiel: str, name: str) -> tuple[str, str] | None:
    """
    Sucht die SVG-Definition fuer <name> in <spiel>/index.html.
    Returnt (svg_text, pattern_name) oder None bei kein Treffer.
    """
    html_path = REPO_ROOT / spiel / "index.html"
    if not html_path.exists():
        print(f"  [WARN] Spiel-Datei fehlt: {html_path}")
        return None
    content = html_path.read_text(encoding="utf-8", errors="replace")
    name_escaped = re.escape(name)
    for pattern in PATTERNS:
        regex = re.compile(pattern["regex"].replace("{NAME}", name_escaped))
        m = regex.search(content)
        if m:
            captured = m.group(1)
            if pattern["name"] == "paths-object":
                # Sonderbehandlung: paths-Array zu vollstaendigem SVG umwandeln
                svg_raw = paths_array_to_svg(captured, viewbox="0 0 200 200")
            else:
                svg_raw = captured
            return svg_raw, pattern["name"]
    return None


def write_icon(name: str, svg_text: str, *, wrap: bool, source: str, dry_run: bool) -> Path:
    out_path = ICONS_DIR / f"{name}.svg"
    final = normalize_svg(svg_text, wrap=wrap)
    if dry_run:
        print(f"  [DRY] schreibe {len(final)} bytes -> {out_path.name}")
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        # Header-Kommentar mit Quelle ergaenzen (nach <svg ...>)
        header_comment = f'  <!-- Quelle: {source} (extract-icons.py) -->\n'
        final = re.sub(r"(<svg[^>]*>)\n", r"\1\n" + header_comment.rstrip("\n") + "\n", final, count=1)
        out_path.write_text(final, encoding="utf-8")
        print(f"  OK  -> _lib/icons/{out_path.name}")
    return out_path


def update_index(entries_to_add: list[dict], *, dry_run: bool) -> None:
    """
    Merged neue Eintraege in INDEX.json. Bei gleichem 'name': existierender
    Eintrag bleibt erhalten (Quelle/Kategorie nicht ueberschreiben), nur die
    Verwendet-In-Liste bleibt unangetastet.
    """
    if INDEX_FILE.exists():
        data = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    else:
        data = {
            "_comment": "Auflistung aller Icons in _lib/icons/.",
            "icons": [],
        }
    existing = {e["name"]: e for e in data.get("icons", [])}
    for entry in entries_to_add:
        if entry["name"] in existing:
            continue
        existing[entry["name"]] = entry
    data["icons"] = sorted(existing.values(), key=lambda e: e["name"])
    if dry_run:
        print(f"\n[DRY] INDEX.json: {len(data['icons'])} Eintraege total (war {len(existing) - len(entries_to_add)} + {len(entries_to_add)} neue)")
    else:
        INDEX_FILE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"\nINDEX.json: {len(data['icons'])} Eintraege total")


def cmd_extract(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest) if args.manifest else DEFAULT_MANIFEST
    manifest = load_manifest(manifest_path)
    if not manifest:
        print(f"Manifest ist leer.")
        return 0

    print(f"Verarbeite {len(manifest)} Eintraege aus {manifest_path.name}\n")

    entries_for_index: list[dict] = []
    extracted = 0
    skipped_existing = 0
    not_found = 0

    for entry in manifest:
        spiel = entry.get("spiel")
        name = entry.get("name")
        if not spiel or not name:
            print(f"  [SKIP] Eintrag ohne 'spiel'/'name': {entry}")
            continue
        out_name = entry.get("ausgabe", name)
        kategorie = entry.get("kategorie", "sonstige")

        out_path = ICONS_DIR / f"{out_name}.svg"
        if out_path.exists() and not args.overwrite:
            print(f"[uebersprungen] {out_name}.svg existiert schon (--overwrite zum erzwingen)")
            skipped_existing += 1
            entries_for_index.append({
                "name": out_name,
                "kategorie": kategorie,
                "quelle": f"{spiel} (bereits in Lib)",
                "verwendet-in": [],
            })
            continue

        print(f"[{out_name}] aus {spiel}/index.html")
        result = extract_one(spiel, name)
        if not result:
            print(f"  [FEHLER] kein passendes Pattern fuer '{name}' gefunden")
            not_found += 1
            continue
        svg_text, pattern_name = result
        wrap = pattern_name == "template-literal-inner-only"
        write_icon(out_name, svg_text, wrap=wrap, source=spiel, dry_run=args.dry_run)
        extracted += 1
        entries_for_index.append({
            "name": out_name,
            "kategorie": kategorie,
            "quelle": spiel,
            "verwendet-in": [],
        })

    update_index(entries_for_index, dry_run=args.dry_run)

    print(f"\nZusammenfassung:")
    print(f"  extrahiert:      {extracted}")
    print(f"  uebersprungen:   {skipped_existing} (schon in Lib)")
    print(f"  nicht gefunden:  {not_found}")
    if args.dry_run:
        print(f"  (DRY-RUN, nichts geschrieben)")
    return 0 if not_found == 0 else 1


# ============================================================================
# discover - alle Spiele scannen, neue SVG-Kandidaten finden
# ============================================================================

# Sub-Patterns wie oben, aber mit (\w+) als Capture fuer den Namen
DISCOVER_PATTERNS = [
    ("A", r"\b(\w+)\s*:\s*`(<svg[^`]+?</svg>)`"),
    ("B", r"\b(\w+)\s*:\s*\(\s*\)\s*=>\s*`(\s*<svg[^`]+?</svg>)\s*`"),
    ("D", r"\b(\w+)\s*:\s*\{[\s\S]*?paths\s*:\s*\[([\s\S]*?)\]\s*,?\s*\n\s*\}"),
]
# Pattern C separat — matcht zu greedy ohne Filter
DISCOVER_PATTERN_C = r"\b(\w+)\s*:\s*`([^`]+?)`"
SVG_TAGS = ("<path", "<circle", "<rect", "<ellipse", "<line ", "<polygon", "<g ", "<svg")
# JS-Property-Namen die KEINE Icon-Namen sind
SKIP_NAMES = {
    "id", "name", "key", "target", "type", "value", "href", "title",
    "label", "group", "svg", "paths", "fill", "stroke", "d", "viewBox",
    "options", "pool", "words", "data", "state", "config", "level",
    "stage", "mode", "color", "icon", "src", "alt", "fact", "rhyme",
    "say", "file", "emoji", "w", "l", "a", "b", "x", "y", "r", "cx",
    "cy", "rx", "ry", "tag", "text", "img", "audio", "video",
    "html", "body", "head", "main", "section", "article", "nav",
    "footer", "header", "div", "span", "p", "h1", "h2", "h3",
    "left", "right", "top", "bottom", "first", "last", "next", "prev",
    "min", "max", "start", "end", "from", "to", "input", "output",
    "default", "active", "hidden", "visible", "show", "hide",
    "true", "false", "null", "undefined", "this", "self", "that",
    "el", "elem", "node", "item", "obj", "fn", "cb", "callback",
    "i", "j", "k", "n", "m", "len", "length", "size", "count",
    "rgb", "rgba", "hsl", "hex", "css", "js",
    "answer", "question", "result", "score", "time", "step",
    "FE0F", "200D",  # Variation Selectors die in Codepoints auftauchen
}


def discover_in_file(html_path: Path) -> list[tuple[str, str]]:
    """Returnt Liste von (icon_name, pattern_letter)."""
    try:
        content = html_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    seen: dict[str, str] = {}  # name -> pattern_letter (erster Treffer gewinnt)

    # Patterns A, B, D
    for letter, regex in DISCOVER_PATTERNS:
        for m in re.finditer(regex, content):
            name = m.group(1)
            if name in SKIP_NAMES or name in seen:
                continue
            if name.isdigit() or len(name) <= 1:
                continue
            seen[name] = letter

    # Pattern C - mit SVG-Tag-Filter, gewinnt nur wenn nicht schon A/B/D
    for m in re.finditer(DISCOVER_PATTERN_C, content):
        name = m.group(1)
        body = m.group(2)
        if name in SKIP_NAMES or name in seen:
            continue
        if name.isdigit() or len(name) <= 1:
            continue
        if not any(tag in body for tag in SVG_TAGS):
            continue
        seen[name] = "C"

    return sorted(seen.items())


def cmd_discover(args: argparse.Namespace) -> int:
    # Existierende Lib-Icons (ohne -openmoji/-jahreszeiten/-schatten/-reim-paare/-was-passt-nicht Varianten ueberlegen)
    existing_names = {p.stem for p in ICONS_DIR.glob("*.svg")}
    # Auch Basis-Namen ohne Suffix als "existierend" zaehlen
    existing_bases = {n.split("-")[0] for n in existing_names}

    # Spiele finden
    spiele = sorted(
        d.name for d in REPO_ROOT.iterdir()
        if d.is_dir()
        and not d.name.startswith(("_", "."))
        and (d / "index.html").exists()
    )

    print(f"Scanne {len(spiele)} Spiele\n")

    findings: dict[str, list[tuple[str, str]]] = {}
    new_global: dict[str, list[tuple[str, str]]] = {}  # name -> list of (spiel, pattern)

    for spiel in spiele:
        results = discover_in_file(REPO_ROOT / spiel / "index.html")
        if not results:
            continue
        findings[spiel] = results
        for name, pattern in results:
            if name in existing_names or name in existing_bases:
                continue
            new_global.setdefault(name, []).append((spiel, pattern))

    # Bericht
    print(f"{'='*70}")
    print(f"Pro Spiel:")
    print(f"{'='*70}\n")
    for spiel, results in findings.items():
        new_in_spiel = [(n, p) for n, p in results if n in new_global]
        if not new_in_spiel:
            continue
        print(f"### {spiel}  ({len(new_in_spiel)} neu)")
        for n, p in new_in_spiel:
            print(f"    {n}  ({p})")
        print()

    print(f"{'='*70}")
    print(f"Neue Kandidaten (Lib hat keinen Eintrag):")
    print(f"{'='*70}\n")
    if not new_global:
        print("(keine)")
    else:
        for name in sorted(new_global):
            sources = new_global[name]
            if len(sources) == 1:
                print(f"  {name}  <- {sources[0][0]} (Pattern {sources[0][1]})")
            else:
                src_list = ", ".join(f"{s} ({p})" for s, p in sources)
                print(f"  {name}  <- {src_list}")
    print()
    print(f"Zusammenfassung: {len(new_global)} neue Kandidaten")

    # Manifest schreiben
    if args.write_manifest and new_global:
        out_path = REPO_ROOT / "scripts" / "discover-manifest.json"
        manifest_entries = []
        for name in sorted(new_global):
            spiel, _pattern = new_global[name][0]  # erste Quelle nehmen
            manifest_entries.append({
                "spiel": spiel,
                "name": name,
                "kategorie": "sonstige",
            })
        out_path.write_text(json.dumps(manifest_entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"\nManifest geschrieben: {out_path.relative_to(REPO_ROOT)}")
        print(f"Naechster Schritt: python scripts/icons.py extract --manifest {out_path.relative_to(REPO_ROOT)}")

    return 0


# ============================================================================
# update - Lib-Icons in Spiele propagieren via Marker-Pattern
# ============================================================================

# Marker:
#   // ICON:<name> START
#   <name>: `<svg>...</svg>`,
#   // ICON:<name> END
# Wir ersetzen ALLES zwischen den beiden Marker-Zeilen.
ICON_MARKER_RE = re.compile(
    r"^([ \t]*)// ICON:(\w+) START[ \t]*\n([\s\S]*?)^[ \t]*// ICON:\2 END",
    re.MULTILINE,
)

# Cache-Version-Bump in Spiel-SW (z.B. plus-tuermchen-v4 -> v5)
CACHE_BUMP_RE = re.compile(r"(const\s+CACHE\s*=\s*['\"][\w-]+-v)(\d+)(['\"])")


def render_icon_block(name: str, indent: str, svg_text: str) -> str:
    """
    Baut den Inhalt zwischen den Markern: '<indent><name>: `<svg>`,\n'
    """
    svg = svg_text.strip()
    # Template-Literal-Konflikt: ${ -> \${ escapen
    svg = svg.replace("${", "\\${")
    return f"{indent}{name}: `{svg}`,\n"


def update_markers_in(content: str, icons_dir: Path) -> tuple[str, int, list[str]]:
    """Returnt (new_content, replacement_count, missing_icons)."""
    missing: list[str] = []
    count = 0

    def replace(m: re.Match) -> str:
        nonlocal count
        indent = m.group(1)
        name = m.group(2)
        svg_path = icons_dir / f"{name}.svg"
        if not svg_path.exists():
            missing.append(name)
            return m.group(0)
        try:
            svg_text = svg_path.read_text(encoding="utf-8")
        except OSError as e:
            missing.append(f"{name} (read error: {e})")
            return m.group(0)
        block = render_icon_block(name, indent, svg_text)
        count += 1
        return f"{indent}// ICON:{name} START\n{block}{indent}// ICON:{name} END"

    new_content = ICON_MARKER_RE.sub(replace, content)
    return new_content, count, missing


def bump_cache_version(sw_path: Path, dry_run: bool) -> str | None:
    """Bumpt die vN-Endung im CACHE-Namen. Returnt neue Version oder None."""
    if not sw_path.exists():
        return None
    try:
        sw = sw_path.read_text(encoding="utf-8")
    except OSError:
        return None
    m = CACHE_BUMP_RE.search(sw)
    if not m:
        return None
    new_v = int(m.group(2)) + 1
    new_sw = CACHE_BUMP_RE.sub(rf"\g<1>{new_v}\g<3>", sw, count=1)
    # Auch im startsWith-Filter im activate-Handler nichts zu aendern
    if not dry_run:
        sw_path.write_text(new_sw, encoding="utf-8")
    return f"v{m.group(2)} -> v{new_v}"


def cmd_update(args: argparse.Namespace) -> int:
    spiele = sorted(
        d.name for d in REPO_ROOT.iterdir()
        if d.is_dir()
        and not d.name.startswith(("_", "."))
        and (d / "index.html").exists()
    )

    total_replacements = 0
    changed = []
    all_missing: dict[str, list[str]] = {}

    for spiel in spiele:
        html_path = REPO_ROOT / spiel / "index.html"
        try:
            content = html_path.read_text(encoding="utf-8")
        except OSError:
            continue
        new_content, count, missing = update_markers_in(content, ICONS_DIR)
        if missing:
            all_missing[spiel] = missing
        if count > 0 and new_content != content:
            if not args.dry_run:
                html_path.write_text(new_content, encoding="utf-8")
            changed.append((spiel, count))
            total_replacements += count

    # SW-Cache-Bump pro geaendertem Spiel
    bumps = {}
    if not args.no_bump:
        for spiel, _ in changed:
            sw_path = REPO_ROOT / spiel / "service-worker.js"
            res = bump_cache_version(sw_path, args.dry_run)
            if res:
                bumps[spiel] = res

    # INDEX.json verwendet-in pflegen
    if not args.dry_run:
        update_verwendet_in_field(spiele)

    print("== Marker-Update ==")
    for spiel, n in changed:
        bump = f", SW {bumps.get(spiel, 'kein Bump')}"
        print(f"  {spiel}: {n} Marker ersetzt{bump}")
    if not changed:
        print("  (keine Marker gefunden — kein Spiel migriert)")
    if all_missing:
        print("\nFehlende Lib-Icons (Marker da, aber kein _lib/icons/<name>.svg):")
        for spiel, ms in all_missing.items():
            print(f"  {spiel}: {', '.join(ms)}")
    print(f"\nGesamt: {total_replacements} Ersetzungen in {len(changed)} Spielen")
    if args.dry_run:
        print("(DRY-RUN, nichts geschrieben)")
    return 0 if not all_missing else 1


def update_verwendet_in_field(spiele: list[str]) -> None:
    """Aktualisiert INDEX.json verwendet-in Feld basierend auf Markern."""
    if not INDEX_FILE.exists():
        return
    d = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    used: dict[str, list[str]] = {}
    for spiel in spiele:
        html_path = REPO_ROOT / spiel / "index.html"
        try:
            content = html_path.read_text(encoding="utf-8")
        except OSError:
            continue
        for m in re.finditer(r"// ICON:(\w+) START", content):
            used.setdefault(m.group(1), []).append(spiel)
    for icon in d["icons"]:
        icon["verwendet-in"] = sorted(set(used.get(icon["name"], [])))
    INDEX_FILE.write_text(
        json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


# ============================================================================
# verify - Konsistenz-Check
# ============================================================================

def cmd_verify(args: argparse.Namespace) -> int:
    issues: list[str] = []
    spiele = sorted(
        d.name for d in REPO_ROOT.iterdir()
        if d.is_dir()
        and not d.name.startswith(("_", "."))
        and (d / "index.html").exists()
    )

    used_names: dict[str, list[str]] = {}
    for spiel in spiele:
        html_path = REPO_ROOT / spiel / "index.html"
        try:
            content = html_path.read_text(encoding="utf-8")
        except OSError:
            continue
        starts = re.findall(r"// ICON:(\w+) START", content)
        ends = re.findall(r"// ICON:(\w+) END", content)
        s_set, e_set = set(starts), set(ends)
        for name in s_set - e_set:
            issues.append(f"{spiel}: Marker START fuer '{name}' ohne END")
        for name in e_set - s_set:
            issues.append(f"{spiel}: Marker END fuer '{name}' ohne START")
        for name in s_set & e_set:
            used_names.setdefault(name, []).append(spiel)

    have = {p.stem for p in ICONS_DIR.glob("*.svg")}

    # Verwendete Namen ohne Lib-Icon
    for name, spiele_list in used_names.items():
        if name not in have:
            issues.append(f"Icon '{name}' wird in {spiele_list} verwendet, aber _lib/icons/{name}.svg fehlt")

    # Lib-Icons ohne Verwendung
    unused = sorted(have - set(used_names))

    # INDEX.json Konsistenz
    if INDEX_FILE.exists():
        d = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        index_names = {i["name"] for i in d["icons"]}
        only_in_index = index_names - have
        only_in_files = have - index_names
        for n in only_in_index:
            issues.append(f"INDEX.json hat '{n}' aber _lib/icons/{n}.svg fehlt")
        for n in only_in_files:
            issues.append(f"_lib/icons/{n}.svg existiert aber kein INDEX-Eintrag")

    print("== Konsistenz-Check ==")
    print(f"  Lib-Icons:           {len(have)}")
    print(f"  Verwendet in Spielen: {len(used_names)}")
    print(f"  Unverwendet:          {len(unused)}")
    print(f"  Issues:              {len(issues)}")
    if used_names:
        print(f"\nVerwendete Icons:")
        for name, spiele_list in sorted(used_names.items()):
            print(f"  {name}: {', '.join(spiele_list)}")
    if issues:
        print(f"\nProbleme:")
        for i in issues:
            print(f"  - {i}")
    return 0 if not issues else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ext = sub.add_parser("extract", help="SVGs aus existierenden Spielen extrahieren")
    p_ext.add_argument("--manifest", "-m", help=f"Pfad zum Manifest (default: {DEFAULT_MANIFEST.relative_to(REPO_ROOT)})")
    p_ext.add_argument("--dry-run", action="store_true", help="Nichts schreiben, nur zeigen was geschehen wuerde")
    p_ext.add_argument("--overwrite", action="store_true", help="Existierende SVGs ueberschreiben")
    p_ext.set_defaults(func=cmd_extract)

    p_dis = sub.add_parser("discover", help="Alle Spiele scannen, neue Icon-Kandidaten finden")
    p_dis.add_argument("--write-manifest", action="store_true",
                       help="scripts/discover-manifest.json mit den Kandidaten erzeugen (zum Befuellen mit kategorie)")
    p_dis.set_defaults(func=cmd_discover)

    p_upd = sub.add_parser("update", help="Lib-Icons in Spiele propagieren (Marker-Pattern)")
    p_upd.add_argument("--dry-run", action="store_true", help="Zeigen was geaendert wuerde, nichts schreiben")
    p_upd.add_argument("--no-bump", action="store_true", help="SW-Cache-Version nicht automatisch bumpen")
    p_upd.set_defaults(func=cmd_update)

    p_ver = sub.add_parser("verify", help="Konsistenz: Marker + Lib-Icons + Verwendung")
    p_ver.set_defaults(func=cmd_verify)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
