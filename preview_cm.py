"""Vista previa de una copa en texto (sin conectar el bot).
Uso: python tools/preview_cm.py sagittarius_cup [seccion]
Secciones: track_overview umas inheritance supports_whale supports_f2p skills"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import core

db = core.Database()
key = sys.argv[1] if len(sys.argv) > 1 else db.current_cm
secs = [sys.argv[2]] if len(sys.argv) > 2 else [s for s, _, _ in core.CM_SECTIONS
                                               if s == "track_overview" or s in db.cm[key].get("sections", {})]
for sec in secs:
    sp = core.cm_spec(db, key, sec)
    print("=" * 70, f"\n# {sp['title']}   [{core.spec_size(sp)}/6000 caracteres]")
    if sp["thumbnail"]: print(f"(miniatura: {sp['thumbnail']})")
    if sp["image"]: print(f"(imagen grande: {sp['image']})")
    if sp["description"]: print("\n" + sp["description"])
    for name, value in sp["fields"]:
        if name != "\u200b": print(f"\n### {name}")
        print(value)
    print(f"\n— {sp['footer']}")
