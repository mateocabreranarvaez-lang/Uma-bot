import os
import threading
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Select, View

# --- MINI SERVIDOR WEB PARA RENDER ---
from http.server import HTTPServer, BaseHTTPRequestHandler

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

# --- BASE DE DATOS DE CHAMPIONS MEETINGS ESPECÍFICAS ---
# Puedes cambiar los títulos, pistas y timestamps aquí fácilmente.
CM_DATABASE = {
    "sagittarius_cup": {
        "title": "🏆 Sagittarius Cup (Long / 2500m)",
        "track": "Nakayama 2500m (Long - Derecha - Interior)",
        "category": "Long",
        "start_time": 1800000000,  # Reemplaza con tu timestamp real de Hammertime
        "end_time": 1800500000,
        "accels": (
            "• **Runner:** *Angling x Scheming* (Seiun Sky) + *Do Ya Breaking*.\n"
            "• **Leader:** *Shadow Break* (Narita Brian).\n"
            "• **Betweener / Chaser:** *Anabolic* (Ryan) + *Kanata* (Dober)."
        )
    },
    "sprint_cup": {
        "title": "🏆 Champions Meeting de Sprint",
        "track": "Nakayama 1200m (Sprint - Derecha - Exterior)",
        "category": "Short",
        "start_time": 1802000000,  # Reemplaza con tu timestamp real
        "end_time": 1802500000,
        "accels": (
            "• **Runner:** *Angling x Scheming* + *Sprint Turbo*.\n"
            "• **Leader:** *Red Flame* / Accels de recta corta.\n"
            "• **Betweener / Chaser:** *Anabolic* + *Non-stop Girl*."
        )
    },
    "tokyo_mile": {
        "title": "🏆 Champions Meeting: Tokyo Mile",
        "track": "Tokyo 1600m (Mile - Izquierda - Línea recta larga)",
        "category": "Mile",
        "start_time": 1815782400,
        "end_time": 1816300800,
        "accels": (
            "• **Runner:** *Angling x Scheming* (Obligatorio).\n"
            "• **Leader:** *Red Flame* / Accels de aceleración en recta final.\n"
            "• **Betweener / Chaser:** *Anabolic* + *Non-stop Girl*."
        )
    }
}

# --- MENÚ DESPLEGABLE CON MÚLTIPLES OPCIONES ---
class CMSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Sagittarius Cup (Long)",
                description="Nakayama 2500m",
                value="sagittarius_cup",
                emoji="🎯"
            ),
            discord.SelectOption(
                label="Próxima CM de Sprint",
                description="Nakayama 1200m",
                value="sprint_cup",
                emoji="⚡"
            ),
            discord.SelectOption(
                label="CM Tokyo 1600m (Mile)",
                description="Tokyo 1600m",
                value="tokyo_mile",
                emoji="🏆"
            )
        ]
        super().__init__(placeholder="Elige una Champions Meeting para consultar...", options=options)

    async def callback(self, interaction: discord.Interaction):
        cm = CM_DATABASE.get(self.values[0])
        
        if cm:
            embed = discord.Embed(
                title=cm["title"],
                description=f"📍 **Pista:** {cm['track']}",
                color=discord.Color.gold()
            )
            
            start_ts = cm["start_time"]
            end_ts = cm["end_time"]
            
            inicio_fmt = f"<t:{start_ts}:F> (<t:{start_ts}:R>)"
            fin_fmt = f"<t:{end_ts}:F> (<t:{end_ts}:R>)"
            
            embed.add_field(name="📅 Inicio", value=inicio_fmt, inline=False)
            embed.add_field(name="🏁 Finalización", value=fin_fmt, inline=False)
            embed.add_field(name="⚡ Accels Meta Recomendados", value=cm["accels"], inline=False)
            
            # NOTA: Sin ephemeral=True para que salga visible para todo el canal
            await interaction.response.send_message(embed=embed)

class CMView(View):
    def __init__(self):
        super().__init__()
        self.add_item(CMSelect())

# --- SLASH COMMAND ---
@bot.tree.command(name="cm", description="Muestra el menú para consultar los datos y horarios de las Champions Meetings")
async def slash_cm(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🏆 Guía de Champions Meeting - Uma Musume",
        description="Selecciona en el menú desplegable de abajo la Champions Meeting que quieras consultar:",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, view=CMView())

# --- EVENTO AL ENCENDER ---
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos Slash.")
    except Exception as e:
        print(f"Error al sincronizar comandos: {e}")
    print(f'Bot encendido correctamente como {bot.user}')

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
