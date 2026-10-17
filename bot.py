import os
import threading
import json
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Select, View

# --- MINI SERVIDOR WEB PARA RENDER ---
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot activo 24/7")

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- CONFIGURACIÓN DEL BOT ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- BASE DE DATOS DE ACCELS META ---
ACCEL_DATABASE = {
    "Short": (
        "• **Runner:** *Angling x Scheming* (Seiun Sky) + *Sprint Turbo*.\n"
        "• **Leader:** *Red Flame* / Accels de recta corta.\n"
        "• **Betweener / Chaser:** *Anabolic* (Ryan) + *Sprint Acceleration*."
    ),
    "Mile": (
        "• **Runner:** *Angling x Scheming* (Seiun Sky Inherit - Obligatorio).\n"
        "• **Leader:** *Red Flame* / Accels de aceleración en recta final.\n"
        "• **Betweener / Chaser:** *Anabolic* (Ryan Inherit) + *Non-stop Girl*."
    ),
    "Medium": (
        "• **Runner:** *Angling x Scheming* + *Do Ya Breaking*.\n"
        "• **Leader:** *Victory Shot!* (Taiki) / Accels de 3ra curva.\n"
        "• **Betweener / Chaser:** *Anabolic* + *Kanata* (Dober Inherit)."
    ),
    "Long": (
        "• **Runner:** *Angling x Scheming* + Control estricto de Stamina/Gold Recovery.\n"
        "• **Leader:** *Shadow Break* (Narita Brian).\n"
        "• **Betweener / Chaser:** *Anabolic* + *Kanata* + Gold Recovery skills."
    )
}

def fetch_latest_cm_data():
    """Consulta segura a la API/web externa para evitar bloqueos."""
    try:
        req = urllib.request.Request(
            "https://raw.githubusercontent.com/uma-musume-db/cm-data/main/current_cm.json",
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=2) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Aviso (usando respaldo): {e}")
        return {
            "name": "Champions Meeting (Próxima)",
            "track": "Tokyo 1600m (Mile)",
            "category": "Mile",
            "start_time": 1815782400,
            "end_time": 1816300800
        }

# --- INTERFAZ UI (SELECT MENU & EMBED) ---
class CMSelect(Select):
    def __init__(self, cm_info):
        self.cm_info = cm_info
        options = [
            discord.SelectOption(
                label=cm_info.get("name", "Champions Meeting Actual"),
                description=f"Pista: {cm_info.get('track', 'Tokyo 1600m')}",
                value="cm_auto",
                emoji="🏆"
            )
        ]
        super().__init__(placeholder="Selecciona una Champions Meeting...", options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.cm_info.get("category", "Mile")
        accels = ACCEL_DATABASE.get(category, ACCEL_DATABASE["Mile"])
        
        embed = discord.Embed(
            title=f"🏆 {self.cm_info.get('name')}",
            description=f"📍 **Pista:** {self.cm_info.get('track')}",
            color=discord.Color.gold()
        )
        
        start_ts = self.cm_info.get("start_time", 1815782400)
        end_ts = self.cm_info.get("end_time", 1816300800)
        
        inicio_fmt = f"<t:{start_ts}:F> (<t:{start_ts}:R>)"
        fin_fmt = f"<t:{end_ts}:F> (<t:{end_ts}:R>)"
        
        embed.add_field(name="📅 Inicio", value=inicio_fmt, inline=False)
        embed.add_field(name="🏁 Finalización", value=fin_fmt, inline=False)
        embed.add_field(name="⚡ Accels Meta Recomendados", value=accels, inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class CMView(View):
    def __init__(self, cm_info):
        super().__init__()
        self.add_item(CMSelect(cm_info))

# --- SLASH COMMANDS (CON /) ---

@bot.tree.command(name="cm", description="Muestra el calendario y los accels meta de la Champions Meeting actual")
async def slash_cm(interaction: discord.Interaction):
    cm_info = fetch_latest_cm_data()
    embed = discord.Embed(
        title="🏆 Guía de Champions Meeting",
        description="Selecciona una opción del menú desplegable para consultar las fechas locales y los accels recomendados.",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, view=CMView(cm_info))

# --- EVENTO AL ENCENDER ---
@bot.event
async def on_ready():
    try:
        # Sincroniza los Slash Commands con Discord globalmente
        synced = await bot.tree.sync()
        print(f"Sincronizados exitosamente {len(synced)} comandos Slash.")
    except Exception as e:
        print(f"Error al sincronizar comandos Slash: {e}")
    print(f'Bot encendido con éxito como {bot.user}')

# --- INICIALIZAR BOT ---
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("Error: No se encontró la variable DISCORD_TOKEN.")
