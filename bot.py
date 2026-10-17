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

# --- BASE DE DATOS COMPLETA DE CMs (GAMETORA + UMALATOR) ---
CM_DATABASE = {
    "taurus_cup": {
        "name": "Taurus Cup (Tokyo 2400m)",
        "start_time": 1755734400,
        "image_url": None,
        "sections": {
            "track_overview": (
                "🏟️ **TRACK INFO & GENERAL OVERVIEW**\n\n"
                "📍 **Pista:** Tokyo Turf 2400m (Medium) - Left - Spring - Firm\n\n"
                "💡 **Distancia Ideal:** Exigencia alta de velocidad y stamina base. La recta larga de Tokyo premia los bursts de velocidad final."
            ),
            "best_umas": (
                "🏇 **BEST UMAS & RUNNING STYLES**\n\n"
                "🏃 **Front Runner:** Silence Suzuka, Seiun Sky\n"
                "🏃 **Pace Chaser:** Narita Brian, Vodka\n"
                "🏃 **Late Surger:** Mejiro Ryan\n"
                "🏃 **End Closer:** Gold Ship\n"
                "🏃 **Debuffer:** Nice Nature"
            ),
            "inheritance": (
                "🧬 **INHERITANCE & STAT FACTORS**\n\n"
                "📊 **Target Stat Factors:**\n• ★9 Stamina - ★9 Power\n\n"
                "🐴 **Recommended Parents / Grandparents:**\n• Super Creek (*Arc Maestro*)\n• Mejiro Ryan (*Anabolic*)\n\n"
                "⚡ **Key Inherited Unique Skills & Priorities:**\n• *Arc Maestro* [Prioridad Alta]\n• *Anabolic* [Prioridad Media]"
            ),
            "support_cards": (
                "🎴 **SUPPORT CARDS (WHALE VS F2P)**\n\n"
                "🐋 **Decks Whale / P2P:**\n• 👟3 Speed + 🫀2 Stamina + 🧠1 Wit\n• Borrow: Super Creek SSR\n\n"
                "🆓 **Decks F2P:**\n• 👟3 Speed + 🫀2 Stamina + 🔥1 Guts\n• Opciones: Rice Shower SR, Manhattan Cafe SR"
            ),
            "skills_priority": (
                "⚡ **KEY SKILLS, PRIORITY & RANKING POINTS**\n\n"
                "• *Arc Maestro* [○ 200 pts / ◎ 300 pts] -> Rentable: ○\n"
                "• *Medium Straight* [○ 130 pts / ◎ 210 pts]\n"
                "• *Non-stop Girl* [○ 200 pts / ◎ 320 pts]"
            )
        }
    },
    "gemini_cup": {
        "name": "Gemini Cup (Kyoto 3200m)",
        "start_time": 1757548800,
        "image_url": None,
        "sections": {
            "track_overview": (
                "🏟️ **TRACK INFO & GENERAL OVERVIEW**\n\n"
                "📍 **Pista:** Kyoto Turf 3200m (Long) - Right - Spring - Firm\n\n"
                "💡 **Distancia Ideal:** La carrera más larga del circuito inicial. La stamina y los recoveries múltiples son innegociables."
            ),
            "best_umas": (
                "🏇 **BEST UMAS & RUNNING STYLES**\n\n"
                "🏃 **Front Runner:** Rice Shower, Maya No Top Gun\n"
                "🏃 **Pace Chaser:** Narita Brian\n"
                "🏃 **Late Surger:** Mejiro Ryan\n"
                "🏃 **End Closer:** Gold Ship (Reina indiscutible)\n"
                "🏃 **Debuffer:** Nice Nature"
            ),
            "inheritance": (
                "🧬 **INHERITANCE & STAT FACTORS**\n\n"
                "📊 **Target Stat Factors:**\n• ★12 Stamina - ★6 Guts\n\n"
                "🐴 **Recommended Parents / Grandparents:**\n• Super Creek (*Arc Maestro*)\n\n"
                "⚡ **Key Inherited Unique Skills & Priorities:**\n• *Arc Maestro* [Prioridad Máxima]"
            ),
            "support_cards": (
                "🎴 **SUPPORT CARDS (WHALE VS F2P)**\n\n"
                "🐋 **Decks Whale / P2P:**\n• 👟2 Speed + 🫀3 Stamina + 🧠1 Wit\n• Borrow: Super Creek SSR\n\n"
                "🆓 **Decks F2P:**\n• 👟2 Speed + 🫀3 Stamina + 🔥1 Guts\n• Opciones: Marvelous Sunday SR"
            ),
            "skills_priority": (
                "⚡ **KEY SKILLS, PRIORITY & RANKING POINTS**\n\n"
                "• *Arc Maestro* [○ 200 pts / ◎ 300 pts]\n"
                "• *Professor of Recovery* [○ 180 pts / ◎ 270 pts]\n"
                "• *Long Distance Straight* [○ 130 pts / ◎ 210 pts]"
            )
        }
    },
    "sagittarius_cup": {
        "name": "Sagittarius Cup (Nakayama 2500m)",
        "start_time": 1800000000,
        "image_url": None,
        "sections": {
            "track_overview": (
                "🏟️ **TRACK INFO & GENERAL OVERVIEW**\n\n"
                "📍 **Pista:** Nakayama Turf 2500m (Long) - Right / Inner - Winter - Fair\n\n"
                "💡 **Distancia Ideal:** Requiere doble recuperación de stamina y excelente aceleración en bajada."
            ),
            "best_umas": (
                "🏇 **BEST UMAS & RUNNING STYLES**\n\n"
                "🏃 **Front Runner:** Seiun Sky\n"
                "🏃 **Pace Chaser:** Narita Brian\n"
                "🏃 **Late Surger:** Mejiro Ryan\n"
                "🏃 **End Closer:** Gold Ship\n"
                "🏃 **Debuffer:** Nice Nature"
            ),
            "inheritance": (
                "🧬 **INHERITANCE & STAT FACTORS**\n\n"
                "📊 **Target Stat Factors:**\n• ★6 Power - ★12 Stamina\n\n"
                "🐴 **Recommended Parents / Grandparents:**\n• Super Creek (*Arc Maestro*), Mejiro Dober (*Kanata*)\n\n"
                "⚡ **Key Inherited Unique Skills & Priorities:**\n• *Anabolic* [Prioridad Alta]"
            ),
            "support_cards": (
                "🎴 **SUPPORT CARDS (WHALE VS F2P)**\n\n"
                "🐋 **Decks Whale / P2P:**\n• 👟2 Speed + 🫀2 Stamina + 🧠2 Wit\n• Borrow: Super Creek SSR\n\n"
                "🆓 **Decks F2P:**\n• 👟3 Speed + 🫀2 Stamina + 🧠1 Wit"
            ),
            "skills_priority": (
                "⚡ **KEY SKILLS, PRIORITY & RANKING POINTS**\n\n"
                "• *Arc Maestro* [○ 200 pts / ◎ 300 pts]\n"
                "• *Non-stop Girl* [○ 200 pts / ◎ 320 pts]"
            )
        }
    },
    "capricorn_cup": {
        "name": "Capricorn Cup (Chukyo 12d, view=self.view)

class CMSectionView(View):
    def __init__(self, cm_data):
        super().__init__()
        self.add_item(CMSectionSelect(cm_data))

# --- AUTOCOMPLETADO DINÁMICO PARA /CM ---
async def cm_autocomplete(interaction: discord.Interaction, current: str):
    choices = [
        app_commands.Choice(name=data["name"], value=key)
        for key, data in CM_DATABASE.items()
    ]
    return [choice for choice in choices if current.lower() in choice.name.lower()]

# --- COMANDO SLASH PRINCIPAL ---
@bot.tree.command(name="cm", description="Muestra la guía completa de una Champions / Copa")
@app_commands.describe(nombre_copa="Selecciona la Champions Meeting")
@app_commands.autocomplete(nombre_copa=cm_autocomplete)
async def slash_cm(interaction: discord.Interaction, nombre_copa: str):
    cm_data = CM_DATABASE.get(nombre_copa)
    
    if not cm_data:
        await interaction.response.send_message(
            "❌ Champions Meeting no encontrada. Por favor selecciónala del menú desplegable.",
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
