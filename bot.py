import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Select, View

# --- SERVIDOR WEB 24/7 ---
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

# --- CARGAR BASE DE DATOS ---
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

# --- FORMATO DE EMBED ESTILO TAZUNA BOT ---
def build_cm_embed(cm_data, section_key):
    embed = discord.Embed(
        color=discord.Color.from_rgb(47, 49, 54) # Fondo oscuro elegante estilo Tazuna
    )

    if section_key == "track_overview":
        embed.title = cm_data.get("name", "Sagittarius Cup")
        
        track = cm_data.get("track", {})
        if track:
            embed.add_field(name="Racetrack", value=track.get("venue", "N/A"), inline=False)
            embed.add_field(name="Distance", value=track.get("distance_m", "N/A"), inline=False)
            embed.add_field(name="Terrain", value=track.get("surface", "N/A"), inline=False)
            embed.add_field(name="Conditions", value=track.get("conditions", "N/A"), inline=False)
            if track.get("similar"):
                embed.add_field(name="Similar to", value=track.get("similar"), inline=False)
        
        if cm_data.get("summary"):
            embed.add_field(name="Overview & Advice", value=cm_data["summary"], inline=False)

    else:
        sections = cm_data.get("sections", {})
        sec = sections.get(section_key, {})
        
        embed.title = f"{cm_data.get('name', '')} — {sec.get('title', section_key.capitalize())}"
        if sec.get("description"):
            embed.description = sec.get("description")

        for field in sec.get("fields", []):
            embed.add_field(
                name=field.get("name", "•"),
                value=field.get("value", "N/A"),
                inline=False
            )

    if cm_data.get("image_url"):
        embed.set_image(url=cm_data["image_url"])

    embed.set_footer(text="Umalator CM Helper")
    return embed

# --- MENÚ INTERACTIVO ---
class CMSectionSelect(Select):
    def __init__(self, cm_data):
        self.cm_data = cm_data
        options = [
            discord.SelectOption(label="Track Info", value="track_overview", emoji="🏟️"),
            discord.SelectOption(label="Best Umas", value="umas", emoji="🏇"),
            discord.SelectOption(label="Stats & Builds", value="stats", emoji="📊"),
            discord.SelectOption(label="Inheritance", value="inheritance", emoji="🧬"),
            discord.SelectOption(label="Supports (Whale)", value="supports_whale", emoji="🐋"),
            discord.SelectOption(label="Supports (F2P)", value="supports_f2p", emoji="🆓"),
            discord.SelectOption(label="Key Skills", value="skills", emoji="⚡")
        ]
        super().__init__(placeholder="SELECCIONA UNA SECCIÓN DE LA CM...", options=options)

    async def callback(self, interaction: discord.Interaction):
        embed = build_cm_embed(self.cm_data, self.values[0])
        await interaction.response.edit_message(content="", embed=embed, view=self.view)

class CMSectionView(View):
    def __init__(self, cm_data):
        super().__init__()
        self.add_item(CMSectionSelect(cm_data))

# --- AUTOCOMPLETADO Y COMANDO ---
async def cm_autocomplete(interaction: discord.Interaction, current: str):
    choices = []
    for key, data in CM_DATABASE.items():
        name = data.get("name", key)
        if not current or current.lower() in name.lower():
            choices.append(app_commands.Choice(name=name, value=key))
    return choices[:25]

@bot.tree.command(name="cm", description="Guía de Champions Meeting")
@app_commands.describe(nombre_copa="Selecciona la copa")
@app_commands.autocomplete(nombre_copa=cm_autocomplete)
async def slash_cm(interaction: discord.Interaction, nombre_copa: str):
    cm_data = CM_DATABASE.get(nombre_copa) or next(iter(CM_DATABASE.values()), None)

    if not cm_data:
        await interaction.response.send_message("❌ No hay datos en `data/cm.json`.", ephemeral=True)
        return

    embed_init = build_cm_embed(cm_data, "track_overview")
    await interaction.response.send_message(embed=embed_init, view=CMSectionView(cm_data))

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
    except Exception as e:
        print(f"Error sync: {e}")
    print(f"Bot listo como {bot.user}")

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
