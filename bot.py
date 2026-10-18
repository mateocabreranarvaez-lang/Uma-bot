import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Select, View

import core

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("umabot")

DB = core.Database()
ASSETS = core.BASE / "assets"


# ------------------------------------------------------------------ servidor 24/7 (Render)
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot activo 24/7")

    def log_message(self, *args):
        pass


def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), DummyHandler).serve_forever()


# ------------------------------------------------------------------ spec -> discord.Embed
def to_embed(spec):
    """Convierte el spec en Embed. Las imágenes que no son URL se buscan en assets/ y se adjuntan."""
    files = []

    def resolve(ref):
        if not ref:
            return None
        if ref.startswith(("http://", "https://")):
            return ref
        path = ASSETS / ref
        if path.exists():
            files.append(discord.File(path, filename=path.name))
            return f"attachment://{path.name}"
        log.warning("Imagen no encontrada: %s", ref)
        return None

    embed = discord.Embed(title=spec["title"], url=spec["url"],
                          description=spec["description"], color=spec["color"])
    if spec["author"]:
        embed.set_author(name=spec["author"])
    for name, value in spec["fields"]:
        embed.add_field(name=name, value=value, inline=False)
    thumb, image = resolve(spec["thumbnail"]), resolve(spec["image"])
    if thumb:
        embed.set_thumbnail(url=thumb)
    if image:
        embed.set_image(url=image)
    if spec["footer"]:
        embed.set_footer(text=spec["footer"])
    return embed, files


async def show(interaction, spec, view=None, content=None, edit=False):
    """Envía o edita el mensaje. attachments=[] limpia imágenes adjuntas de la vista anterior."""
    embed, files = to_embed(spec)
    if edit:
        await interaction.response.edit_message(content=content, embed=embed, attachments=files, view=view)
    else:
        kwargs = {"content": content, "embed": embed}
        if files:
            kwargs["files"] = files
        if view is not None:
            kwargs["view"] = view
        await interaction.response.send_message(**kwargs)


# ------------------------------------------------------------------ menú genérico de coincidencias
class PickSelect(Select):
    """'Found N matches. Pick one:' — las versiones ✕ ◯ ◎ aparecen como opciones separadas."""

    def __init__(self, items, label, description, placeholder, emoji, on_pick):
        self.items = {str(i): it for i, it in enumerate(items[:25])}
        self.on_pick = on_pick
        options = [discord.SelectOption(label=label(it)[:100], value=k, emoji=emoji,
                                        description=(description(it) or None))
                   for k, it in self.items.items()]
        super().__init__(placeholder=placeholder, options=options)

    async def callback(self, interaction):
        await self.on_pick(interaction, self.items[self.values[0]])


class PickView(View):
    def __init__(self, *args, **kwargs):
        super().__init__(timeout=600)
        self.add_item(PickSelect(*args, **kwargs))


# ------------------------------------------------------------------ Champions Meeting
class CMSelect(Select):
    def __init__(self, cm_key, current):
        secs = DB.cm[cm_key].get("sections", {})
        options = [discord.SelectOption(label=label, value=key, emoji=emoji, default=(key == current))
                   for key, label, emoji in core.CM_SECTIONS
                   if key == "track_overview" or key in secs]
        super().__init__(placeholder="SELECCIONA UNA SECCIÓN DE LA CM...", options=options)
        self.cm_key = cm_key

    async def callback(self, interaction):
        section = self.values[0]
        await show(interaction, core.cm_spec(DB, self.cm_key, section), CMView(self.cm_key, section),
                   content=None, edit=True)


class CMView(View):
    def __init__(self, cm_key, current="track_overview"):
        super().__init__(timeout=900)
        self.add_item(CMSelect(cm_key, current))


async def open_cm(interaction, cm_key, edit=False, content=None):
    await show(interaction, core.cm_spec(DB, cm_key, "track_overview"), CMView(cm_key),
               content=content, edit=edit)


def cm_label(d, key):
    t = d.get("track", {})
    return f"{d.get('name', key)} ({t.get('venue', '?')} {t.get('distance_m', '')} {t.get('surface', '')})".replace("  ", " ")


async def cm_autocomplete(interaction, current):
    q = core.norm(current)
    out = [app_commands.Choice(name=cm_label(d, k)[:100], value=k)
           for k, d in DB.cm.items()
           if not q or q in core.norm(d.get("name", "")) or q in core.norm(k)
           or q in core.norm(d.get("track", {}).get("venue", ""))]
    return out[:25]


# ------------------------------------------------------------------ /skill
class SkillVersionSelect(Select):
    def __init__(self, sibs):
        options = [discord.SelectOption(label=s.get("display", s["name"])[:100], value=s["id"]) for s in sibs[:25]]
        super().__init__(placeholder="Ver otra versión (✕ / ◯ / ◎)...", options=options)

    async def callback(self, interaction):
        await open_skill(interaction, DB.skill_by_id[self.values[0]], edit=True)


async def open_skill(interaction, sk, edit=False, content=None):
    view = None
    sibs = DB.siblings(sk)
    if sibs:
        view = View(timeout=600)
        view.add_item(SkillVersionSelect(sibs))
    await show(interaction, core.skill_spec(DB, sk), view, content=content, edit=edit)


async def skill_autocomplete(interaction, current):
    return [app_commands.Choice(name=s.get("display", s["name"])[:100], value=s["id"])
            for s in DB.search_skills(current, 25)]


# ------------------------------------------------------------------ /support
class SupportSkillSelect(Select):
    def __init__(self, names):
        found = [DB.find_skill_exact(n) for n in names]
        self.found = {s["id"]: s for s in found if s}
        options = [discord.SelectOption(label=s.get("display", s["name"])[:100], value=sid) for sid, s in self.found.items()]
        super().__init__(placeholder="Select a skill", options=options[:25])

    async def callback(self, interaction):
        await open_skill(interaction, self.found[self.values[0]], edit=True)


class SupportEventSelect(Select):
    def __init__(self, sp):
        self.sp = sp
        options = [discord.SelectOption(label=e["name"][:100], value=str(i))
                   for i, e in enumerate(sp["events"][:25])]
        super().__init__(placeholder="Select an event", options=options)

    async def callback(self, interaction):
        ev = self.sp["events"][int(self.values[0])]
        await show(interaction, core.event_spec(self.sp, ev), SupportView(self.sp), edit=True)


class SupportView(View):
    def __init__(self, sp):
        super().__init__(timeout=900)
        names = sp.get("support_skills", []) + sp.get("event_skills", [])
        if any(DB.find_skill_exact(n) for n in names):
            self.add_item(SupportSkillSelect(names))
        if sp.get("events"):
            self.add_item(SupportEventSelect(sp))


async def open_support(interaction, sp, edit=False, content=None):
    view = SupportView(sp)
    await show(interaction, core.support_spec(DB, sp), view if view.children else None,
               content=content, edit=edit)


async def support_autocomplete(interaction, current):
    return [app_commands.Choice(name=f"{s['name']} — {s.get('title', '')} ({s.get('rarity', '?')})"[:100],
                                value=s["id"]) for s in DB.search_supports(current, 25)]


# ------------------------------------------------------------------ bot
class UmaBot(commands.Bot):
    async def setup_hook(self):
        synced = await self.tree.sync()
        log.info("Sincronizados %d comandos slash.", len(synced))


bot = UmaBot(command_prefix="!", intents=discord.Intents.default())


@bot.tree.command(name="cm", description="Guía completa de una Champions Meeting")
@app_commands.describe(busqueda="Escribe o elige la copa")
@app_commands.autocomplete(busqueda=cm_autocomplete)
async def slash_cm(interaction: discord.Interaction, busqueda: str = None):
    if not DB.cm:
        return await interaction.response.send_message("❌ No hay datos en `data/cm.json`.", ephemeral=True)
    if not busqueda:
        return await open_cm(interaction, DB.current_cm)
    if busqueda in DB.cm:
        return await open_cm(interaction, busqueda)
    q = core.norm(busqueda)
    matches = [(k, d) for k, d in DB.cm.items()
               if q in core.norm(d.get("name", "")) or q in core.norm(k)
               or q in core.norm(d.get("track", {}).get("venue", ""))]
    if not matches:
        return await interaction.response.send_message(f"🔍 Sin resultados para **{busqueda}**.", ephemeral=True)
    if len(matches) == 1:
        return await open_cm(interaction, matches[0][0])

    async def pick(inter, item):
        await open_cm(inter, item[0], edit=True, content=f"✅ Seleccionaste **{item[1].get('name')}**")

    await interaction.response.send_message(
        f"🔍 **Found {len(matches)} matches. Pick one:**",
        view=PickView(matches, lambda m: m[1].get("name", m[0]), lambda m: m[1].get("track", {}).get("distance_m"),
                      "Choose a Champions Meeting...", "🏆", pick))


@bot.tree.command(name="skill", description="Busca una skill (cada versión ✕ ◯ ◎ aparece por separado)")
@app_commands.describe(nombre="Nombre de la skill")
@app_commands.autocomplete(nombre=skill_autocomplete)
async def slash_skill(interaction: discord.Interaction, nombre: str):
    if not DB.skills:
        return await interaction.response.send_message("❌ No hay datos en `data/skills.json`.", ephemeral=True)
    if nombre in DB.skill_by_id:
        return await open_skill(interaction, DB.skill_by_id[nombre])
    matches = DB.search_skills(nombre)
    if not matches:
        return await interaction.response.send_message(f"🔍 Sin resultados para **{nombre}**.", ephemeral=True)
    if len(matches) == 1:
        return await open_skill(interaction, matches[0])

    async def pick(inter, sk):
        await open_skill(inter, sk, edit=True, content=f"✅ Seleccionaste **{sk.get('display', sk['name'])}**")

    await interaction.response.send_message(
        f"🔍 **Found {len(matches)} matches. Pick one:**",
        view=PickView(matches, lambda s: s.get("display", s["name"]),
                      lambda s: f"{s.get('category', '')} · 💰{s.get('cost') if s.get('cost') is not None else '—'} · ⭐{s.get('eval_pts', '—')}",
                      "Choose a skill...", "⚡", pick))


@bot.tree.command(name="support", description="Busca una support card")
@app_commands.describe(nombre="Personaje o nombre de la carta")
@app_commands.autocomplete(nombre=support_autocomplete)
async def slash_support(interaction: discord.Interaction, nombre: str):
    if not DB.supports:
        return await interaction.response.send_message("❌ No hay datos en `data/supports.json`.", ephemeral=True)
    if nombre in DB.support_by_id:
        return await open_support(interaction, DB.support_by_id[nombre])
    matches = DB.search_supports(nombre)
    if not matches:
        return await interaction.response.send_message(f"🔍 Sin resultados para **{nombre}**.", ephemeral=True)
    if len(matches) == 1:
        return await open_support(interaction, matches[0])

    async def pick(inter, sp):
        await open_support(inter, sp, edit=True, content=f"✅ You selected **{sp.get('title', sp['name'])}**")

    await interaction.response.send_message(
        f"🔍 **Found {len(matches)} matches. Pick one:**",
        view=PickView(matches, lambda s: f"{s.get('title', s['name'])} ({s.get('rarity', '?')})",
                      lambda s: s["name"], "Choose a support...", "🃏", pick))


@bot.event
async def on_ready():
    log.info("Bot listo como %s", bot.user)


if __name__ == "__main__":
    threading.Thread(target=run_dummy_server, daemon=True).start()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise SystemExit("Falta la variable de entorno DISCORD_TOKEN")
    bot.run(token)
