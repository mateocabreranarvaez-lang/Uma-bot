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

# --- CARGAR BASE DE DATOS DE LAS 10 CMS ---
def load_cm_database():
    path = os.path.join("data", "cm.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

CM_DATABASE = load_cm_database()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- CONSTRUCTOR DE EMBEDS (BANNER ARRIBA Y MAPA ABAJO) ---
def build_cm_embed(cm_data, section_key):
    embed = discord.Embed(
        color=discord.Color.from_rgb(47, 49, 54) # Estilo Tazuna Dark
    )

    if section_key == "track_overview":
        embed.title = cm_data.get("name", "Champions Meeting")
        
        # Banner oficial de la carrera arriba (Thumbnail / Foto 4)
        if cm_data.get("banner_url"):
            embed.set_thumbnail(url=cm_data["banner_url"])
        
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

        # Mapa de fases del circuito abajo en grande (Foto 2)
        if cm_data.get("track_map_url"):
            embed.set_image(url=cm_data["track_map_url"])

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

        if cm_data.get("banner_url"):
            embed.set_thumbnail(url=cm_data["banner_url"])

    embed.set_footer(text="Umalator CM Helper • GameTora Data")
    return embed# --- MENÚ DE SECCIONES DE LA GUÍA ---
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

# --- MENÚ DE BÚSQUEDA INTERACTIVA ("Found matches. Pick one:") ---
class SearchMatchSelect(Select):
    def __init__(self, matches):
        self.matches = matches
        options = [
            discord.SelectOption(label=data.get("name", key), value=key, emoji="🏆")
            for key, data in matches.items()
        ]
        super().__init__(placeholder="Choose a Champions Meeting...", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_key = self.values[0]
        cm_data = CM_DATABASE[selected_key]
        embed = build_cm_embed(cm_data, "track_overview")
        await interaction.response.edit_message(content=f"✅ You selected **{cm_data.get('name')}**", embed=embed, view=CMSectionView(cm_data))

class SearchMatchView(View):
    def __init__(self, matches):
        super().__init__()
        self.add_item(SearchMatchSelect(matches))# --- FUNCIÓN DE AUTOCOMPLETADO PARA DISCORD ---
async def cm_autocomplete(interaction: discord.Interaction, current: str):
    choices = []
    for key, data in CM_DATABASE.items():
        name = data.get("name", key)
        if not current or current.lower() in name.lower() or current.lower() in key.lower():
            choices.append(app_commands.Choice(name=name, value=key))
    return choices[:25]

# --- COMANDO SLASH PRINCIPAL CON BÚSQUEDA Y AUTOCOMPLETADO ---
@bot.tree.command(name="cm", description="Busca y muestra guías de Champions Meeting")
@app_commands.describe(busqueda="Selecciona o escribe la copa que buscas")
@app_commands.autocomplete(busqueda=cm_autocomplete)
async def slash_cm(interaction: discord.Interaction, busqueda: str = None):
    if not CM_DATABASE:
        await interaction.response.send_message("❌ No hay datos cargados en `data/cm.json`.", ephemeral=True)
        return

    # Si se selecciona directamente del autocompletado
    if busqueda and busqueda in CM_DATABASE:
        cm_data = CM_DATABASE[busqueda]
        embed = build_cm_embed(cm_data, "track_overview")
        await interaction.response.send_message(embed=embed, view=CMSectionView(cm_data))
        return

    # Si no escribe nada, por defecto muestra la actual (Sagittarius Cup)
    if not busqueda:
        cm_data = CM_DATABASE.get("sagittarius_cup", next(iter(CM_DATABASE.values())))
        embed = build_cm_embed(cm_data, "track_overview")
        await interaction.response.send_message(embed=embed, view=CMSectionView(cm_data))
        return

    # Búsqueda por texto parcial si escriben manual
    matches = {
        key: data for key, data in CM_DATABASE.items()
        if busqueda.lower() in data.get("name", "").lower() or busqueda.lower() in key.lower() or busqueda.lower() in data.get("track", {}).get("venue", "").lower()
    }

    if not matches:
        await interaction.response.send_message(f"🔍 No matches found for **{busqueda}**.", ephemeral=True)
    elif len(matches) == 1:
        cm_data = next(iter(matches.values()))
        embed = build_cm_embed(cm_data, "track_overview")
        await interaction.response.send_message(embed=embed, view=CMSectionView(cm_data))
    else:
        # Menú desplegable si hay múltiples coincidencias
        await interaction.response.send_message(
            f"🔍 **Found {len(matches)} matches. Pick one:**",
            view=SearchMatchView(matches)
        )

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos Slash.")
    except Exception as e:
        print(f"Error sync: {e}")
    print(f"Bot listo como {bot.user}")

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
