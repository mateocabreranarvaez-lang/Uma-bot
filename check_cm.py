"""Informe de calidad de las guías (data/cm_guides.json) frente al objetivo.

Uso: python tools/check_cm.py
Muestra, por copa y sección: caracteres usados (objetivo ~5500), estilos que faltan y
nombres de skills que NO existen en el juego Global (para cazar errores o nombres inventados).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import core

db = core.Database()
STYLE_KEYS = {"Front Runner": ["front"], "Pace Chaser": ["pace"], "Late Surger": ["late"],
              "End Closer": ["end closer", "end"], "Debuffer": ["debuff"]}
print(f"Datos: {len(db.cm)} copas, {len(db.skills)} skills, {len(db.supports)} supports ({db.version_note})")
print(f"Copa actual: {db.current_cm}\n")
print(f"{'copa':<17}{'sección':<16}{'chars':>6}  notas")
problems = 0
for key, cm in db.cm.items():
    for sec, _, _ in core.CM_SECTIONS:
        if sec != "track_overview" and sec not in cm.get("sections", {}):
            print(f"{key:<17}{sec:<16}{'—':>6}  (sin escribir)")
            continue
        spec = core.cm_spec(db, key, sec)
        text = " ".join([spec["description"] or ""] + [n + " " + v for n, v in spec["fields"]]).lower()
        notes = []
        if sec in ("umas", "inheritance", "skills", "supports_whale", "supports_f2p"):
            miss = [s for s, ks in STYLE_KEYS.items() if not any(k in text for k in ks)]
            if miss:
                notes.append("faltan estilos: " + ", ".join(miss))
        for style, entries in cm.get("sections", {}).get(sec, {}).get("styles", {}).items():
            bad = [e["name"] for e in entries if not db.find_skill_exact(e["name"])]
            if bad:
                notes.append(f"skills inexistentes en {style}: {', '.join(bad)}")
        if sec != "track_overview" and core.spec_size(spec) < core.TARGET_CHARS * 0.9:
            notes.append("corta (<90% del objetivo)")
        problems += bool(notes)
        print(f"{key:<17}{sec:<16}{core.spec_size(spec):>6}  {'; '.join(notes)}")
print(f"\nSecciones con avisos: {problems}")
