import os
import threading
from typing import Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Select, View

# --- MINI SERVIDOR WEB PARA RENDER (24/7) ---
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

# --- BASE DE DATOS DE CMs Y SECCIONES DE UMALATOR ---
CM_DATABASE = {
    "sagittarius_cup": {
        "name": "Sagittarius Cup (Long / 2500m)",
        "track": "Nakayama 2500m (Long - Derecha - Interior)",
        "category": "Long (Largo)",
        "start_time": 1800000000,  # Timestamp Unix de inicio
        "end_time": 1800500000,    # Timestamp Unix de fin
        "sections": {
            "stats": (
                "📊 **Stats Recomendadas:**\n"
                "• **Speed:** 1200+ (Máximo)\n"
                "• **Stamina:** 900+ (Obligatorio con al menos 2 Skills Gold Recovery)\n"
                "• **Power:** 1000+\n"
                "• **Guts:** 600+\n"
                "• **Wit:** 800+"
            ),
            "umas": (
                "🐴 **Umas Meta Recomendadas:**\n"
                "• **Front Runners:** Seiun Sky, Daiwa Scarlet\n"
                "• **Pace Chasers:** Narita Brian, Grass Wonder\n"
                "• **Late Surgers:** Mejiro Ryan, Symboli Rudolf\n"
                "• **End Closers:** Gold Ship"
            ),
            "inherits": (
                "🧬 **Herencias / Inherits Principales:**\n"
                "• *Angling x Scheming* (Seiun Sky) - Imprescindible para Front Runners\n"
                "• *Anabolic* (Mejiro Ryan) - Clave para Late Surgers y End Closers\n"
                "• *Kanata, Until the Skies Scream* (Mejiro Dober)"
            ),
            "skills": (
                "⚡ **Accels y Skills Clave:**\n"
                "• *Non-stop Girl* / *Acceleration Unleashed*\n"
                "• *Straightaway Spurt* / *Spurt Acceleration*\n"
                "• Gold Recovery: *Arc Maestro*, *Cool Down*"
            ),
            "estilos": (
                "🏃 **Estrategia por Estilo:**\n"
                "• **Front Runners:** Asegurar el primer puesto antes de la bajada final.\n"
                "• **Pace Chasers:** Mantener buen ritmo de posición intermedia.\n"
                "• **Late Surgers & End Closers:** Guardar stamina y desatar aceleración en la última curva."
            )
        }
    },
    "sprint_cup": {
        "name": "Sprint Cup (Short / 1200m)",
        "track": "Nakayama 1200m (Short - Derecha - Exterior)",
        "category": "Short (Corto)",
        "start_time": 1802000000,
        "end_time": 1802500000,
        "sections": {
            "stats": (
                "📊 **Stats Recomendadas:**\n"
                "• **Speed:** 1200+ (Prioridad absoluta)\n"
                "• **Stamina:** 450-500 (Baja exigencia)\n"
                "• **Power:** 1100+\n"
                "• **Guts:** 800+\n"
                "• **Wit:** 900+"
            ),
            "umas": (
                "🐴 **Umas Meta Recomendadas:**\n"
                "• **Front Runners:** Bakushin O, Taiki Shuttle\n"
                "• **Pace Chasers:** Curren Chan, King Halo\n"
                "• **Late Surgers / End Closers:** Air Groove, Nishino Flower"
            ),
            "inherits": (
                "🧬 **Herencias / Inherits Principales:**\n"
                "• *Red Flame* (Maruzensky)\n"
                "• *Plan X* / Aceleraciones de recta corta"
            ),
            "skills": (
                "⚡ **Accels y Skills Clave:**\n"
                "• *Sprint Turbo*\n"
                "• *Sprint Acceleration*\n"
                "• *Upbeat Spurt*"
            ),
            "estilos": (
                "🏃 **Estrategia por Estilo:**\n"
                "• **Front Runners & Pace Chasers:** Dominar la salida explosiva desde el inicio.\n"
                "• **Late Surgers & End Closers:** Posicionarse bien antes de la recta corta para evitar bloqueos."
            )
        }
    }
}

# --- MENÚ DESPLEGABLE DE SECCIONES (ACTUALIZA EL MENSAJE EN VEZ DE ENVIAR OTRO) ---
class CMSectionSelect(Select):
    def __init__(self, cm_data):
        self.cm_data = cm_data
        options = [
            discord.SelectOption(label="Stats Recomendadas", value="stats", emoji="📊", description="Ver estadísticas objetivas"),
            discord.SelectOption(label="Umas Meta", value="umas", emoji="🐴", description="Ver personajes recomendados"),
            discord.SelectOption(label="Herencias / Inherits", value="inherits", emoji="🧬", description="Ver habilidades a heredar"),
            discord.SelectOption(label="Accels y Skills", value="skills", emoji="⚡", description="Ver aceleraciones clave"),
            discord.SelectOption(label="Estilos de Carrera", value="estilos", emoji="🏃", description="Front Runners, Pace, etc.")
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
        embed.set_footer(text="Umalator CM Helper • Usa el menú de abajo para cambiar de sección")
        
        # Edita el mensaje existente en lugar de enviar uno nuevo
        await interaction.response.edit_message(embed=embed, view=self.view)

class CMSectionView(View):
    def __init__(self, cm_data):
        super().__init__()
        self.add_item(CMSectionSelect(cm_data))

# --- AUTOCOMPLETADO PARA EL COMANDO /CM ---
async def cm_autocomplete(interaction: discord.Interaction, current: str):
    choices = [
        app_commands.Choice(name="Sagittarius Cup (Long / 2500m)", value="sagittarius_cup"),
        app_commands.Choice(name="Sprint Cup (Short / 1200m)", value="sprint_cup")
    ]
    return [choice for choice in choices if current.lower() in choice.name.lower()]

# --- COMANDO SLASH CON AUTOCOMPLETADO ---
@bot.tree.command(name="cm", description="Busca la guía y los datos de una Champions Meeting específica")
@app_commands.describe(nombre_copa="Selecciona o escribe la Champions Meeting")
@app_commands.autocomplete(nombre_copa=cm_autocomplete)
async def slash_cm(interaction: discord.Interaction, nombre_copa: str):
    cm_data = CM_DATABASE.get(nombre_copa)
    
    if not cm_data:
        await interaction.response.send_message(
            "❌ No se encontró esa Champions Meeting. Por favor selecciónala de la lista de autocompletado.",
            ephemeral=True
        )
        return

    # Tarjeta de presentación general con pista y fechas (tal como lo pediste)
    embed_init = discord.Embed(
        title=f"🏆 {cm_data['name']}",
        description=(
            f"📍 **Pista:** {cm_data['track']}\n"
            f"📏 **Categoría:** {cm_data['category']}\n\n"
            "Umalator CM Helper • Usa el menú de abajo para cambiar de sección."
        ),
        color=discord.Color.blue()
    )
    
    start_ts = cm_data["start_time"]
    end_ts = cm_data["end_time"]
    embed_init.add_field(name="📅 Inicio", value=f"<t:{start_ts}:F> (<t:{start_ts}:R>)", inline=False)
    embed_init.add_field(name="🏁 Finalización", value=f"<t:{end_ts}:F> (<t:{end_ts}:R>)", inline=False)
    embed_init.set_footer(text="Umalator CM Helper • Selecciona una sección en el menú")

    await interaction.response.send_message(embed=embed_init, view=CMSectionView(cm_data))

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
