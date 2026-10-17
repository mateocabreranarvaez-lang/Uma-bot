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

# --- BASE DE DATOS DE CMs Y LAS 5 SECCIONES DE UMALATOR ---
CM_DATABASE = {
    "sagittarius_cup": {
        "name": "Sagittarius Cup (Nakayama 2500m)",
        "track": "Nakayama Turf 2500m (Long) - Right / Inner - Winter - Fair",
        "start_time": 1800000000,
        "end_time": 1800500000,
        "sections": {
            "track_stats": (
                "🏟️ **Track Info & Target Stats**\n"
                "• **Distance:** 2500m (Long)\n"
                "• **Track:** Nakayama Turf (Right / Inner)\n"
                "• **Speed Target:** 1200+\n"
                "• **Stamina Target:** 900+ (Requires 2 Gold Stamina Recoveries)\n"
                "• **Power Target:** 1000+\n"
                "• **Guts Target:** 600+\n"
                "• **Wit Target:** 800+"
            ),
            "styles_hierarchy": (
                "🏆 **Running Styles Hierarchy**\n"
                "• **Tier S:** Front Runner (Pacing advantage)\n"
                "• **Tier A:** Pace Chaser / Late Surger\n"
                "• **Tier B:** End Closer (Requires heavy acceleration skills)"
            ),
            "umas_inheritance": (
                "🏇 **Umas & Inheritance**\n"
                "• **Front Runner:** Seiun Sky, Daiwa Scarlet\n"
                "• **Pace Chaser:** Narita Brian, Grass Wonder\n"
                "• **Late Surger:** Mejiro Ryan, Symboli Rudolf\n"
                "• **End Closer:** Gold Ship\n\n"
                "🧬 **Key Inherited Skills:**\n"
                "• *Angling x Scheming* (Seiun Sky)\n"
                "• *Anabolic* (Mejiro Ryan)\n"
                "• *Kanata, Until the Skies Scream* (Mejiro Dober)"
            ),
            "support_cards": (
                "🎴 **Support Cards (Whale vs F2P)**\n"
                "• **Whale Deck:** Kitasan Black SSR, Fine Motion SSR, Super Creek SSR, Mr. C.B. SSR\n"
                "• **F2P Deck:** Speed SSR (Event), Rice Shower SSR (Main Story), Marvelous Sunday SR, Sweep Tosho SR"
            ),
            "skills_priority": (
                "⚡ **Key Skills & Priority**\n"
                "• **Core Accels:** *Non-stop Girl*, *Straightaway Spurt*, *Spurt Acceleration*\n"
                "• **Stamina Recoveries:** *Arc Maestro*, *Cool Down*\n"
                "• **Mid-leg Skills:** *Proficient Corner*, *Arc Position*"
            )
        }
    },
    "sprint_cup": {
        "name": "Sprint Cup (Nakayama 1200m)",
        "track": "Nakayama Turf 1200m (Short) - Right / Outer - Spring - Fair",
        "start_time": 1802000000,
        "end_time": 1802500000,
        "sections": {
            "track_stats": (
                "🏟️ **Track Info & Target Stats**\n"
                "• **Distance:** 1200m (Short)\n"
                "• **Track:** Nakayama Turf (Right / Outer)\n"
                "• **Speed Target:** 1200+ (Max priority)\n"
                "• **Stamina Target:** 450-500\n"
                "• **Power Target:** 1100+\n"
                "• **Guts Target:** 800+\n"
                "• **Wit Target:** 900+"
            ),
            "styles_hierarchy": (
                "🏆 **Running Styles Hierarchy**\n"
                "• **Tier S:** Front Runner / Pace Chaser\n"
                "• **Tier A:** Late Surger\n"
                "• **Tier B:** End Closer"
            ),
            "umas_inheritance": (
                "🏇 **Umas & Inheritance**\n"
                "• **Front Runner:** Sakura Bakushin O, Taiki Shuttle\n"
                "• **Pace Chaser:** Curren Chan, King Halo\n"
                "• **Late Surger / End Closer:** Air Groove, Nishino Flower\n\n"
                "🧬 **Key Inherited Skills:**\n"
                "• *Red Flame* (Maruzensky)\n"
                "• *Plan X*"
            ),
            "support_cards": (
                "🎴 **Support Cards (Whale vs F2P)**\n"
                "• **Whale Deck:** Kitasan Black SSR, Sakura Bakushin O SSR, Biko Pegasus SSR\n"
                "• **F2P Deck:** Eishin Flash SR, King Halo SR, Sweep Tosho SR"
            ),
            "skills_priority": (
                "⚡ **Key Skills & Priority**\n"
                "• **Core Accels:** *Sprint Turbo*, *Sprint Acceleration*, *Upbeat Spurt*\n"
                "• **Positioning:** *Sprint Corner*, *Short Distance Straight*"
            )
        }
    }
}

# --- MENÚ DESPLEGABLE CON LAS 5 SECCIONES EXACTAS ---
class CMSectionSelect(Select):
    def __init__(self, cm_data):
        self.cm_data = cm_data
        options = [
            discord.SelectOption(label="Track & Stats", value="track_stats", emoji="🏟️"),
            discord.SelectOption(label="Running Styles Hierarchy", value="styles_hierarchy", emoji="🏆"),
            discord.SelectOption(label="Umas & Inheritance", value="umas_inheritance", emoji="🏇"),
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
        embed.set_footer(text="Umalator CM Helper • Usa el menú de abajo para cambiar de sección")
        
        # Edita el mensaje existente para mantener todo limpio
        await interaction.response.edit_message(embed=embed, view=self.view)

class CMSectionView(View):
    def __init__(self, cm_data):
        super().__init__()
        self.add_item(CMSectionSelect(cm_data))

# --- AUTOCOMPLETADO PARA /CM ---
async def cm_autocomplete(interaction: discord.Interaction, current: str):
    choices = [
        app_commands.Choice(name="Sagittarius Cup (Nakayama 2500m)", value="sagittarius_cup"),
        app_commands.Choice(name="Sprint Cup (Nakayama 1200m)", value="sprint_cup")
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
            "❌ Champions Meeting no encontrada. Por favor elígela usando el autocompletado.",
            ephemeral=True
        )
        return

    # Mensaje inicial con Info General + Timestamps de fechas locales
    embed_init = discord.Embed(
        title=f"🏆 {cm_data['name']}",
        description=(
            f"📍 **Track Info:** {cm_data['track']}\n\n"
            "Umalator CM Helper • Usa el menú de abajo para cambiar de sección"
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
