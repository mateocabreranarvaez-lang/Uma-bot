"""Genera data/skills.json, supports.json, races.json, cm_base.json y meta.json.

Se ejecuta UNA vez en tu PC cuando quieras actualizar datos (no en el servidor del bot).

Uso (ajusta las rutas a donde descomprimiste los repos):
  python tools/import_data.py \
      --global  UmaTools-main/public/assets/master/global.json \
      --tazuna  TazunaDiscordBot-main/assets \
      --out     data

Fuentes:
  - global.json (UmaTools): base maestra del juego Global -> nombres exactos con ◎ ○ ×,
    costo (need_skill_point) y puntos (grade_value).
  - assets/ de TazunaBot: descripciones, efectos, aliases, supports, carreras, copas y pistas.
"""
import argparse
import json
import re
import sys
from pathlib import Path

GT = "https://gametora.com"
RARITY = {1: "normal", 2: "gold"}  # 3, 4, 5 -> unique

# Etiquetas en español para el tipo de skill (los nombres del juego no se traducen)
KIND_LABEL = {
    "passive": "Pasiva (stat)", "recovery": "Recuperación", "speed": "Velocidad",
    "acceleration": "Aceleración", "debuff": "Debuff (afecta a rivales)",
    "unique": "Única", "other": "Otra",
}
STYLE_NAMES = {1: "Front Runner", 2: "Pace Chaser", 3: "Late Surger", 4: "End Closer"}
DIST_NAMES = {1: "Short", 2: "Mile", 3: "Medium", 4: "Long"}
SURFACE_NAMES = {1: "Turf", 2: "Dirt"}


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"  {path}  ({len(data) if hasattr(data, '__len__') else ''} entradas)")


def slug(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def kind_from_tazuna(cat, rarity):
    c = re.sub(r"^(golden|rainbow)", "", cat or "")
    if rarity == "unique":
        return "unique"
    if c.endswith(("debuff",)):
        return "debuff"
    for key, kind in (("recovery", "recovery"), ("accel", "acceleration"), ("velocity", "speed")):
        if c.startswith(key):
            return kind
    if c in ("speed", "stamina", "power", "guts", "speednegative", "staminanegative",
             "powernegative", "gutsnegative", "gate", "gatenegative"):
        return "passive"
    return "other"


def kind_from_global(sk, rarity):
    """Respaldo cuando Tazuna no tiene la skill: usa el tipo de efecto de la base maestra."""
    if rarity == "unique":
        return "unique"
    types = {sk.get(f"ability_type_1_{i}") for i in (1, 2, 3)} - {0, None}
    if 9 in types:
        return "recovery"
    if 31 in types:
        return "acceleration"
    if 27 in types:
        return "speed"
    if types & {1, 2, 3, 4, 5, 10}:
        return "passive"
    return "other"


def parse_restrictions(sk):
    """Estilo / distancia / superficie si la condición es simple (sin 'o' entre alternativas)."""
    out = {}
    conds = [sk.get("condition_1") or "", sk.get("condition_2") or ""]
    for label, pat, names in (("styles", r"running_style==(\d)", STYLE_NAMES),
                              ("distance", r"distance_type==(\d)", DIST_NAMES),
                              ("surface", r"ground_type==(\d)", SURFACE_NAMES)):
        vals = set()
        for c in conds:
            if "@" in c:  # alternativas: demasiado ambiguo, no adivinamos
                vals = set()
                break
            vals.update(int(v) for v in re.findall(pat, c))
        if vals and all(v in names for v in vals):
            out[label] = " / ".join(names[v] for v in sorted(vals))
    return out


def build_skills(global_path, tz_dir):
    g = load(global_path)
    skills = g["skills"]
    tz = {s["gametora_id"]: s for s in load(tz_dir / "skill.json") if "skill_name" in s}
    out, matched = [], 0
    for s in skills:
        if "obsolete" in s["name"].lower() or s["name"].startswith("Carnival Bonus"):
            continue
        sid = str(s["id"])
        t = tz.get(sid)
        matched += bool(t)
        rarity = RARITY.get(s["rarity"], "unique")
        inherited = s["id"] >= 900000
        cost = s["need_skill_point"] or None
        kind = kind_from_tazuna(t["category"], rarity) if t else kind_from_global(s, rarity)
        entry = {
            "id": sid,
            "name": s["name"],
            "display": s["name"] + (" (Inherited)" if inherited else " (Unique)" if rarity == "unique" else ""),
            "rarity": rarity,
            "kind": kind,
            "category": KIND_LABEL[kind],
            "group": s["group_id"],
            "tier_rate": s["group_rate"],
            "cost": cost,
            "eval_pts": s["grade_value"],
            "desc": (t or {}).get("description") or s["description"],
            "inherited": inherited,
            "image_url": f"{GT}/images/umamusume/skill_icons/utx_ico_skill_{s['icon_id']}.png",
            "url": f"{GT}/umamusume/skills/{sid}",
        }
        if t:
            effects = []
            for e in t.get("effect", []):
                line = e.get("description", "")
                if e.get("conditions"):
                    line += " — " + "; ".join(e["conditions"])
                if line:
                    effects.append(line)
            if effects:
                entry["effects"] = effects
            if t.get("review"):
                entry["review"] = t["review"]
            if t.get("aliases"):
                entry["aliases"] = [a for a in t["aliases"] if a]
        entry.update(parse_restrictions(s))
        out.append(entry)
    print(f"  skills: {len(out)} (con datos de Tazuna: {matched})")
    return out, g["source"]


def build_supports(tz_dir):
    out = []
    for s in load(tz_dir / "supporter.json"):
        effects = {}
        for line in s.get("effects", []):
            k, _, v = line.partition(" - ")
            effects[k.strip()] = v.strip()
        events = []
        for e in s.get("events", []):
            opts = [{"choice": f"Opción {i}", "result": r} for i, r in enumerate(e.get("results", []), 1)]
            events.append({"name": e["name"], "type": e.get("type", "event"), "options": opts})
        out.append({
            "id": s["id"].split()[0],
            "name": s["character_name"],
            "title": s["card_name"],
            "rarity": s["rarity"].upper(),
            "type": s["category"],
            "unique": [] if s["unique"] == "-" else s["unique"].split("\n"),
            "effects": effects,
            "support_skills": s.get("support_skills", []),
            "event_skills": s.get("event_skills", []),
            "events": events,
            "image_url": s.get("thumbnail"),
            "gametora_url": s.get("url"),
            "aliases": s.get("aliases", []),
        })
    print(f"  supports: {len(out)}")
    return out


def build_races(tz_dir):
    keep = ("race_name", "grade", "racetrack", "direction", "terrain", "distance_type",
            "distance_meters", "season", "date", "thumbnail", "image", "url")
    out = [{k: r.get(k) for k in keep} for r in load(tz_dir / "races.json")]
    print(f"  races: {len(out)}")
    return out


def build_cm(tz_dir, races, assets_dir):
    maps = {m["name"]: m for m in load(tz_dir / "maps.json")}
    flat = lambda n: re.sub(r"[^a-z0-9]+", "", re.sub(r"\s*\(.*?\)", "", n.lower()))
    flat_full = lambda n: re.sub(r"[^a-z0-9]+", "", n.lower())
    banners = {}
    for r in races:
        if r.get("thumbnail"):
            banners.setdefault(flat(r["race_name"]), r["thumbnail"])
            banners.setdefault(flat_full(r["race_name"]), r["thumbnail"])
    out = {}
    for c in load(tz_dir / "champsmeet.json"):
        t = c["track"]
        key = slug(c["name"].replace(" 2026", ""))
        banner = None
        for race in [x.strip() for x in t.get("similar", "").split(",")]:
            hit = banners.get(flat(race)) or banners.get(flat_full(race))
            if hit:
                banner = hit
                break
        m = maps.get(c["map_id"], {})
        out[key] = {
            "name": c["name"],
            "number": c["number"],
            "gametora_url": f"{GT}/umamusume/events/champions-meeting",
            "banner_url": banner,
            "track_map_url": f"maps/{key}.png" if (assets_dir / "maps" / f"{key}.png").exists() else None,
            "umalator_url": c.get("umalator"),
            "map_id": c["map_id"],
            "course_id": m.get("cid"),
            "track": {
                "venue": t["racetrack"],
                "distance_m": f"{t['distance_type']} ({t['distance_meters']})",
                "surface": t["terrain"],
                "conditions": f"{t['season']} • {t['ground']} • {t['weather']} • {t['direction']}",
                "similar": t.get("similar", ""),
            },
            "summary": "",
            "sections": {},
        }
    print(f"  copas: {len(out)}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--global", dest="glob", required=True, help="ruta a master/global.json de UmaTools")
    ap.add_argument("--tazuna", required=True, help="carpeta assets/ de TazunaBot")
    ap.add_argument("--out", default="data")
    ap.add_argument("--assets", default="assets", help="carpeta assets/ del bot (donde están maps/*.png)")
    a = ap.parse_args()
    tz_dir, out = Path(a.tazuna), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    print("Importando...")
    skills, source = build_skills(a.glob, tz_dir)
    races = build_races(tz_dir)
    save(out / "skills.json", skills)
    save(out / "supports.json", build_supports(tz_dir))
    save(out / "races.json", races)
    save(out / "cm_base.json", build_cm(tz_dir, races, Path(a.assets)))
    save(out / "meta.json", {"game_version": source.get("game_version"),
                             "imported_at": source.get("imported_at"),
                             "note": "Costo y puntos: valores base de la base maestra Global."})
    print("Listo. cm_base.json se regenera siempre; tus guías van aparte en cm_guides.json y nunca se pisan.")


if __name__ == "__main__":
    sys.exit(main())
