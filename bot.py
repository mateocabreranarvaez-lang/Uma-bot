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

# --- BASE DE DATOS COMPLETA DE CMs (CON NOMBRES OFICIALES DEL JUEGO) ---
CM_DATABASE = {
    "taurus_cup": {
        "name": "Taurus Cup (Tokyo 2400m)",
        "start_time": 1755734400,
        "image_url": None,
        "sections": {
            "track_overview": "🏟️ **TRACK INFO & GENERAL OVERVIEW**\n\n📍 **Pista:** Tokyo Turf 2400m (Medium) - Left - Spring - Firm\n\n💡 **Distancia Ideal:** Exigencia alta de velocidad y stamina base. La recta larga de Tokyo premia los bursts de velocidad final.",
            "best_umas": "🏇 **BEST UMAS & RUNNING STYLES**\n\n🏃 **Front Runner:** Silence Suzuka, Seiun Sky\n🏃 **Pace Chaser:** Narita Brian, Vodka\n🏃 **Late Surger:** Mejiro Ryan\n🏃 **End Closer:** Gold Ship\n🏃 **Debuffer:** Nice Nature",
            "inheritance": "🧬 **INHERITANCE & STAT FACTORS**\n\n📊 **Target Stat Factors:**\n• ★9 Stamina - ★9 Power\n\n🐴 **Recommended Parents / Grandparents:**\n• Super Creek (*Swinging Maestro*)\n• Mejiro Ryan (*Feel the Burn*)\n\n⚡ **Key Inherited Unique Skills & Priorities:**\n• *Swinging Maestro* [Prioridad Alta]\n• *Feel the Burn* [Prioridad Media]",
            "support_cards": "🎴 **SUPPORT CARDS (WHALE VS F2P)**\n\n🐋 **Decks Whale / P2P:**\n• 👟3 Speed + 🫀2 Stamina + 🧠1 Wit\n• Borrow: Super Creek SSR\n\n🆓 **Decks F2P:**\n• 👟3 Speed + 🫀2 Stamina + 🔥1 Guts\n• Opciones: Rice Shower SR, Manhattan Cafe SR",
            "skills_priority": "⚡ **KEY SKILLS, PRIORITY & RANKING POINTS**\n\n• *Swinging Maestro* [○ 200 pts / ◎ 300 pts] -> Rentable: ○\n• *Medium Straight* [○ 130 pts / ◎ 210 pts]\n• *Non-Stop Girl* [○ 200 pts / ◎ 320 pts]"
        }
    },
    "gemini_cup": {
        "name": "Gemini Cup (Kyoto 3200m)",
        "start_time": 1757548800,
        "image_url": None,
        "sections": {
            "track_overview": "🏟️ **TRACK INFO & GENERAL OVERVIEW**\n\n📍 **Pista:** Kyoto Turf 3200m (Long) - Right - Spring - Firm\n\n💡 **Distancia Ideal:** La carrera más larga del circuito inicial. La stamina y los recoveries múltiples son innegociables.",
            "best_umas": "🏇 **BEST UMAS & RUNNING STYLES**\n\n🏃 **Front Runner:** Rice Shower, Maya No Top Gun\n🏃 **Pace Chaser:** Narita Brian\n🏃 **Late Surger:** Mejiro Ryan\n🏃 **End Closer:** Gold Ship (Reina indiscutible)\n🏃 **Debuffer:** Nice Nature",
            "inheritance": "🧬 **INHERITANCE & STAT FACTORS**\n\n📊 **Target Stat Factors:**\n• ★12 Stamina - ★6 Guts\n\n🐴 **Recommended Parents / Grandparents:**\n• Super Creek (*Swinging Maestro*)\n\n⚡ **Key Inherited Unique Skills & Priorities:**\n• *Swinging Maestro* [Prioridad Máxima]",
            "support_cards": "🎴 **SUPPORT CARDS (WHALE VS F2P)**\n\n🐋 **Decks Whale / P2P:**\n• 👟2 Speed + 🫀3 Stamina + 🧠1 Wit\n• Borrow: Super Creek SSR\n\n🆓 **Decks F2P:**\n• 👟2 Speed + 🫀3 Stamina + 🔥1 Guts\n• Opciones: Marvelous Sunday SR",
            "skills_priority": "⚡ **KEY SKILLS, PRIORITY & RANKING POINTS**\n\n• *Swinging Maestro* [○ 200 pts / ◎ 300 pts]\n• *Professor of Curvature* [○ 180 pts / ◎ 270 pts]\n• *Long Distance Straights* [○ 130 pts / ◎ 210 pts]"
        }
    },
    "sagittarius_cup": {
        "name": "Sagittarius Cup (Nakayama 2500m)",
        "start_time": 1800000000,
        "image_url": None,
        "sections": {
            "track_overview": "🏟️ **TRACK INFO & GENERAL OVERVIEW**\n\n📍 **Pista:** Nakayama Turf 2500m (Long) - Right / Inner - Winter - Fair\n\n💡 **Distancia Ideal:** Requiere doble recuperación de stamina y excelente aceleración en bajada.",
            "best_umas": "🏇 **BEST UMAS & RUNNING STYLES**\n\n🏃 **Front Runner:** Seiun Sky\n🏃 **Pace Chaser:** Narita Brian\n🏃 **Late Surger:** Mejiro Ryan\n🏃 **End Closer:** Gold Ship\n🏃 **Debuffer:** Nice Nature",
            "inheritance": "🧬 **INHERITANCE & STAT FACTORS**\n\n📊 **Target Stat Factors:**\n• ★6 Power - ★12 Stamina\n\n🐴 **Recommended Parents / Grandparents:**\n• Super Creek (*Swinging Maestro*), Mejiro Dober (*Kanata*)\n\n⚡ **Key Inherited Unique Skills & Priorities:**\n• *Feel the Burn* [Prioridad Alta]",
            "support_cards": "🎴 **SUPPORT CARDS (WHALE VS F2P)**\n\n🐋 **Decks Whale / P2P:**\n• 👟2 Speed + 🫀2 Stamina + 🧠2 Wit\n• Borrow: Super Creek SSR\n\n🆓 **Decks F2P:**\n• 👟3 Speed + 🫀2 Stamina + 🧠1 Wit",
            "skills_priority": "⚡ **KEY SKILLS, PRIORITY & RANKING POINTS**\n\n• *Swinging Maestro* [○ 200 pts / ◎ 300 pts]\n• *Non-Stop Girl* [○ 200 pts / ◎ 320 pts]"
        }
    },
    "capricorn_cup": {
        "name": "Capricorn Cup (Chukyo 1200m)",
        "start_time": 1802000000,
        "image_url": None,
        "sections": {
            "track_overview": "🏟️ **TRACK INFO & GENERAL OVERVIEW**\n\n📍 **Pista:** Chukyo Turf 1200m (Short) - Left - Winter - Firm\n\n💡 **Distancia Ideal:** Máxima prioridad en velocidad pura y aceleración explosiva en recta corta.",
            "best_umas": "🏇 **BEST UMAS & RUNNING STYLES**\n\n🏃 **Front Runner:** Sakura Bakushin O, Taiki Shuttle\n🏃 **Pace Chaser:** Curren Chan\n🏃 **Late Surger:** Air Groove\n🏃 **End Closer:** Nishino Flower\n🏃 **Debuffer:** Grass Wonder",
            "inheritance": "🧬 **INHERITANCE & STAT FACTORS**\n\n📊 **Target Stat Factors:**\n• ★9 Speed - ★9 Power\n\n🐴 **Recommended Parents / Grandparents:**\n• Maruzensky (*Red Shift*)\n\n⚡ **Key Inherited Unique Skills & Priorities:**\n• *Red Shift* [Prioridad Alta]",
            "support_cards": "🎴 **SUPPORT CARDS (WHALE VS F2P)**\n\n🐋 **Decks Whale / P2P:**\n• 👟3 Speed + 🔥2 Guts + 🧠1 Wit\n• Borrow: Kitasan Black SSR\n\n🆓 **Decks F2P:**\n• 👟3 Speed + 🔥1 Guts + 🧠2 Wit",
            "skills_priority": "⚡ **KEY SKILLS, PRIORITY & RANKING POINTS**\n\n• *Sprint Turbo* [○ 180 pts / ◎ 280 pts]\n• *Non-Stop Girl* [○ 200 pts / ◎ 320 pts]"
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
        text_content = self.cm_data["sections"].get(section_key, "Información no disponible.")
        
        embed = discord.Embed(
            title=f"🏆 {self.cm_data['name']}",
            description=text_content,
            color=discord.Color.gold()
        )
        
        if section_key == "track_overview":
            start_ts = self.cm_data["start_time"]
            embed.add_field(name="📅 Inicia", value=f"<t:{start_ts}:F> (<t:{start_ts}:R>)", inline=False)
            
        if self.cm_data.get("image_url"):
            embed.set_image(url=self.cm_data["image_url"])
            
        embed.set_footer(text="Umalator CM Helper")
        
        # Se asegura que content sea explícitamente "" o None para evitar mostrar objetos como texto
        await interaction.response.edit_message(content="", embed=embed, view=self.view)

class CMSectionView(View):
    def __init__(self, cm_data):
        super().__init__()
        self.add_item(CMSectionSelect(cm_data))

# --- AUTOCOMPLETADO DINÁMICO MEJORADO Y ROBUSTO ---
async def cm_autocomplete(interaction: discord.Interaction, current: str):
    choices = []
    for key, data in CM_DATABASE.items():
        name = data["name"]
        if not current or current.lower() in name.lower() or current.lower() in key.lower():
            choices.append(app_commands.Choice(name=name, value=key))
    return choices[:25]

# --- COMANDO SLASH PRINCIPAL ---
@bot.tree.command(name="cm", description="Muestra la guía completa de una Champions Meeting")
@app_commands.describe(nombre_copa="Selecciona la Champions Meeting de la lista")
@app_commands.autocomplete(nombre_copa=cm_autocomplete)
async def slash_cm(interaction: discord.Interaction, nombre_copa: str):
    cm_data = CM_DATABASE.get(nombre_copa)
    
    if not cm_data:
        for key, data in CM_DATABASE.items():
            if nombre_copa.lower() in data["name"].lower():
                cm_data = data
                break
                
    if not cm_data:
        await interaction.response.send_message(
            "❌ **Copa no encontrada.** Por favor selecciona una opción de la lista flotante al usar /cm.",
            ephemeral=True
        )
        return

    text_content = cm_data["sections"]["track_overview"]
    start_ts = cm_data["start_time"]

    embed_init = discord.Embed(
        title=f"🏆 {cm_data['name']}",
        description=text_content,
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
