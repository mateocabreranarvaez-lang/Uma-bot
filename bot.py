import os
import threading
from typing import Optional
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

# --- BASE DE DATOS DE CMs Y SUS SECCIONES DE UMALATOR ---
CM_DATABASE = {
    "sagittarius_cup": {
        "name": "Sagittarius Cup (Nakayama 2500m)",
        "start_time": 1800000000, # Reemplazar con timestamp Unix real
        "end_time": 1800500000,
        "sections": {
            "stats": "📊 **Stats Recomendadas:**\n• Speed: 1200+\n• Stamina: 900+ (con 2 Gold Recovery)\n• Power: 1000+\n• Guts: 600+\n• Wit: 800+",
            "umas": "🐴 **Umas Meta Recomendadas:**\n• **Runners:** Seiun Sky, Daiwa Scarlet\n• **Leaders:** Narita Brian, Grass Wonder\n• **Betweeners:** Mejiro Ryan, Symboli Rudolf\n• **Chasers:** Gold Ship",
            "inherits": "🧬 **Herencias / Inherits Principales:**\n• *Angling x Scheming* (Seiun Sky)\n• *Anabolic* (Mejiro Ryan)\n• *Kanata, Until the Skies Scream* (Mejiro Dober)",
            "skills": "⚡ **Accels y Skills Clave:**\n• *Non-stop Girl*\n• *Straightaway Spurt* / *Spurt Acceleration*\n• Gold Recovery Skills (*Arc Maestro*, *Cool Down*)",
            "estilos": "🏃 **Estrategia por Estilo:**\n• **Runner:** Dominar recta inicial y activar Seiun inherit.\n• **Leader:** Mantener posición alta sin gastar stamina extra.\n• **Betweener/Chaser:** Guardar stamina para burst en la 3ra/4ta curva."
        }
    },
    "sprint_cup": {
        "name": "Sprint Cup (Nakayama 1200m)",
        "start_time": 1802000000,
        "end_time": 1802500000,
        "sections": {
            "stats": "📊 **Stats Recomendadas:**\n• Speed: 1200+\n• Stamina: 450-500\n• Power: 1100+\n• Guts: 800+\n• Wit: 900+",
            "umas": "🐴 **Umas Meta Recomendadas:**\n• **Runners:** Bakushin O, Taiki Shuttle\n• **Leaders:** Curren Chan, King Halo\n• **Betweeners/Chasers:** Air Groove, Nishino Flower",
            "inherits": "🧬 **Herencias / Inherits Principales:**\n• *Red Flame* (Maruzensky)\n• *Plan X* / Accels de distancia corta",
            "skills": "⚡ **Accels y Skills Clave:**\n• *Sprint Turbo*\n• *Sprint Acceleration*\n• *Upbeat Spurt*",
            "estilos": "🏃 **Estrategia por Estilo:**\n• **Runner/Leader:** Aceleración explosiva en salida.\n• **Betweener:** Posicionarse temprano antes de la recta corta."
        }
    }
}

# --- MENÚ DESPLEGABLE DE SECCIONES (STATS, UMAS, HERENCIAS, SKILLS, ESTILOS) ---
class CMSectionSelect(Select):
    def __init__(self, cm_data):
        self.cm_data = cm_data
        options = [
            discord.SelectOption(label="Stats Recomendadas", value="stats", emoji="📊", description="Ver estadísticas objetivas"),
            discord.SelectOption(label="Umas Meta", value="umas", emoji="🐴", description="Ver personajes recomendados"),
            discord.SelectOption(label="Herencias / Inherits", value="inherits", emoji="🧬", description="Ver habilidades a heredar"),
            discord.SelectOption(label="Accels y Skills", value="skills", emoji="⚡", description="Ver aceleraciones clave"),
            discord.SelectOption(label="Estilos de Carrera", value="estilos", emoji="🏃", description="Estrategia por posición")
        ]
        super().__init__(placeholder="SELECCIONA UNA SECCIÓN DE LA CM...", options=options)

    async def callback(self, interaction: discord.Interaction):
        section_key = self.values[0]
        content = self.cm_data["sections"].get(section_key, "Información no disponible.")
        
        embed = discord.Embed(
            title=f"🏆 {self.cm_data['name']}",
            description=content,
            color=discord.Color.gold()
        )
        
        start_ts = self.cm_data["start_time"]
        end_ts = self.cm_data["end_time"]
        embed.add_field(name="📅 Fecha de Inicio", value=f"<t:{start_ts}:F> (<t:{start_ts}:R>)", inline=False)
        embed.add_field(name="🏁 Fecha de Fin", value=f"<t:{end_ts}:F> (<t:{end_ts}:R>)", inline=False)
        embed.set_footer(text="Umalator CM Helper • Usa el menú para cambiar de sección")
        
        # Publico para todo el canal
        await interaction.response.send_message(embed=embed)

class CMSectionView(View):
    def __init__(self, cm_data):
        super().__init__()
        self.add_item(CMSectionSelect(cm_data))

# --- COMANDO SLASH CON BÚSQUEDA POR NOMBRE ---
@bot.tree.command(name="cm", description="Busca la guía de una Champions Meeting específica")
@app_commands.describe(nombre_copa="Escribe el nombre de la CM (ej: Sagittarius, Sprint)")
async def slash_cm(interaction: discord.Interaction, nombre_copa: Optional[str] = None):
    # Si el usuario NO escribe nada en nombre_copa
    if not nombre_copa:
        copas_disponibles = "\n• ".join([data["name"] for data in CM_DATABASE.values()])
        embed_error = discord.Embed(
            title="⚠️ Especifica una Champions Meeting",
            description=(
                "Por favor, escribe el nombre de la Champions Meeting que quieras buscar.\n\n"
                f"**Copas disponibles actualmente:**\n• {copas_disponibles}\n\n"
                "**Ejemplo de uso:** `/cm Sagittarius`"
            ),
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed_error, ephemeral=True)
        return

    # Buscar coincidencia en la base de datos
    busqueda = nombre_copa.lower().strip()
    cm_encontrada = None
    
    for key, data in CM_DATABASE.items():
        if busqueda in key or busqueda in data["name"].lower():
            cm_encontrada = data
            break

    # Si escribió algo pero no se encontró
    if not cm_encontrada:
        await interaction.response.send_message(
            f"❌ No se encontró la Champions Meeting **'{nombre_copa}'**. Por favor revisa el nombre e intenta de nuevo.",
            ephemeral=True
        )
        return

    # Si se encontró la copa, mostramos el menú con sus 5 secciones
    embed_init = discord.Embed(
        title=f"🏆 {cm_encontrada['name']}",
        description="Selecciona abajo la sección que deseas consultar (Stats, Umas, Herencias, Skills o Estilos):",
        color=discord.Color.blue()
    )
    start_ts = cm_encontrada["start_time"]
    end_ts = cm_encontrada["end_time"]
    embed_init.add_field(name="📅 Inicio", value=f"<t:{start_ts}:F>", inline=True)
    embed_init.add_field(name="🏁 Fin", value=f"<t:{end_ts}:F>", inline=True)
    
    await interaction.response.send_message(embed=embed_init, view=CMSectionView(cm_encontrada))

# --- EVENTO AL ENCENDER ---
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos Slash.")
    except Exception as e:
        print(f"Error sincronizando comandos: {e}")
    print(f'Bot encendido correctamente como {bot.user}')

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
