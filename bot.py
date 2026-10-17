
import os
import threading
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Select, View


# =========================================================
# CONFIGURACIÓN
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

log = logging.getLogger("umalator")

EMBED_COLOR = discord.Color.gold()
FOOTER_TEXT = "Umalator CM Helper | Global"

TOKEN = os.getenv("DISCORD_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

if not TOKEN:
    raise RuntimeError(
        "Falta DISCORD_TOKEN. Configúralo en Environment Variables de Render."
    )


# =========================================================
# SERVIDOR HTTP PARA RENDER
# =========================================================

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/", "/health"):
            self.send_error(404)
            return

        body = b"Umalator CM Helper is running."

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format_string, *args):
        # Evita llenar los logs con cada solicitud HTTP.
        return


def run_web_server():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), HealthHandler)
    log.info("Servidor HTTP iniciado en el puerto %s", PORT)
    server.serve_forever()


# =========================================================
# BASE DE DATOS
# IMPORTANTE: Fechas y estrategias pendientes de verificación.
# No presentar estos datos como recomendaciones oficiales.
# =========================================================

CM_DATABASE = {
    "taurus_cup": {
        "name": "Taurus Cup (Tokyo 2400m)",
        "start_time": 1755734400,
        "image_url": None,
        "verified": False,
        "sections": {
            "track_overview": (
                "🏟️ **TRACK INFO & GENERAL OVERVIEW**\n\n"
                "📍 **Pista:** Tokyo Turf 2400m (Medium) - Left - "
                "Spring - Firm\n\n"
                "💡 **Nota:** Datos pendientes de verificar para "
                "la edición correspondiente de Global."
            ),
            "best_umas": (
                "🏇 **BEST UMAS & RUNNING STYLES**\n\n"
                "🏃 **Front Runner:** Silence Suzuka, Seiun Sky\n"
                "🏃 **Pace Chaser:** Narita Brian, Vodka\n"
                "🏃 **Late Surger:** Mejiro Ryan\n"
                "🏃 **End Closer:** Gold Ship\n"
                "🏃 **Debuffer:** Nice Nature\n\n"
                "⚠️ Lista provisional; no constituye un ranking verificado."
            ),
            "inheritance": (
                "🧬 **INHERITANCE & FACTORS**\n\n"
                "📊 **Factores sugeridos:** ★9 Stamina - ★9 Power\n\n"
                "🐴 **Padres sugeridos:** Super Creek, Mejiro Ryan\n\n"
                "⚠️ Los factores y las habilidades heredadas deben "
                "validarse según la pista y la estrategia."
            ),
            "support_cards": (
                "🎴 **SUPPORT CARDS: WHALE VS F2P**\n\n"
                "🐋 **Deck sugerido:** 3 Speed + 2 Stamina + 1 Wit\n"
                "🆓 **Alternativa sugerida:** 3 Speed + 2 Stamina + 1 Guts\n\n"
                "⚠️ Composiciones provisionales. Ajustar a las cartas "
                "disponibles, límites de estadísticas y distancia."
            ),
            "skills_priority": (
                "⚡ **KEY SKILLS & PRIORITY**\n\n"
                "• Swinging Maestro\n"
                "• Medium Straight\n"
                "• Non-Stop Girl\n\n"
                "⚠️ Prioridad y puntos pendientes de verificación "
                "para la edición y las condiciones exactas."
            ),
        },
    },

    "gemini_cup": {
        "name": "Gemini Cup (Kyoto 3200m)",
        "start_time": 1757548800,
        "image_url": None,
        "verified": False,
        "sections": {
            "track_overview": (
                "🏟️ **TRACK INFO & GENERAL OVERVIEW**\n\n"
                "📍 **Pista:** Kyoto Turf 3200m (Long) - Right - "
                "Spring - Firm\n\n"
                "⚠️ Datos de pista y fecha pendientes de verificar "
                "para la edición de Global."
            ),
            "best_umas": (
                "🏇 **BEST UMAS & RUNNING STYLES**\n\n"
                "🏃 **Front Runner:** Rice Shower, Maya no Top Gun\n"
                "🏃 **Pace Chaser:** Narita Brian\n"
                "🏃 **Late Surger:** Mejiro Ryan\n"
                "🏃 **End Closer:** Gold Ship\n"
                "🏃 **Debuffer:** Nice Nature\n\n"
                "⚠️ Selección provisional; el rendimiento depende "
                "del build y las condiciones de carrera."
            ),
            "inheritance": (
                "🧬 **INHERITANCE & FACTORS**\n\n"
                "📊 **Factores sugeridos:** ★12 Stamina - ★6 Guts\n\n"
                "🐴 **Padre sugerido:** Super Creek\n\n"
                "⚠️ Validar factores, herencia y recuperación antes "
                "de utilizar esta configuración."
            ),
            "support_cards": (
                "🎴 **SUPPORT CARDS: WHALE VS F2P**\n\n"
                "🐋 **Deck sugerido:** 2 Speed + 3 Stamina + 1 Wit\n"
                "🆓 **Alternativa sugerida:** 2 Speed + 3 Stamina + 1 Guts\n\n"
                "⚠️ Plantillas provisionales, no builds verificadas."
            ),
            "skills_priority": (
                "⚡ **KEY SKILLS & PRIORITY**\n\n"
                "• Swinging Maestro\n"
                "• Professor of Curvature\n"
                "• Long Distance Straights\n\n"
                "⚠️ Confirmar activación, condiciones y coste de cada "
                "habilidad para esta pista."
            ),
        },
    },

    "sagittarius_cup": {
        "name": "Sagittarius Cup (Nakayama 2500m)",
        "start_time": 1800000000,
        "image_url": None,
        "verified": False,
        "sections": {
            "track_overview": (
                "🏟️ **TRACK INFO & GENERAL OVERVIEW**\n\n"
                "📍 **Pista propuesta:** Nakayama Turf 2500m - "
                "Right / Inner - Winter\n\n"
                "⚠️ Confirmar fecha, estado del terreno y condiciones "
                "de la edición de Global."
            ),
            "best_umas": (
                "🏇 **BEST UMAS & RUNNING STYLES**\n\n"
                "🏃 **Front Runner:** Seiun Sky\n"
                "🏃 **Pace Chaser:** Narita Brian\n"
                "🏃 **Late Surger:** Mejiro Ryan\n"
                "🏃 **End Closer:** Gold Ship\n"
                "🏃 **Debuffer:** Nice Nature\n\n"
                "⚠️ Selección provisional pendiente de datos de carrera."
            ),
            "inheritance": (
                "🧬 **INHERITANCE & FACTORS**\n\n"
                "📊 **Factores sugeridos:** ★6 Power - ★12 Stamina\n\n"
                "🐴 **Padres sugeridos:** Super Creek, Mejiro Dober\n\n"
                "⚠️ Validar las habilidades heredadas y su utilidad "
                "para el trazado concreto."
            ),
            "support_cards": (
                "🎴 **SUPPORT CARDS: WHALE VS F2P**\n\n"
                "🐋 **Deck sugerido:** 2 Speed + 2 Stamina + 2 Wit\n"
                "🆓 **Alternativa:** 3 Speed + 2 Stamina + 1 Wit\n\n"
                "⚠️ Plantillas provisionales."
            ),
            "skills_priority": (
                "⚡ **KEY SKILLS & PRIORITY**\n\n"
                "• Swinging Maestro\n"
                "• Non-Stop Girl\n\n"
                "⚠️ La prioridad depende de la activación y de las "
                "condiciones específicas de la carrera."
            ),
        },
    },

    "capricorn_cup": {
        "name": "Capricorn Cup (Chukyo 1200m)",
        "start_time": 1802000000,
        "image_url": None,
        "verified": False,
        "sections": {
            "track_overview": (
                "🏟️ **TRACK INFO & GENERAL OVERVIEW**\n\n"
                "📍 **Pista propuesta:** Chukyo Turf 1200m - Left - "
                "Winter\n\n"
                "⚠️ Verificar edición, clima, terreno y fecha."
            ),
            "best_umas": (
                "🏇 **BEST UMAS & RUNNING STYLES**\n\n"
                "🏃 **Front Runner:** Sakura Bakushin O, Taiki Shuttle\n"
                "🏃 **Pace Chaser:** Curren Chan\n"
                "🏃 **Late Surger:** Air Groove\n"
                "🏃 **End Closer:** Nishino Flower\n"
                "🏃 **Debuffer:** Grass Wonder\n\n"
                "⚠️ Selección provisional; no es un ranking confirmado."
            ),
            "inheritance": (
                "🧬 **INHERITANCE & FACTORS**\n\n"
                "📊 **Factores sugeridos:** ★9 Speed - ★9 Power\n\n"
                "🐴 **Padre sugerido:** Maruzensky\n\n"
                "⚠️ Verificar herencia y habilidades según el trazado."
            ),
            "support_cards": (
                "🎴 **SUPPORT CARDS: WHALE VS F2P**\n\n"
                "🐋 **Deck sugerido:** 3 Speed + 2 Guts + 1 Wit\n"
                "🆓 **Alternativa:** 3 Speed + 1 Guts + 2 Wit\n\n"
                "⚠️ Plantillas provisionales; ajustar según las cartas."
            ),
            "skills_priority": (
                "⚡ **KEY SKILLS & PRIORITY**\n\n"
                "• Sprint Turbo\n"
                "• Non-Stop Girl\n\n"
                "⚠️ Confirmar coste, condiciones y prioridad antes "
                "de recomendar estas habilidades."
            ),
        },
    },
}


# =========================================================
# CONFIGURACIÓN DE LAS SECCIONES
# =========================================================

SECTION_OPTIONS = [
    ("Track Info & Overview", "track_overview", "🏟️"),
    ("Best Umas & Running Styles", "best_umas", "🏇"),
    ("Inheritance & Factors", "inheritance", "🧬"),
    ("Support Cards: Whale vs F2P", "support_cards", "🎴"),
    ("Skills & Priority", "skills_priority", "⚡"),
]


def make_embed(cm_data, section_key):
    """Construye un embed consistente para cualquier sección."""
    sections = cm_data.get("sections", {})
    description = sections.get(
        section_key,
        "Esta sección todavía no tiene información disponible."
    )

    embed = discord.Embed(
        title=f"🏆 {cm_data['name']}",
        description=description,
        color=EMBED_COLOR,
    )

    if section_key == "track_overview":
        start_time = cm_data.get("start_time")

        if isinstance(start_time, int) and start_time > 0:
            embed.add_field(
                name="📅 Fecha registrada",
                value=f"<t:{start_time}:F> (<t:{start_time}:R>)",
                inline=False,
            )

    image_url = cm_data.get("image_url")
    if image_url:
        embed.set_image(url=image_url)

    if not cm_data.get("verified", False):
        embed.add_field(
            name="⚠️ Estado de la información",
            value=(
                "Datos provisionales. Fechas, pista y recomendaciones "
                "todavía requieren verificación para Global."
            ),
            inline=False,
        )

    embed.set_footer(text=FOOTER_TEXT)
    return embed


# =========================================================
# MENÚ DESPLEGABLE
# =========================================================

class CMSectionSelect(Select):
    def __init__(self, cm_data):
        self.cm_data = cm_data

        options = [
            discord.SelectOption(
                label=label,
                value=key,
                emoji=emoji,
            )
            for label, key, emoji in SECTION_OPTIONS
        ]

        super().__init__(
            placeholder="Selecciona una sección de la CM...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="umalator:cm_section",
        )

    async def callback(self, interaction: discord.Interaction):
        section_key = self.values[0]
        embed = make_embed(self.cm_data, section_key)

        await interaction.response.edit_message(
            content=None,
            embed=embed,
            view=self.view,
        )


class CMSectionView(View):
    def __init__(self, cm_data):
        super().__init__(timeout=900)
        self.add_item(CMSectionSelect(cm_data))


# =========================================================
# BOT Y SINCRONIZACIÓN DE COMANDOS
# =========================================================

intents = discord.Intents.default()
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
)


@bot.event
async def setup_hook():
    # Se ejecuta una vez durante la inicialización del cliente.
    try:
        synced = await bot.tree.sync()
        log.info("Comandos slash sincronizados: %s", len(synced))
    except discord.DiscordException:
        log.exception("No se pudieron sincronizar los comandos slash")
        raise


@bot.event
async def on_ready():
    log.info("Bot conectado como %s (ID: %s)", bot.user, bot.user.id)


# =========================================================
# AUTOCOMPLETADO
# =========================================================

async def cm_autocomplete(
    interaction: discord.Interaction,
    current: str,
):
    current = current.casefold().strip()
    choices = []

    for key, data in CM_DATABASE.items():
        name = data.get("name", key)

        if current in name.casefold() or current in key.casefold():
            choices.append(
                app_commands.Choice(name=name[:100], value=key)
            )

    return choices[:25]


# =========================================================
# COMANDO /cm
# =========================================================

@bot.tree.command(
    name="cm",
    description="Muestra la guía de una Champions Meeting",
)
@app_commands.describe(
    nombre_copa="Selecciona la Champions Meeting que quieres consultar",
)
@app_commands.autocomplete(nombre_copa=cm_autocomplete)
async def slash_cm(
    interaction: discord.Interaction,
    nombre_copa: str,
):
    cm_data = CM_DATABASE.get(nombre_copa)

    if cm_data is None:
        await interaction.response.send_message(
            "❌ No encontré esa Champions Meeting. "
            "Selecciona una opción del autocompletado de `/cm`.",
            ephemeral=True,
        )
        return

    embed = make_embed(cm_data, "track_overview")
    view = CMSectionView(cm_data)

    await interaction.response.send_message(
        embed=embed,
        view=view,
    )


@slash_cm.error
async def slash_cm_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
):
    log.error(
        "Error en /cm",
        exc_info=(type(error), error, error.__traceback__),
    )

    message = (
        "Ocurrió un error al abrir la guía. "
        "Inténtalo de nuevo en unos momentos."
    )

    try:
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(
                message,
                ephemeral=True,
            )
    except discord.DiscordException:
        log.exception("No se pudo enviar el mensaje de error")


# =========================================================
# INICIO
# =========================================================

def main():
    # El servidor web y el bot funcionan en hilos separados.
    web_server = ThreadingHTTPServer(
        ("0.0.0.0", PORT),
        HealthHandler,
    )
    web_thread = threading.Thread(
        target=web_server.serve_forever,
        name="render-health-server",
        daemon=True,
    )
    web_thread.start()

    log.info("Servidor web listo en el puerto %s", PORT)

    try:
        bot.run(TOKEN, log_handler=None)
    finally:
        web_server.shutdown()
        web_server.server_close()


if __name__ == "__main__":
    main()
