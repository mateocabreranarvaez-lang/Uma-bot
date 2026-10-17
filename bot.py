import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Select, View

# --- SERVIDOR WEB 24/7 PARA RENDER ---
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

# --- CARGAR EL JSON DE LA CM ---
def load_cm_database():
    path = os.path.join("data", "cm.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "sections" in data or "name" in data:
                return {"sagittarius_cup": data}
            return data
    return {}

CM_DATABASE = load_cm_database()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- CONSTRUCTOR QUE LEE EL 100% DE TUS CAMPOS SIN RECORTAR NADA ---
def build_cm_embed(cm_data, section_key):
    embed = discord.Embed(
        title=f"🏆 {cm_data.get('name', 'Champions Meeting')}",
        color=discord.Color.from_rgb(255, 165, 0) # Estilo Tazuna (Naranja)
    )

    if section_key == "track_overview":
        # Muestra tu summary completo y los datos de track
        embed.description = cm_data.get("summary", "Sin resumen disponible.")
        
        track = cm_data.get("track", {})
        if track:
            track_info = (
                f"🏟️ **Superficie:** {track.get('venue', 'N/A')} ({track.get('surface', 'N/A')})\n"
                f"📏 **Distancia:** {track.get('distance_m', 'N/A')}m ({track.get('distance_type', 'N/A')})\n"
                f"🔄 **Sentido / Trazado:** {track.get('direction', 'N/A')} / {track.get('course', 'N/A')}\n"
                f"❄️ **Estación / Clima:** {track.get('season', 'N/A')} / {track.get('weather', 'N/A')}"
            )
            embed.add_field(name="📍 Detalles del Circuito", value=track_info, inline=False)
    else:
        # Secciones dinámicas: extrae tal cual tu estructura de secciones
        sections = cm_data.get("sections", {})
        sec = sections.get(section_key, {})
        
        embed.title = f"🏆 {cm_data.get('name', '')} — {sec.get('title', section_key.capitalize())}"
        
        description = sec.get("description", "")
        if description:
            embed.description = description

        # Recorre CADA UNO de los fields que pusiste en tu JSON sin omitir ninguno
        fields = sec.get("fields", [])
        for field in fields:
            name = field.get("name", "•")
            value = field.get("value", "N/A")
            # inline=False obliga a que cada bloque baje de línea, evitando que se vea amontonado
            embed.add_field(name=f"📌 {name}", value=value, inline=False)

    if cm_data.get("image_url"):
        embed.set_image(url=cm_data["image_url"])

    embed.set_footer(text="Tazuna CM Assistant • GameTora & Umalator Data")
    return embed

# --- MENÚ DESPLEGABLE CON LAS SECCIONES ---
class CMSectionSelect(Select):
    def __init__(self, cm_data):
        self.cm_data = cm_data
        options = [
            discord.SelectOption(label="Track & Resumen", value="track_overview", emoji="🏟️"),
            discord.SelectOption(label="Mejores Umas", value="umas", emoji="🏇"),
            discord.SelectOption(label="Stats Recomendadas", value="stats", emoji="📊"),
            discord.SelectOption(label="Herencia", value="inheritance", emoji="🧬"),
            discord.SelectOption(label="Supports Whale", value="supports_whale", emoji="🐋"),
            discord.SelectOption(label="Supports F2P", value="supports_f2p", emoji="🆓"),
            discord.SelectOption(label="Skills Recomendadas", value="skills", emoji="⚡")
        ]
        super().__init__(placeholder="SELECCIONA UNA SECCIÓN DE LA GUÍA...", options=options)

    async def callback(self, interaction: discord.Interaction):
        section_key = self.values[0]
        embed = build_cm_embed(self.cm_data, section_key)
        await interaction.response.edit_message(content="", embed=embed, view=self.view)

class CMSectionView(View):
    def __init__(self, cm_data):
        super().__init__()
        self.add_item(CMSectionSelect(cm_data))

# --- AUTOCOMPLETADO ---
async def cm_autocomplete(interaction: discord.Interaction, current: str):
    choices = []
    for key, data in CM_DATABASE.items():
        name = data.get("name", key)
        if not current or current.lower() in name.lower() or current.lower() in key.lower():
            choices.append(app_commands.Choice(name=name, value=key))
    return choices[:25]

# --- COMANDO /cm ---
@bot.tree.command(name="cm", description="Muestra la guía completa de la Champions Meeting")
@app_commands.describe(nombre_copa="Selecciona la Champions Meeting")
@app_commands.autocomplete(nombre_copa=cm_autocomplete)
async def slash_cm(interaction: discord.Interaction, nombre_copa: str):
    cm_data = CM_DATABASE.get(nombre_copa)
    
    if not cm_data:
        for key, data in CM_DATABASE.items():
            if nombre_copa.lower() in data.get("name", "").lower():
                cm_data = data
                break
                
    if not cm_data and CM_DATABASE:
        cm_data = next(iter(CM_DATABASE.values()))

    if not cm_data:
        await interaction.response.send_message(
            "❌ **Copa no encontrada.** Revisa tu archivo `data/cm.json`.",
            ephemeral=True
        )
        return

    embed_init = build_cm_embed(cm_data, "track_overview")
    await interaction.response.send_message(embed=embed_init, view=CMSectionView(cm_data))

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
