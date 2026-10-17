
import os
import json
import logging
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
from aiohttp import web
from dotenv import load_dotenv

# =========================================================
# CONFIGURACIÓN
# =========================================================

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

TOKEN = os.getenv("DISCORD_TOKEN")
DEV_GUILD_ID = os.getenv("DEV_GUILD_ID")
PORT = int(os.getenv("PORT", "10000"))

BRAND = "Umalator CM Helper"
COLOR = discord.Color.from_rgb(41, 67, 91)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

log = logging.getLogger("umalat or_cm_helper")


# =========================================================
# CARGA DE DATOS
# =========================================================

def load_json(filename, fallback):
    path = DATA_DIR / filename

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        log.warning("No existe el archivo: %s", path)
    except json.JSONDecodeError:
        log.exception("JSON inválido: %s", path)
    except OSError:
        log.exception("No se pudo leer: %s", path)

    return fallback


def load_dataset(filename):
    data = load_json(filename, [])

    if not isinstance(data, list):
        log.warning("%s debe contener una lista JSON.", filename)
        return []

    return [item for item in data if isinstance(item, dict)]


SKILLS = load_dataset("skills.json")
SUPPORTS = load_dataset("supports.json")
CM_DATABASE = load_json("cm.json", {})


# =========================================================
# BOT
# IMPORTANTE: SE DEFINE ANTES DE LOS DECORADORES
# =========================================================

intents = discord.Intents.default()


class UmalatorBot(commands.Bot):

    async def setup_hook(self):
        # Sincronizar los comandos slash.
        try:
            if DEV_GUILD_ID:
                guild = discord.Object(id=int(DEV_GUILD_ID))
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                log.info(
                    "Sincronizados %s comandos en el servidor de pruebas.",
                    len(synced)
                )
            else:
                synced = await self.tree.sync()
                log.info(
                    "Sincronizados %s comandos globales.",
                    len(synced)
                )
        except Exception:
            log.exception("Error al sincronizar los comandos.")

        # Endpoint HTTP para comprobaciones de Render.
        app = web.Application()

        async def health(_request):
            return web.json_response({
                "status": "ok",
                "bot": BRAND,
                "discord_connected": self.is_ready()
            })

        async def home(_request):
            return web.Response(text=f"{BRAND} is running.")

        app.router.add_get("/", home)
        app.router.add_get("/health", health)

        runner = web.AppRunner(app)
        await runner.setup()

        site = web.TCPSite(runner, "0.0.0.0", PORT)
        await site.start()

        self._health_runner = runner
        log.info("Servidor HTTP iniciado en el puerto %s.", PORT)


bot = UmalatorBot(
    command_prefix="!",
    intents=intents
)


@bot.event
async def on_ready():
    log.info(
        "Conectado como %s (%s)",
        bot.user,
        bot.user.id
    )


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def make_embed(title, description=""):
    embed = discord.Embed(
        title=title,
        description=description or "Información no disponible.",
        color=COLOR
    )
    embed.set_footer(text=BRAND)
    return embed


def find_matches(dataset, query):
    query = query.casefold().strip()

    if not query:
        return []

    results = []

    for item in dataset:
        searchable = [
            str(item.get("name", "")),
            str(item.get("character", ""))
        ]

        aliases = item.get("aliases", [])
        if isinstance(aliases, list):
            searchable.extend(str(alias) for alias in aliases)

        if any(query in value.casefold() for value in searchable):
            results.append(item)

    return results


def display_value(value, fallback="No verificado"):
    if value is None or value == "":
        return fallback
    return str(value)


def source_field(embed, item):
    url = item.get("source_url")

    if isinstance(url, str) and url.startswith(("https://", "http://")):
        embed.add_field(
            name="Fuente",
            value=f"[Consultar fuente]({url})",
            inline=False
        )


def add_list_field(embed, title, values, limit=8):
    if not isinstance(values, list) or not values:
        return

    text = "\n".join(f"• {value}" for value in values[:limit])

    if len(text) > 1000:
        text = text[:997] + "..."

    embed.add_field(
        name=title,
        value=text,
        inline=False
    )


# =========================================================
# COMANDO /CM
# =========================================================

CM_SECTIONS = {
    "overview": "Vista general",
    "umas": "Mejores Umas",
    "stats": "Stats: Graded y Open",
    "inheritance": "Herencia",
    "supports_whale": "Supports Whale",
    "supports_f2p": "Supports F2P",
    "skills": "Skills por estrategia"
}


def get_cm_section(section):
    sections = CM_DATABASE.get("sections", {})

    if isinstance(sections, dict):
        data = sections.get(section, {})
        if isinstance(data, dict):
            return data

    return {}


def build_cm_embed(section):
    cm_name = CM_DATABASE.get(
        "name",
        "Champions Meeting"
    )

    if section == "overview":
        track = CM_DATABASE.get("track", {})

        embed = make_embed(
            f"🏁 {cm_name}",
            CM_DATABASE.get(
                "summary",
                "Guía del Champions Meeting. Selecciona una sección "
                "del menú para consultar sus recomendaciones."
            )
        )

        if isinstance(track, dict) and track:
            venue = track.get("venue", "No verificado")
            distance = track.get("distance_m", "No verificado")
            distance_type = track.get("distance_type", "No verificado")
            surface = track.get("surface", "No verificado")
            direction = track.get("direction", "No verificado")
            course = track.get("course", "No verificado")
            season = track.get("season", "No verificado")
            weather = track.get("weather", "No verificado")
            ground = track.get("ground", "No verificado")

            embed.add_field(
                name="🏟️ Circuito",
                value=(
                    f"**Sede:** {venue}\n"
                    f"**Distancia:** {distance} m ({distance_type})\n"
                    f"**Superficie:** {surface}\n"
                    f"**Dirección:** {direction}\n"
                    f"**Trazado:** {course}\n"
                    f"**Estación:** {season}\n"
                    f"**Clima:** {weather}\n"
                    f"**Terreno:** {ground}"
                ),
                inline=False
            )

        embed.add_field(
            name="📌 Guía",
            value=(
                "Consulta las estrategias y las builds de cada sección. "
                "Los datos que no hayan sido verificados no se mostrarán "
                "como recomendaciones definitivas."
            ),
            inline=False
        )

        sources = CM_DATABASE.get("sources", [])
        if isinstance(sources, list):
            links = []

            for source in sources[:5]:
                if not isinstance(source, dict):
                    continue

                name = source.get("name", "Fuente")
                url = source.get("url", "")

                if isinstance(url, str) and url.startswith("https://"):
                    links.append(f"• [{name}]({url})")

            if links:
                embed.add_field(
                    name="Fuentes",
                    value="\n".join(links),
                    inline=False
                )

        return embed

    data = get_cm_section(section)

    if not data:
        return make_embed(
            f"🏁 {cm_name} · {CM_SECTIONS.get(section, section)}",
            "Esta sección todavía no tiene datos cargados."
        )

    embed = make_embed(
        f"🏁 {cm_name} · {data.get('title', CM_SECTIONS.get(section, section))}",
        data.get("description", "")
    )

    fields = data.get("fields", [])

    if isinstance(fields, list):
        for field in fields[:20]:
            if not isinstance(field, dict):
                continue

            value = str(field.get("value", "Información no disponible."))

            if len(value) > 1024:
                value = value[:1021] + "..."

            embed.add_field(
                name=str(field.get("name", "Información"))[:256],
                value=value or "Información no disponible.",
                inline=bool(field.get("inline", False))
            )

    return embed


class CMSelect(discord.ui.Select):

    def __init__(self):
        options = [
            discord.SelectOption(
                label="Vista general",
                value="overview",
                emoji="🏁",
                default=True
            ),
            discord.SelectOption(
                label="Mejores Umas",
                value="umas",
                emoji="🐎"
            ),
            discord.SelectOption(
                label="Stats: Graded y Open",
                value="stats",
                emoji="📊"
            ),
            discord.SelectOption(
                label="Herencia",
                value="inheritance",
                emoji="🧬"
            ),
            discord.SelectOption(
                label="Supports Whale",
                value="supports_whale",
                emoji="💳"
            ),
            discord.SelectOption(
                label="Supports F2P",
                value="supports_f2p",
                emoji="🆓"
            ),
            discord.SelectOption(
                label="Skills por estrategia",
                value="skills",
                emoji="✨"
            )
        ]

        super().__init__(
            placeholder="Selecciona una sección de la guía...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        section = self.values[0]

        for option in self.options:
            option.default = option.value == section

        await interaction.response.edit_message(
            embed=build_cm_embed(section),
            view=self.view
        )


class CMView(discord.ui.View):

    def __init__(self, owner_id):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.add_item(CMSelect())

    async def interaction_check(self, interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "Ejecuta `/cm` para abrir tu propia guía.",
                ephemeral=True
            )
            return False

        return True


@bot.tree.command(
    name="cm",
    description="Consulta la guía del Champions Meeting."
)
async def cm(interaction: discord.Interaction):
    await interaction.response.send_message(
        embed=build_cm_embed("overview"),
        view=CMView(interaction.user.id)
    )


# =========================================================
# COMANDO /SKILL
# =========================================================

@bot.tree.command(
    name="skill",
    description="Busca una skill de Umamusume Global."
)
@app_commands.describe(
    nombre="Nombre oficial o parte del nombre de la skill"
)
async def skill(
    interaction: discord.Interaction,
    nombre: str
):
    matches = find_matches(SKILLS, nombre)

    if not matches:
        await interaction.response.send_message(
            f"No encontré **{discord.utils.escape_markdown(nombre)}** "
            "en el dataset local de skills.",
            ephemeral=True
        )
        return

    if len(matches) > 1:
        choices = "\n".join(
            f"• {item.get('name', 'Sin nombre')}"
            for item in matches[:10]
        )

        await interaction.response.send_message(
            f"Encontré varias coincidencias:\n{choices}\n\n"
            "Escribe un nombre más específico.",
            ephemeral=True
        )
        return

    item = matches[0]

    embed = make_embed(
        f"✨ {item.get('name', 'Skill')}",
        item.get("description", "Descripción no verificada.")
    )

    embed.add_field(
        name="Tipo",
        value=display_value(item.get("type")),
        inline=True
    )
    embed.add_field(
        name="Coste SP",
        value=display_value(item.get("sp_cost")),
        inline=True
    )
    embed.add_field(
        name="Rating ○",
        value=display_value(item.get("rating_o")),
        inline=True
    )
    embed.add_field(
        name="Rating ◎",
        value=display_value(item.get("rating_oo")),
        inline=True
    )

    add_list_field(
        embed,
        "Variantes",
        item.get("variants", [])
    )

    source_field(embed, item)

    await interaction.response.send_message(embed=embed)


# =========================================================
# COMANDO /SUPPORT
# =========================================================

@bot.tree.command(
    name="support",
    description="Busca una Support Card de Umamusume Global."
)
@app_commands.describe(
    nombre="Nombre de la carta o del personaje"
)
async def support(
    interaction: discord.Interaction,
    nombre: str
):
    matches = find_matches(SUPPORTS, nombre)

    if not matches:
        await interaction.response.send_message(
            f"No encontré **{discord.utils.escape_markdown(nombre)}** "
            "en el dataset local de supports.",
            ephemeral=True
        )
        return

    if len(matches) > 1:
        choices = "\n".join(
            f"• {item.get('name', 'Sin nombre')}"
            for item in matches[:10]
        )

        await interaction.response.send_message(
            f"Encontré varias cartas:\n{choices}\n\n"
            "Escribe un nombre más específico.",
            ephemeral=True
        )
        return

    item = matches[0]

    embed = make_embed(
        f"🃏 {item.get('name', 'Support Card')}",
        f"**Personaje:** {item.get('character', 'No verificado')}"
    )

    embed.add_field(
        name="Rareza",
        value=display_value(item.get("rarity")),
        inline=True
    )
    embed.add_field(
        name="Tipo",
        value=display_value(item.get("type")),
        inline=True
    )
    embed.add_field(
        name="Limit Break",
        value=display_value(item.get("limit_break")),
        inline=True
    )

    add_list_field(
        embed,
        "Efectos",
        item.get("effects", [])
    )

    add_list_field(
        embed,
        "Skills y hints",
        item.get("hints", [])
    )

    source_field(embed, item)

    await interaction.response.send_message(embed=embed)


# =========================================================
# INICIO
# =========================================================

if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError(
            "No se encontró DISCORD_TOKEN en las variables de entorno."
        )

    bot.run(TOKEN)
