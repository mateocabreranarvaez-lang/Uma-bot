"""Lógica del bot sin dependencias de Discord (se puede probar sin conectarse).

Un "spec" de embed es un dict:
{title, url, author, description, thumbnail, image, fields:[(name, value)], footer, color}
bot.py lo convierte en discord.Embed.
"""
import difflib
import json
import logging
import re
import unicodedata
from pathlib import Path

log = logging.getLogger("umabot")

BASE = Path(__file__).parent
DATA = BASE / "data"

# Límites de Discord: 6000 caracteres en total por embed, 1024 por campo, 4096 en descripción.
EMBED_LIMIT = 5900   # margen de seguridad bajo 6000
TARGET_CHARS = 5500  # objetivo de las guías
FIELD_LIMIT = 1024
DESC_LIMIT = 4096

GT_CM = "https://gametora.com/umamusume/events/champions-meeting"
GT_SKILLS = "https://gametora.com/umamusume/skills"
GT_SUPPORTS = "https://gametora.com/umamusume/supports"

CM_SECTIONS = [
    ("track_overview", "Track Info", "🏟️"),
    ("umas", "Best Umas", "🏇"),
    ("inheritance", "Inheritance", "🧬"),
    ("supports_whale", "Supports (Whale)", "🐋"),
    ("supports_f2p", "Supports (F2P)", "🆓"),
    ("skills", "Key Skills", "⚡"),
]

STYLES = ["Front Runner", "Pace Chaser", "Late Surger", "End Closer", "Debuffer"]

VARIANT_CHARS = "◯○◎✕×✗"
TIER_ICON = {"gold": "🟡", "normal": "⚪", "inherit": "🧬", "passive": "🟢", "unique": "🌟"}
KIND_ICON = {
    "passive": "🟢", "recovery": "💚", "speed": "🏃", "acceleration": "⚡",
    "debuff": "🟣", "unique": "🌟", "other": "🔹",
}
RARITY_COLOR = {"gold": 0xF1C40F, "normal": 0xBDC3C7, "unique": 0xE67E22, "SSR": 0xF1C40F,
                "SR": 0xE67E22, "R": 0x95A5A6}
DEFAULT_COLOR = 0x2F3136


# ---------------------------------------------------------------- datos
def load_json(name, default):
    path = DATA / name
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def norm(text):
    """Minúsculas, sin acentos, sin símbolos de variante (◯ ◎ ✕) ni puntuación."""
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(f"[{VARIANT_CHARS}]", " ", text.lower())
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return " ".join(text.split())


def variant_of(name):
    for ch in VARIANT_CHARS:
        if ch in name:
            return {"○": "◯", "×": "✕", "✗": "✕"}.get(ch, ch)
    return ""


def canon(name):
    """Unifica símbolos parecidos (◯ -> ○, ✕/✗ -> ×) para comparar nombres de skills."""
    return str(name).replace("◯", "○").replace("✕", "×").replace("✗", "×")


def merge_cm(base, guides):
    """cm_base.json (datos automáticos) + cm_guides.json (guías escritas a mano)."""
    out = {}
    for key, cm in base.items():
        cm = dict(cm)
        g = guides.get(key, {})
        for k, v in g.items():
            if k == "track":
                cm["track"] = {**cm.get("track", {}), **v}
            elif k == "sections":
                cm["sections"] = {**cm.get("sections", {}), **v}
            else:
                cm[k] = v
        out[key] = cm
    return out


class Database:
    def __init__(self, cm=None, skills=None, supports=None, meta=None):
        guides = load_json("cm_guides.json", {})
        self.config = guides.pop("_config", {})
        if cm is not None:
            self.cm = cm
        else:
            base = load_json("cm_base.json", {})
            self.cm = merge_cm(base, guides) if base else load_json("cm.json", {})
        self.skills = skills if skills is not None else load_json("skills.json", [])
        self.supports = supports if supports is not None else load_json("supports.json", [])
        self.meta = meta if meta is not None else load_json("meta.json", {})
        for i, s in enumerate(self.skills):
            s.setdefault("id", f"s{i}")
            s.setdefault("display", s["name"])
            s["_base"] = norm(s["name"])
            s["_variant"] = variant_of(s["name"])
            s["_alias"] = [a for a in (norm(x) for x in s.get("aliases", [])) if a]
        for i, s in enumerate(self.supports):
            s.setdefault("id", f"c{i}")
            s["_key"] = norm(f"{s['name']} {s.get('title', '')} {s.get('rarity', '')}")
            s["_alias"] = [a for a in (norm(x) for x in s.get("aliases", [])) if a]
        self.skill_by_id = {s["id"]: s for s in self.skills}
        self.support_by_id = {s["id"]: s for s in self.supports}
        self._by_lname = {}
        for s in self.skills:
            self._by_lname.setdefault(canon(s["name"]).lower(), []).append(s)

    @property
    def current_cm(self):
        key = self.config.get("current_cm")
        if key in self.cm:
            return key
        return next(reversed(self.cm), None) if self.cm else None

    @property
    def version_note(self):
        v = self.meta.get("game_version")
        return f"Global v{v}" if v else "datos del juego"

    # ---- skills
    @staticmethod
    def _prefer(cands):
        """Entre varias candidatas: la que tiene costo y, de preferencia, la versión ○ (tier 1)."""
        return min(cands, key=lambda s: (s.get("cost") is None, s.get("tier_rate", 1) != 1,
                                         abs(s.get("tier_rate", 1)), s["name"]))

    def find_skill_exact(self, name):
        cands = self._by_lname.get(canon(name).lower())
        if not cands:
            q = norm(name)
            cands = [s for s in self.skills if s["_base"] == q]
        return self._prefer(cands) if cands else None

    def siblings(self, skill):
        """Otras versiones (× / ○ / ◎ / dorada) del mismo grupo o con el mismo nombre base."""
        grp = skill.get("group")
        out = [s for s in self.skills if s["id"] != skill["id"] and (
            (grp is not None and s.get("group") == grp) or s["_base"] == skill["_base"])]
        return sorted(out, key=lambda s: (s.get("tier_rate", 0), s["name"]))

    def search_skills(self, query, limit=25):
        return _rank(self.skills, query, lambda s: [s["_base"]] + s["_alias"], limit,
                     tiebreak=lambda s: (_VARIANT_ORDER.get(s["_variant"], 9), s["name"], s["id"]))

    # ---- supports
    def search_supports(self, query, limit=25):
        return _rank(self.supports, query, lambda s: [s["_key"]] + s["_alias"], limit,
                     tiebreak=lambda s: (s["name"], s.get("rarity", ""), s["id"]))


_VARIANT_ORDER = {"✕": 0, "◯": 1, "◎": 2, "": 3}


def _rank(items, query, key, limit, tiebreak):
    q = norm(query)
    if not q:
        return []
    tokens = q.split()
    scored = []
    for it in items:
        keys = key(it)
        keys = [keys] if isinstance(keys, str) else keys
        score = 0
        for k in keys:
            if k == q:
                sc = 100
            elif k.startswith(q):
                sc = 80
            elif q in k:
                sc = 60
            elif all(t in k for t in tokens):
                sc = 50
            else:
                ratio = max([difflib.SequenceMatcher(None, q, k).ratio()] +
                            [difflib.SequenceMatcher(None, q, w).ratio() for w in k.split()])
                sc = ratio * 40 if ratio >= 0.7 else 0
            score = max(score, sc)
        if score:
            scored.append((-score, tiebreak(it), it))
    scored.sort(key=lambda x: (x[0], x[1]))
    # La coincidencia difusa (erratas) solo se usa si no hay coincidencias directas
    if scored and -scored[0][0] >= 50:
        scored = [x for x in scored if -x[0] >= 50]
    return [x[2] for x in scored[:limit]]


# ---------------------------------------------------------------- texto
def chunk_text(text, limit=FIELD_LIMIT):
    """Parte un texto en trozos <= limit cortando en saltos de línea."""
    chunks, cur = [], ""
    for line in str(text).split("\n"):
        while len(line) > limit:
            cut = line.rfind(" ", 0, limit)
            cut = cut if cut > limit // 2 else limit
            piece, line = line[:cut], line[cut:].lstrip()
            if cur:
                chunks.append(cur)
                cur = ""
            chunks.append(piece)
        if len(cur) + len(line) + (1 if cur else 0) > limit:
            chunks.append(cur)
            cur = line
        else:
            cur = f"{cur}\n{line}" if cur else line
    if cur:
        chunks.append(cur)
    return chunks or ["—"]


def new_spec(**kw):
    spec = {"title": None, "url": None, "author": None, "description": None,
            "thumbnail": None, "image": None, "fields": [], "footer": None,
            "color": DEFAULT_COLOR}
    spec.update(kw)
    return spec


def add_field(spec, name, value):
    """Añade un campo; si el valor pasa de 1024 lo reparte en varios."""
    for i, chunk in enumerate(chunk_text(value)):
        spec["fields"].append((str(name)[:256] if i == 0 else "\u200b", chunk))


def spec_size(spec):
    total = len(spec.get("title") or "") + len(spec.get("description") or "")
    total += len(spec.get("footer") or "") + len(spec.get("author") or "")
    total += sum(len(n) + len(v) for n, v in spec["fields"])
    return total


def finalize(spec, footer):
    """Fija el pie y recorta si se pasa del límite (avisando en el log)."""
    spec["footer"] = footer
    if spec.get("description") and len(spec["description"]) > DESC_LIMIT:
        spec["description"] = spec["description"][:DESC_LIMIT - 1] + "…"
    while spec_size(spec) > EMBED_LIMIT and spec["fields"]:
        over = spec_size(spec) - EMBED_LIMIT
        name, value = spec["fields"][-1]
        if len(value) - over - 1 > 60:
            spec["fields"][-1] = (name, value[:len(value) - over - 1].rstrip() + "…")
        else:
            spec["fields"].pop()
        log.warning("Embed recortado (%s) por superar el límite", spec.get("title"))
    return spec


# ---------------------------------------------------------------- Champions Meeting
def skill_line(db, entry):
    """Línea de una skill del CM; completa precio y puntos desde skills.json."""
    sk = db.find_skill_exact(entry["name"])
    cost = entry.get("cost", sk.get("cost") if sk else None)
    pts = entry.get("pts", sk.get("eval_pts") if sk else None)
    icon = TIER_ICON.get(entry.get("tier", "normal"), "⚪")
    parts = [f"{icon} **{entry['name']}**"]
    if cost is not None:
        parts.append(f"💰 {cost}")
    if pts is not None:
        parts.append(f"⭐ {pts}")
    line = " · ".join(parts)
    if entry.get("note"):
        line += f" — {entry['note']}"
    return line


def cm_spec(db, cm_key, section):
    cm = db.cm[cm_key]
    secs = cm.get("sections", {})
    name = cm.get("name", "Champions Meeting")
    spec = new_spec(url=cm.get("gametora_url", GT_CM))
    spec["thumbnail"] = cm.get("banner_url")

    if section == "track_overview":
        spec["title"] = f"🏆 {name}"
        spec["image"] = cm.get("track_map_url")
        track = cm.get("track", {})
        for label, key in (("Racetrack", "venue"), ("Distance", "distance_m"),
                           ("Terrain", "surface"), ("Conditions", "conditions"),
                           ("Similar to", "similar")):
            if track.get(key):
                add_field(spec, label, f"**{track[key]}**")
        if cm.get("summary"):
            add_field(spec, "Overview & Advice", cm["summary"])
        if cm.get("umalator_url") and len(cm["umalator_url"]) < 900:
            add_field(spec, "Simulación", f"[Abrir en Umalator]({cm['umalator_url']})")
        for f in secs.get("stats", {}).get("fields", []):
            if "league" in f.get("name", "").lower():
                add_field(spec, f"📊 {f['name']}", f["value"])
        for f in secs.get("track_overview", {}).get("fields", []):
            add_field(spec, f.get("name", "•"), f.get("value", "—"))
    else:
        sec = secs.get(section, {})
        spec["title"] = f"{name} — {sec.get('title', section)}"
        spec["description"] = sec.get("description")
        for f in sec.get("fields", []):
            add_field(spec, f.get("name", "•"), f.get("value", "—"))
        for style, entries in sec.get("styles", {}).items():
            add_field(spec, f"🏁 {style}", "\n".join(skill_line(db, e) for e in entries))
    return finalize(spec, f"Haz clic en el título para abrir GameTora • {db.version_note}")


# ---------------------------------------------------------------- Skills
def skill_spec(db, sk):
    kind = sk.get("kind", "other")
    spec = new_spec(
        title=f"{KIND_ICON.get(kind, '🔹')} {sk.get('display', sk['name'])}",
        url=sk.get("url") or GT_SKILLS,
        author=sk.get("category") or kind.capitalize(),
        thumbnail=sk.get("image_url"),
        color=RARITY_COLOR.get(sk.get("rarity", "normal"), DEFAULT_COLOR),
    )
    spec["description"] = sk.get("desc") or None
    info = []
    if sk.get("cost") is not None:
        info.append(f"💰 **Costo:** {sk['cost']} SP")
    elif sk.get("rarity") == "unique" and not sk.get("inherited"):
        info.append("💰 **Costo:** no se compra (skill única)")
    if sk.get("eval_pts") is not None:
        info.append(f"⭐ **Puntos de rating:** {sk['eval_pts']}")
    if sk.get("cost") and sk.get("eval_pts"):
        info.append(f"📈 **Eficiencia:** {sk['eval_pts'] / sk['cost']:.2f} pts por SP")
    rar = {"normal": "Normal (blanca)", "gold": "Dorada", "unique": "Única"}.get(sk.get("rarity"))
    if rar:
        info.append(f"💎 **Rareza:** {rar}" + (" · heredada" if sk.get("inherited") else ""))
    if sk.get("styles"):
        info.append(f"🏁 **Estilo:** {sk['styles']}")
    if sk.get("distance"):
        info.append(f"📏 **Distancia:** {sk['distance']}")
    if sk.get("surface"):
        info.append(f"🌱 **Superficie:** {sk['surface']}")
    if info:
        add_field(spec, "Datos", "\n".join(info))
    if sk.get("effects"):
        add_field(spec, "Efecto", "\n".join(f"• {e}" for e in sk["effects"]))
    if sk.get("review"):
        add_field(spec, "Notas", sk["review"])
    sibs = db.siblings(sk)
    if sibs:
        add_field(spec, "Otras versiones", "\n".join(
            f"• **{x.get('display', x['name'])}** — 💰 {x['cost'] if x.get('cost') is not None else '—'}"
            f" · ⭐ {x.get('eval_pts', '—')}" for x in sibs[:8]))
    if sk.get("learned_from"):
        add_field(spec, "Se obtiene con", "\n".join(f"• {x}" for x in sk["learned_from"]))
    return finalize(spec, f"Costo y puntos base ({db.version_note}); los puntos reales varían con la aptitud")


# ---------------------------------------------------------------- Supports
def support_spec(db, sp):
    spec = new_spec(
        title=f"{sp.get('title', sp['name'])} ({sp.get('rarity', '?')})",
        url=sp.get("gametora_url") or GT_SUPPORTS,
        author=sp["name"],
        thumbnail=sp.get("image_url"),
        color=RARITY_COLOR.get(sp.get("rarity", ""), DEFAULT_COLOR),
    )
    desc = []
    uniq = sp.get("unique")
    if uniq:
        desc.append("__Unique__")
        desc.extend(uniq if isinstance(uniq, list) else [uniq])
        desc.append("")
    for k, v in sp.get("effects", {}).items():
        desc.append(f"✨ {k} - {v}")
    spec["description"] = "\n".join(desc) or None
    if sp.get("support_skills"):
        add_field(spec, "Support Skills", "\n".join(_skill_name_line(db, n) for n in sp["support_skills"]))
    if sp.get("event_skills"):
        add_field(spec, "Event Skills", "\n".join(_skill_name_line(db, n) for n in sp["event_skills"]))
    return finalize(spec, f"Haz clic en el título para abrir GameTora • {db.version_note}")


def _skill_name_line(db, name):
    sk = db.find_skill_exact(name)
    icon = KIND_ICON.get(sk.get("kind", "other"), "🔹") if sk else "🔹"
    return f"{icon} {name}"


def event_spec(sp, event):
    spec = new_spec(title=event["name"], author=f"{sp['name']} — {sp.get('title', '')}",
                    thumbnail=sp.get("image_url"), url=sp.get("gametora_url") or GT_SUPPORTS,
                    color=RARITY_COLOR.get(sp.get("rarity", ""), DEFAULT_COLOR))
    for opt in event.get("options", []):
        add_field(spec, opt.get("choice", "•"), opt.get("result", "—"))
    return finalize(spec, "Evento de support card")
