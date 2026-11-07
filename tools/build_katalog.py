#!/usr/bin/env python3
"""Baut aus katalog/*.yaml die Ausgaben für Agenten (Konzept 1.2, Ebene „Ausgabe").

Aufruf:  python3 tools/build_katalog.py [--check] [--mit-kandidaten --out DIR]
Ergebnis: plugins/engineering/generated/kern.md
          plugins/engineering/generated/linsen/<linse>.md + index.json (Auswahl-Metadaten für review.py)
Bricht ab (Exit 1), wenn ein Budget reißt, eine id doppelt ist oder eine Linse fehlt.
--check baut nur im Speicher und schreibt nichts.
--mit-kandidaten nimmt Regeln mit status: kandidat dazu (für das Replay-Eval); nur zusammen mit --out,
damit generated/ nie Kandidaten enthält.
"""
import json, sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def arg(name, default):
    return Path(sys.argv[sys.argv.index(name) + 1]).expanduser().resolve() if name in sys.argv else default


# --katalog DIR and --out DIR let an overlay build its own catalog with this tool.
KATALOG = arg("--katalog", ROOT / "katalog")
OUT = arg("--out", ROOT / "plugins" / "engineering" / "generated")

KERN_MAX_BYTES = 2048   # Konzept 1.4, Startwert
LINSE_MAX_REGELN = 15   # Konzept 1.4, Startwert
KERN_TITLE = sys.argv[sys.argv.index("--titel") + 1] if "--titel" in sys.argv else "Core rules (always apply)"
HEADER = "<!-- Erzeugt von tools/build_katalog.py aus katalog/. Nicht von Hand ändern. -->\n"


def load(katalog=KATALOG):
    linsen = yaml.safe_load((katalog / "linsen.yaml").read_text())
    kern = yaml.safe_load((katalog / "kern.yaml").read_text()) if (katalog / "kern.yaml").exists() else []
    regeln = [r for f in sorted(katalog.glob("*.yaml")) if f.name not in ("linsen.yaml", "kern.yaml")
              for r in yaml.safe_load(f.read_text()) or []]
    return linsen, kern, regeln


def build(linsen, kern, regeln, status=("aktiv",)):
    """Gibt {relativer Pfad: Inhalt} zurück oder wirft ValueError mit allen Verstößen."""
    kern = [k for k in kern if k.get("status", "aktiv") in status]
    errs, ids = [], {}
    for r in regeln + kern:
        if r["id"] in ids:
            errs.append(f"id doppelt: {r['id']}")
        ids[r["id"]] = r
    names = {l["name"] for l in linsen}
    aktiv = [r for r in regeln if r.get("status") in status and r.get("stufe") == "linse"]
    for r in aktiv:
        if r["linse"] not in names:
            errs.append(f"{r['id']}: Linse {r['linse']} fehlt in linsen.yaml")
    for k in kern:
        for src in k.get("abgeleitet_von", []):
            if src not in ids:
                errs.append(f"{k['id']}: abgeleitet_von {src} existiert nicht")

    files = {}
    kern_md = HEADER + f"# {KERN_TITLE}\n\n" + "".join(f"- {k['regel']} `[{k['id']}]`\n" for k in kern)
    if len(kern_md.encode()) > KERN_MAX_BYTES:
        errs.append(f"Kern {len(kern_md.encode())} Bytes > Budget {KERN_MAX_BYTES}")
    files["kern.md"] = kern_md

    index = {"kern": "../kern.md", "linsen": []}
    for l in linsen:
        rs = sorted((r for r in aktiv if r["linse"] == l["name"]), key=lambda r: -r.get("belege", 0))
        if len(rs) > LINSE_MAX_REGELN:
            errs.append(f"Linse {l['name']}: {len(rs)} Regeln > Budget {LINSE_MAX_REGELN}")
        if not rs or l.get("review") == "aus":  # review: aus = nach Eval nicht im Linsen-Modus
            continue
        esk = sorted({r["eskaliert"] for r in rs if r.get("eskaliert")})
        body = HEADER + f"# Lens: {l['titel']}\n\n" + "".join(f"Severity: {e}.\n\n" for e in esk) + "".join(
            f"- {r['regel']}{' (severity: ' + r['schwere'] + ')' if r.get('schwere') else ''} `[{r['id']}]`\n"
            for r in rs)
        files[f"linsen/{l['name']}.md"] = body
        index["linsen"].append({k: l[k] for k in ("name", "titel", "stack", "pfade", "inhalt") if k in l}
                               | {"datei": f"{l['name']}.md", "regeln": len(rs)})
    files["linsen/index.json"] = json.dumps(index, indent=1, ensure_ascii=False) + "\n"
    if errs:
        raise ValueError("\n".join(errs))
    return files


def kern_belege(kern, regeln):
    by_id = {r["id"]: r for r in regeln}
    return {k["id"]: sum(by_id[s].get("belege", 0) for s in k.get("abgeleitet_von", []) if s in by_id) for k in kern}


def main():
    linsen, kern, regeln = load(KATALOG)
    mit = "--mit-kandidaten" in sys.argv
    out = OUT
    if mit and "--out" not in sys.argv:
        sys.exit("--mit-kandidaten nur mit --out DIR")
    try:
        files = build(linsen, kern, regeln, ("aktiv", "kandidat") if mit else ("aktiv",))
    except ValueError as e:
        sys.exit(f"Budget/Konsistenz verletzt:\n{e}")
    for kid, n in sorted(kern_belege(kern, regeln).items(), key=lambda x: -x[1]):
        print(f"  kern {kid}: {n} Belege")
    print(f"Kern {len(files['kern.md'].encode())}/{KERN_MAX_BYTES} Bytes, "
          f"{len(files) - 2} Linsen, {sum(1 for r in regeln if r.get('status') == 'aktiv')} aktive Regeln")
    if "--check" in sys.argv:
        return
    for rel, text in files.items():
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    print(f"geschrieben nach {out}")


if __name__ == "__main__":
    main()
