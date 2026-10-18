"""Genera una imagen de fases/trazado por cada copa (estilo gráfico de pista de Umalator).

Uso:
  python tools/make_track_maps.py --tazuna TazunaDiscordBot-main/assets --cm data/cm_base.json --out assets/maps

Cada PNG se guarda como assets/maps/<clave_de_la_copa>.png. El bot los adjunta desde assets/,
así que no dependen de ninguna web. Colores y datos de pista: TazunaBot (MIT, JustWastingTime).
Fuente: Rubik (SIL OFL), incluida en tools/fonts/.
"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
C = {
    "bg": "#2b2d31", "title": "#6BB5A8", "axis": "#8b96a8", "tick": "#9ea7b7",
    "sky": "#A8D4F8", "flat": "#8DB86A", "uphill": "#E89548", "downhill": "#C49AA8",
    "blank": "#B8B2A8", "straight": "#A8BDD6", "corner": "#EDCA72",
    "early": "#59B292", "mid": "#D4BC6A", "late": "#F7A5A5", "spurt": "#E195AB",
    "text_dark": "#23262b", "keep": "#934761",
}
W, PAD_L, PAD_R = 1100, 30, 30
ROW_H, GAP = 46, 8


def font(bold, size):
    return ImageFont.truetype(str(HERE / "fonts" / ("Rubik-Bold.ttf" if bold else "Rubik-Regular.ttf")), size)


def fit_text(draw, text, box_w, bold=True, start=15, min_size=9):
    """Devuelve (texto, fuente) que quepa en box_w, o (None, None) si no cabe."""
    for size in range(start, min_size - 1, -1):
        f = font(bold, size)
        if draw.textlength(text, font=f) <= box_w - 8:
            return text, f
    return None, None


def render(m, title_extra=""):
    total = int(m["distance_meters"].rstrip("m"))
    x0, x1 = PAD_L, W - PAD_R
    px = lambda meters: x0 + (x1 - x0) * meters / total
    top = 58
    rows = 3
    H = top + rows * (ROW_H + GAP) + 70
    img = Image.new("RGB", (W, H), C["bg"])
    d = ImageDraw.Draw(img)
    d.text((PAD_L, 14), f"{m['name']}{title_extra}", font=font(True, 22), fill=C["title"])
    d.text((PAD_L, 40), f"{m['racetrack']} · {m['terrain']} · {m['direction']} · {total}m", font=font(False, 13), fill=C["axis"])

    def segment_row(y, segs, color_of, label_of):
        for seg in segs:
            xa, xb = px(seg["start"]), px(seg["end"])
            col = color_of(seg)
            d.rectangle([xa, y, xb, y + ROW_H], fill=col, outline=C["bg"], width=2)
            text = label_of(seg)
            if text:
                t, f = fit_text(d, text, xb - xa)
                if t:
                    d.text(((xa + xb) / 2, y + ROW_H / 2), t, font=f, fill=C["text_dark"], anchor="mm")
            # marcas de metros de inicio de segmento
            d.text((xa + 2, y + ROW_H + 1), str(seg["start"]), font=font(False, 9), fill=C["axis"])

    # fila 1: elevación
    y = top
    def elev_label(s):
        ch = s.get("change")
        return s["label"] + (f" {abs(ch):g}%" if ch and s.get("type") != "flat" else "")
    segment_row(y, m.get("elevation", []), lambda s: C.get(s.get("type"), C["flat"]), elev_label)
    # fila 2: rectas / curvas
    y += ROW_H + GAP + 6
    def lay_col(s):
        lab = s["label"].lower()
        return C["corner"] if lab.startswith("corner") else C["straight"] if lab.startswith("straight") else C["blank"]
    def lay_label(s):
        lab = s["label"]
        if lab.lower().startswith("corner"):
            return "C" + lab.split()[-1] if (px(s["end"]) - px(s["start"])) < 60 else lab
        return lab
    segment_row(y, m.get("layout", []), lay_col, lay_label)
    # fila 3: fases de carrera
    y += ROW_H + GAP + 6
    zc = {"early": C["early"], "mid": C["mid"], "late": C["late"], "last": C["spurt"]}
    def zone_col(s):
        l = s["label"].lower()
        return next((v for k, v in zc.items() if l.startswith(k)), C["blank"])
    segment_row(y, m.get("zones", []), zone_col, lambda s: s["label"])
    # línea de fin de "position keep"
    for pk in m.get("position_keep_ends", []):
        d.line([px(pk), top - 6, px(pk), y + ROW_H + 4], fill=C["keep"], width=2)
    # eje de metros
    ay = y + ROW_H + 26
    d.line([x0, ay, x1, ay], fill=C["axis"], width=1)
    step = 200 if total <= 2600 else 400
    for mtr in range(0, total + 1, step):
        d.line([px(mtr), ay, px(mtr), ay + 6], fill=C["tick"], width=1)
        d.text((px(mtr), ay + 9), f"{mtr}m", font=font(False, 11), fill=C["tick"], anchor="mt")
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tazuna", required=True, help="carpeta assets/ de TazunaBot (para maps.json)")
    ap.add_argument("--cm", default="data/cm_base.json")
    ap.add_argument("--out", default="assets/maps")
    a = ap.parse_args()
    maps = {m["name"]: m for m in json.load(open(Path(a.tazuna) / "maps.json", encoding="utf-8"))}
    cms = json.load(open(a.cm, encoding="utf-8"))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for key, cm in cms.items():
        m = maps.get(cm.get("map_id"))
        if not m:
            print(f"  ! {key}: no hay trazado para '{cm.get('map_id')}'")
            continue
        render(m).save(out / f"{key}.png", optimize=True)
        print(f"  {key}.png  ({m['name']})")


if __name__ == "__main__":
    main()
