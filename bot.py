
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import discord
from discord import app_commands
from discord.ext import commands


# =========================================================
# CONFIGURACIÓN
# =========================================================

TOKEN = os.getenv("DISCORD_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

GOLD = 0xD4AF37
DARK = 0x202225

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# =========================================================
# DATOS DE LA CHAMPIONS MEETING
# CM20 - SAGITTARIUS CUP
# =========================================================

CM_DATABASE = {
    "cm20": {
        "name": "CM20 — Sagittarius Cup",
        "subtitle": "Champions Meeting • Global",
        "track": "Nakayama Turf",
        "distance": "2500 m",
        "distance_type": "Long",
        "direction": "Right-handed",
        "course": "Inner course",
        "season": "Winter",
        "weather": "Cloudy",
        "ground": "Good",
        "source": "https://uma.guide/guides/cm20-guide",
        "official_source": (
            "https://umamusume.gg/"
            "the-league-selection-period-for-the-champions-meeting-"
            "sagittarius-cup-has-begun/"
        ),
        "sections": {
            "overview": {
                "title": "Track Info & Overview",
                "description": (
                    "Información del circuito y sus condiciones. "
                    "Estos parámetros determinan qué habilidades "
                    "y aptitudes pueden ser útiles."
                ),
                "fields": [
                    (
                        "🏟️ Circuito",
                        "Nakayama Turf — 2500 m\n"
                        "Distancia: Long\n"
                        "Superficie: Turf\n"
                        "Recorrido: Inner course"
                    ),
                    (
                        "🌦️ Condiciones",
                        "Dirección: Right-handed\n"
                        "Temporada: Winter\n"
                        "Clima: Cloudy\n"
                        "Pista: Good"
                    ),
                    (
                        "📌 Qué significa para tu build",
                        "Prioriza una Uma con aptitud Long y Turf "
                        "adecuada. La distancia exige administrar bien "
                        "la stamina; no basta con maximizar Speed."
                    ),
                    (
                        "⚠️ Importante",
                        "Los objetivos de estadísticas son referencias "
                        "para la Graded League, no requisitos oficiales "
                        "ni una garantía de victoria."
                    ),
                ],
            },

            "umas": {
                "title": "Best Umas & Running Styles",
                "description": (
                    "Cómo elegir tus tres corredoras sin depender "
                    "de una tier list que puede cambiar según las "
                    "habilidades, herencias y supports disponibles."
                ),
                "fields": [
                    (
                        "🏃 Front Runner",
                        "Puede intentar mantener la ventaja desde el "
                        "inicio. Necesita una salida y una estrategia "
                        "de velocidad consistentes; si pierde la "
                        "posición, su plan puede complicarse."
                    ),
                    (
                        "🏃 Pace Chaser",
                        "Corre detrás de las líderes. Busca una build "
                        "equilibrada con velocidad, stamina y una buena "
                        "aceleración para el tramo decisivo."
                    ),
                    (
                        "🏃 Late Surger",
                        "Guarda posición para avanzar más tarde. "
                        "Conviene revisar que sus habilidades se "
                        "activen en el momento correcto y no dependan "
                        "de condiciones difíciles de cumplir."
                    ),
                    (
                        "🏃 End Closer",
                        "Avanza desde atrás y puede aprovechar "
                        "aceleraciones de final de carrera. Necesita "
                        "habilidades compatibles con su estilo y "
                        "suficiente velocidad para rematar."
                    ),
                    (
                        "🧩 Cómo elegir",
                        "Compara las aptitudes de Turf y Long, el "
                        "estilo preferido, las habilidades únicas y "
                        "las opciones de aceleración de cada Uma. "
                        "No elijas solo por rareza o popularidad."
                    ),
                    (
                        "👥 Equipo de tres",
                        "Prueba combinaciones que puedan competir "
                        "por posiciones distintas. Después revisa "
                        "las carreras de práctica para detectar "
                        "problemas de stamina, posicionamiento "
                        "o activación de skills."
                    ),
                ],
            },

            "inheritance": {
                "title": "Inheritance & Factors",
                "description": (
                    "La herencia debe ayudar a alcanzar las aptitudes "
                    "y estadísticas que tu build necesita."
                ),
                "fields": [
                    (
                        "🧬 Prioridad de aptitudes",
                        "Revisa primero Turf y Long. Mejorar una "
                        "aptitud relevante puede ser más valioso "
                        "que acumular factores sin un objetivo claro."
                    ),
                    (
                        "💙 Factores azules",
                        "Stamina puede ayudar a llegar al objetivo "
                        "de resistencia sin dedicar tantos turnos "
                        "de entrenamiento a esa estadística."
                    ),
                    (
                        "🟠 Factores rojos",
                        "Busca factores compatibles con las aptitudes "
                        "que quieras mejorar. No se puede garantizar "
                        "un rango S: el resultado depende de la herencia."
                    ),
                    (
                        "⚪ Factores blancos",
                        "Prioriza skills heredables que encajen con "
                        "el estilo de carrera y el circuito. También "
                        "pueden ayudar los factores que aporten "
                        "estadísticas mediante eventos de herencia."
                    ),
                    (
                        "📋 Antes de entrenar",
                        "Define una meta de estadísticas y skills. "
                        "Después escoge los padres que te acerquen "
                        "a esa meta; no al revés."
                    ),
                ],
            },

            "supports": {
                "title": "Support Cards — Whale vs F2P",
                "description": (
                    "Una estructura de deck para adaptar a las cartas "
                    "que realmente tienes. No presupone que poseas "
                    "cartas limitadas o copias MLB."
                ),
                "fields": [
                    (
                        "🐳 Cuenta con muchos recursos",
                        "Usa supports de alto rendimiento para entrenar "
                        "Speed, Power y Wit, y ajusta el deck para "
                        "alcanzar la stamina necesaria. Una carta "
                        "de stamina puede ser útil si la herencia "
                        "no aporta suficientes puntos."
                    ),
                    (
                        "🆓 F2P",
                        "Prioriza cartas gratuitas o fáciles de "
                        "mejorar que tengan niveles altos y buenas "
                        "bonificaciones. Una carta bien desarrollada "
                        "puede rendir mejor que una SSR poco mejorada."
                    ),
                    (
                        "📚 Roles útiles",
                        "Speed: elevar la velocidad final.\n"
                        "Stamina: cubrir el coste de 2500 m.\n"
                        "Power: aceleración y movimiento.\n"
                        "Wit: consistencia de skills y posicionamiento.\n"
                        "Friend/Group: apoyo según el escenario."
                    ),
                    (
                        "📊 Punto de partida",
                        "Prueba varios decks y compara los resultados "
                        "finales, las skills obtenidas y la estabilidad "
                        "de los entrenamientos. La composición óptima "
                        "depende de tus niveles y del escenario."
                    ),
                    (
                        "⚠️ No copies un deck a ciegas",
                        "Comprueba el nivel de cada support, sus "
                        "bonificaciones y las skills que realmente "
                        "puede enseñar. Los decks de jugadores con "
                        "muchas copias no siempre son reproducibles."
                    ),
                ],
            },

            "skills": {
                "title": "Skills & Priority",
                "description": (
                    "En CM20 importa tanto el efecto de una skill "
                    "como su zona de activación y sus condiciones."
                ),
                "fields": [
                    (
                        "🚀 Aceleración en la recta",
                        "La guía de CM20 destaca habilidades como "
                        "Victory Cheer!, Break It Down! y "
                        "Straightaway Spurt / Encroaching Shadow "
                        "por su posible utilidad en la fase final. "
                        "Comprueba que tu Uma cumpla sus condiciones."
                    ),
                    (
                        "↪️ Aceleración en curva",
                        "Angling and Scheming y otras habilidades "
                        "de aceleración en curva pueden ser opciones "
                        "viables, según el estilo y la posición "
                        "de la corredora."
                    ),
                    (
                        "💨 Velocidad",
                        "Las skills de velocidad son útiles cuando "
                        "se activan en una fase relevante. Evita "
                        "gastar puntos solo porque una skill sea "
                        "dorada: importa su efecto real en este track."
                    ),
                    (
                        "💚 Skills verdes compatibles",
                        "Revisa las skills relacionadas con "
                        "Nakayama Racecourse, Right-Handed, "
                        "Winter Runner y Cloudy Days. Comprueba "
                        "los nombres y requisitos en el cliente "
                        "Global antes de comprar cada skill."
                    ),
                    (
                        "⛔ Skills que no activan",
                        "La información de CM20 indica que Night "
                        "Races y Sharp Turns no se activan en esta "
                        "copa. No inviertas puntos en ellas para "
                        "esta carrera."
                    ),
                    (
                        "🧠 Orden recomendado",
                        "1. Aceleración apropiada para tu estilo.\n"
                        "2. Recuperación suficiente para 2500 m.\n"
                        "3. Skills de velocidad con buena activación.\n"
                        "4. Skills verdes compatibles y económicas.\n"
                        "5. Opciones situacionales si sobran puntos."
                    ),
                ],
            },
        },
    }
}


# =========================================================
# EMBEDS
# =========================================================

def make_embed(cm_key: str, section_key: str) -> discord.Embed:
    cm = CM_DATABASE[cm_key]
    section = cm["sections"][section_key]

    embed = discord.Embed(
        title=f"🏇 {cm['name']}",
        description=(
            f"**{section['title']}**\n"
            f"{section['description']}"
        ),
        color=GOLD,
    )

    embed.set_author(
        name="Umalator CM Helper",
        icon_url="https://cdn.discordapp.com/embed/avatars/0.png",
    )

    embed.add_field(
        name="📍 Track",
        value=(
            f"**{cm['track']}** • {cm['distance']}\n"
            f"{cm['distance_type']} | {cm['direction']} | "
            f"{cm['ground']}"
        ),
        inline=False,
    )

    for field_name, field_value in section["fields"]:
        # Discord limita cada valor de campo a 1024 caracteres.
        embed.add_field(
            name=field_name[:256],
            value=field_value[:1024],
            inline=False,
        )

    embed.add_field(
        name="🔗 Fuentes",
        value=(
            f"[Guía técnica de CM20]({cm['source']})\n"
            f"[Anuncio oficial del evento]({cm['official_source']})"
        ),
        inline=False,
    )

    embed.set_footer(
        text="Umalator CM Helper • Global • Datos de CM20"
    )

    return embed


# =========================================================
# SELECT MENU Y NAVEGACIÓN
# =========================================================

SECTION_OPTIONS = [
    discord.SelectOption(
        label="Track Info & Overview",
        value="overview",
        emoji="🗺️",
        description="Circuito, distancia y condiciones",
    ),
    discord.SelectOption(
        label="Best Umas & Running Styles",
        value="umas",
        emoji="🏇",
        description="Estilos de carrera y selección de Umas",
    ),
    discord.SelectOption(
        label="Inheritance & Factors",
        value="inheritance",
        emoji="🧬",
        description="Herencia, aptitudes y factores",
    ),
    discord.SelectOption(
        label="Support Cards — Whale vs F2P",
        value="supports",
        emoji="🃏",
        description="Roles de supports y opciones F2P",
    ),
    discord.SelectOption(
        label="Skills & Priority",
        value="skills",
        emoji="⚡",
        description="Aceleración, velocidad y skills verdes",
    ),
]


class CMSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="Selecciona una sección de la guía...",
            min_values=1,
            max_values=1,
            options=SECTION_OPTIONS,
            custom_id="umalator_cm_section",
        )

    async def callback(self, interaction: discord.Interaction):
        section_key = self.values[0]
        self.view.current_section = section_key

        await interaction.response.edit_message(
            embed=make_embed("cm20", section_key),
            view=self.view,
        )


class HomeButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Overview",
            emoji="🏠",
            style=discord.ButtonStyle.secondary,
            custom_id="umalator_cm_home",
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.current_section = "overview"

        await interaction.response.edit_message(
            embed=make_embed("cm20", "overview"),
            view=self.view,
        )


class CMView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=600)
        self.current_section = "overview"
        self.add_item(CMSelect())
        self.add_item(HomeButton())


# =========================================================
# SLASH COMMAND
# =========================================================

@bot.tree.command(
    name="cm",
    description="Abre la guía de Champions Meeting CM20.",
)
async def cm_command(interaction: discord.Interaction):
    view = CMView()

    await interaction.response.send_message(
        embed=make_embed("cm20", "overview"),
        view=view,
    )


@bot.tree.command(
    name="cmhelp",
    description="Muestra información sobre Umalator CM Helper.",
)
async def cmhelp_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🏇 Umalator CM Helper",
        description=(
            "Guía de Champions Meeting para Umamusume: Pretty Derby.\n\n"
            "**Comandos disponibles**\n"
            "`/cm` — abrir la guía de CM20.\n"
            "`/cmhelp` — mostrar esta ayuda."
        ),
        color=GOLD,
    )

    embed.set_footer(text="Más guías se pueden añadir a CM_DATABASE.")

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True,
    )


# =========================================================
# SERVIDOR HTTP PARA RENDER
# =========================================================

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/health"):
            body = b"Umalator CM Helper is running."
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Evita llenar los logs de Render con cada solicitud.
        return


def run_http_server():
    server = ThreadingHTTPServer(
        ("0.0.0.0", PORT),
        HealthHandler,
    )
    server.serve_forever()


# =========================================================
# ARRANQUE DEL BOT
# =========================================================

@bot.event
async def on_ready():
    print(f"Conectado como {bot.user} (ID: {bot.user.id})")

    try:
        synced = await bot.tree.sync()
        print(f"Slash commands sincronizados: {len(synced)}")
    except Exception as error:
        print(f"Error sincronizando slash commands: {error}")


if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError(
            "Falta DISCORD_TOKEN en las variables de entorno."
        )

    http_thread = threading.Thread(
        target=run_http_server,
        daemon=True,
    )
    http_thread.start()

    bot.run(TOKEN)
