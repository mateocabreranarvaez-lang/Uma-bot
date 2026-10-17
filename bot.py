import os
import threading
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

# --- BASE DE DATOS DE CMs (ESTRUCTURA COMPLETA DEFINITIVA) ---
CM_DATABASE = {
    "sagittarius_cup": {
        "name": "Sagittarius Cup",
        "start_time": 1800000000,
        "image_url": None, # Espacio reservado para la imagen del circuito / Tazuna
        "sections": {
            "track_overview": (
                "🏟️ **TRACK INFO & GENERAL OVERVIEW**\n\n"
                "📍 **Pista:** Nakayama Turf 2500m (Long) - Right / Inner - Winter - Fair\n\n"
                "💡 **Distancia Ideal:** Explicación detallada de la adaptación a la carrera..."
            ),
            "best_umas": (
                "🏇 **BEST UMAS & RUNNING STYLES**\n\n"
                "🏃 **Front Runner:**\n• Uma 1: Explicación fría y técnica de su ulti...\n\n"
                "🏃 **Pace Chaser:**\n• Uma 1: Explicación...\n\n"
                "🏃 **Late Surger:**\n• Uma 1: Explicación...\n\n"
                "🏃 **End Closer:**\n• Uma 1: Explicación...\n\n"
                "🏃 **Debuffer:**\n• Uma 1: Explicación..."
            ),
            "inheritance": (
                "🧬 **INHERITANCE & STAT FACTORS**\n\n"
                "📊 **Target Stat Factors:**\n• ★6 Power - ★12 Stamina\n\n"
                "🐴 **Recommended Parents / Grandparents (Herencia & Afinidad):**\n"
                "• Parent Uma 1: Explicación de por qué es buena herencia / compatibilidad...\n"
                "• Parent Uma 2: Explicación...\n\n"
                "⚡ **Key Inherited Unique Skills & Priorities:**\n"
                "• Unique Skill 1 (Prioridad Alta)\n"
                "• Unique Skill 2 (Prioridad Media)"
            ),
            "support_cards": (
                "🎴 **SUPPORT CARDS (WHALE VS F2P)**\n\n"
                "🐋 **Decks Whale / P2P:**\n"
                "• Configuración: 👟3 Speed + 🧠2 Wit + 👥1 Pal\n"
                "• Opciones por slot...\n"
                "• Carta a prestar (Borrow): ...\n\n"
                "🆓 **Decks F2P:**\n"
                "• Configuración: 👟3 Speed + 🔥1 Guts + 🧠2 Wit\n"
                "• Opciones F2P por slot..."
            ),
            "skills_priority": (
                "⚡ **KEY SKILLS, PRIORITY & RANKING POINTS**\n\n"
                "• **Front Runner Skills:**\n  - Skill 1 [○ 200 pts / ◎ 300 pts] -> Más rentable: ○\n\n"
                "• **Pace Chaser Skills:**\n  - ...\n\n"
                "• **Late Surger Skills:**\n  - ...\n\n"
                "• **End Closer Skills:**\n  - ...\n\n"
                "• **Debuffer Skills:**\n  - ..."
            )
        }
    }
}

# --- MENÚ DESPLEGABLE CON LAS 5 SECCIONES DEFINITIVAS ---
class CMSectionSelect(Select):
    def __init__(self, cm_data):
        self.cm_data = cm_data
        options = [
            discord.SelectOption(label="Track Info & Overview", value="track_overview", emoji="🏟️"),
            discord.SelectOption(label="Best Umas & Styles", value="best_umas", emoji="🏇"),
            discord.SelectOption(label="Inheritance & Factors", value="inheritance", emoji="🧬"),
            discord.SelectOption(label="Support Cards (Whale vs F2P)", value="support_cards", emoji="🎴"),
            discord.SelectOption(label="Key Skills & Priority", value="skills_priority", emoji="⚡")
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
        
        # Muestra la Fecha de Inicio solo si está en la Sección 1
        if section_key == "track_overview":
            start_ts = self.cm_data["start_time"]
            embed.add_field(name="📅 Inicia", value=f"<t:{start_ts}:F> (<t:{start_ts}:R>)", inline=False)
            
        if self.cm_data.get("image_url"):
            embed.set_image(url=self.cm_data["image_url"])
            
        embed.set_footer(text="Umalator CM Helper")
        
        # Edita el mensaje existente para mantener todo limpio
        await interaction.response.edit_message(embed=embed, view=self.view)

class CMSectionView(View):
    def __init__(self, cm_data):
        super().__init__()
        self.add_item(CMSectionSelect(cm_data))

# --- AUTOCOMPLETADO PARA /CM ---
async def cm_autocomplete(interaction: discord.Interaction, current: str):
    choices = [
        app_commands.Choice(name="Sagittarius Cup", value="sagittarius_cup")
    ]
    return [choice for choice in choices if current.lower() in choice.name.lower()]

# --- COMANDO SLASH PRINCIPAL ---
@bot.tree.command(name="cm", description="Muestra la guía completa de una Champions Meeting")
@app_commands.describe(nombre_copa="Selecciona la Champions Meeting")
@app_commands.autocomplete(nombre_copa=cm_autocomplete)
async def slash_cm(interaction: discord.Interaction, nombre_copa: str):
    cm_data = CM_DATABASE.get(nombre_copa)
    
    if not cm_data:
        await interaction.response.send_message(
            "❌ Champions Meeting no encontrada. Por favor selecciónala de la lista.",
            ephemeral=True
        )
        return

    # La primera respuesta carga DIRECTAMENTE la Sección 1 (Track Info & Overview)
    content = cm_data["sections"]["track_overview"]
    start_ts = cm_data["start_time"]

    embed_init = discord.Embed(
        title=f"🏆 {cm_data['name']}",
        description=content,
        color=discord.Color.blue()
    )
    
    embed_init.add_field(name="📅 Inicia", value=f"<t:{start_ts}:F> (<t:{start_ts}:R>)", inline=False)
    
    if cm_data.get("image_url"):
        embed_init.set_image(url=cm_data["image_url"])
        
    embed_init.set_footer(text="Umalator CM Helper")

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
