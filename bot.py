import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

class MiBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("¡Comandos de barra '/' sincronizados correctamente!")

bot = MiBot()

@bot.event
async def on_ready():
    print(f'¡Bot conectado como: {bot.user}!')

# Base de datos organizada por secciones para el menú
CM_DATA = {
    "sagitario": {
        "titulo": "Sagitario Cup",
        "secciones": {
            "track": {
                "titulo": "🏟️ Track Info & Target Stats",
                "descripcion": (
                    "• **Distance:** 2500m (Long)\n"
                    "• **Track:** Turf\n"
                    "• **Turn:** Right (Clockwise)\n"
                    "• **Season / Weather:** Winter / Cloudy / Slight\n\n"
                    "📊 **Target Stats Recomendadas:**\n\n"
                    "🏆 **Graded League (Sin Límite):**\n"
                    "• *Speed:* 1200\n"
                    "• *Stamina:* 900 - 1000 (+ 2 Gold Recovery Skills)\n"
                    "• *Power:* 900+\n"
                    "• *Guts:* 400+\n"
                    "• *Wits:* 600+\n\n"
                    "🛡️ **Open League (Cap A / A+):**\n"
                    "• *Speed:* 1000\n"
                    "• *Stamina:* 800 (+ 1-2 Gold Recovery Skills)\n"
                    "• *Power:* 800\n"
                    "• *Guts:* 350\n"
                    "• *Wits:* 400 - 500 (Ajustar para no superar el límite de puntos)"
                ),
                "color": discord.Color.gold(),
                "imagen": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f3c7.png"
            },
            "styles": {
                "titulo": "🏆 Hierarchy of Running Styles",
                "descripcion": (
                    "Orden de estilos recomendados de **mejor (1º)** a **peor (último)**:\n\n"
                    "1️⃣ **Pace / Leader:** Es el estilo más consistente. Con buena *Stamina* y un acelerador de herencia clave, tiene una ventana de victoria muy estable.\n"
                    "2️⃣ **Front Runner:** Muy fuerte si logras conseguir la delantera antes de la última curva, pero requiere inversión alta en *Speed* e herencias de aceleración.\n"
                    "3️⃣ **Late Surger / Betweener:** Buena potencia en el *Spurt* final, pero depende mucho de no quedar atrapado en el tráfico de la curva.\n"
                    "4️⃣ **Chaser:** Sufre un poco más en esta distancia por el trazado de las curvas, aunque con las skills adecuadas puede sorprender."
                ),
                "color": discord.Color.blue(),
                "imagen": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f3c7.png"
            },
            "umas": {
                "titulo": "🏇 Recommended Umas & Inheritance",
                "descripcion": (
                    "⭐ **Top Tier Umas:**\n"
                    "• Oguri Cap (Christmas)\n"
                    "• Narita Taishin\n"
                    "• Gold Ship\n\n"
                    "🧬 **Required Inheritance (Parents Skills):**\n"
                    "• **Angling x Scheming** (Seiun Sky Unique) ➔ Indispensable para *Front Runner* y *Pace* para activar la aceleración al entrar al tramo final.\n"
                    "• **Let's Anabolic!** (Mejiro Ryan Unique) ➔ Acelerador clave para estilos que vienen desde atrás."
                ),
                "color": discord.Color.green(),
                "imagen": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f3c7.png"
            },
            "supports": {
                "titulo": "🎴 Support Cards (Whale vs F2P)",
                "descripcion": (
                    "🐳 **Whale Setup (Full Dupes SSR):**\n"
                    "• **Speed:** SSR Kitasan Black\n"
                    "• **Stamina:** SSR Super Creek\n"
                    "• **Wits:** SSR Fine Motion\n\n"
                    "🆓 **F2P Setup (SR & Event SSR):**\n"
                    "• **Speed:** SR Sweep Tosho / SR Eishin Flash\n"
                    "• **Stamina:** SR Manhattan Cafe\n"
                    "• **Event SSR:** SSR Daiwa Scarlet"
                ),
                "color": discord.Color.purple(),
                "imagen": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f3c7.png"
            },
            "skills": {
                "titulo": "⚡ Key Skills & Priority",
                "descripcion": (
                    "🚨 **Core Acceleration Skills (Prioridad Máxima):**\n"
                    "• *Nonstop Girl* / *Straight Shot* (Para cerrar con máxima velocidad en el *Last Spurt*).\n\n"
                    "💚 **Recovery Skills (Stamina):**\n"
                    "• *Swinging Maestro* (Esta skill es fundamental por su altísima recuperación de stamina en carreras de categoría Long).\n"
                    "• *Cool Down* / *Gourmand* (Opciones secundarias si falta stamina base).\n\n"
                    "🎯 **Speed Skills:**\n"
                    "• *Profundidad de curva* / *Posicionamiento de recta*."
                ),
                "color": discord.Color.red(),
                "imagen": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f3c7.png"
            }
        }
    }
}

# Definición de la barra / menú desplegable interactivo
class CMSelectMenu(discord.ui.Select):
    def __init__(self, cm_key: str):
        self.cm_key = cm_key
        options = [
            discord.SelectOption(
                label="Información de Pista & Stats",
                value="track",
                description="Datos de la carrera y Target Stats para Graded/Open",
                emoji="🏟️"
            ),
            discord.SelectOption(
                label="Jerarquía de Estilos de Carrera",
                value="styles",
                description="Ranking de estilos (Pace, Front Runner, etc.)",
                emoji="🏆"
            ),
            discord.SelectOption(
                label="Umas Recomendadas & Herencias",
                value="umas",
                description="Top Umas y Unique Skills obligatorias de herencia",
                emoji="🏇"
            ),
            discord.SelectOption(
                label="Cartas de Soporte (Whales vs F2P)",
                value="supports",
                description="Setups recomendados para ballenas y opciones F2P",
                emoji="🎴"
            ),
            discord.SelectOption(
                label="Habilidades Clave & Prioridad",
                value="skills",
                description="Core Acceleration, Recovery y Speed Skills",
                emoji="⚡"
            ),
        ]
        super().__init__(placeholder="SELECCIONA UNA SECCIÓN DE LA CM...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # Cuando el usuario elige una opción en la barra, recuperamos la sección
        seccion_key = self.values[0]
        seccion_data = CM_DATA[self.cm_key]["secciones"][seccion_key]

        embed = discord.Embed(
            title=f"{CM_DATA[self.cm_key]['titulo']} - {seccion_data['titulo']}",
            description=seccion_data["descripcion"],
            color=seccion_data["color"]
        )
        embed.set_thumbnail(url=seccion_data["imagen"])
        embed.set_footer(text="Umalator CM Helper • Usa el menú de abajo para cambiar de sección")

        # Editamos el mensaje existente
        await interaction.response.edit_message(embed=embed, view=self.view)


class CMView(discord.ui.View):
    def __init__(self, cm_key: str):
        super().__init__(timeout=180) # La barra se mantiene activa por 3 minutos
        self.add_item(CMSelectMenu(cm_key))


@bot.tree.command(name="champions_meeting", description="Obtén la guía interactiva para una Champions Meeting específica")
@app_commands.choices(cm=[
    app_commands.Choice(name="Sagitario Cup", value="sagitario"),
])
async def champions_meeting(interaction: discord.Interaction, cm: app_commands.Choice[str]):
    await interaction.response.defer()

    cm_key = cm.value
    data = CM_DATA.get(cm_key)

    if not data:
        await interaction.followup.send("No se encontró información para esa Champions Meeting.")
        return

    # Cargamos por defecto la primera sección (Track Info & Stats)
    primera_seccion = data["secciones"]["track"]
    embed_inicial = discord.Embed(
        title=f"{data['titulo']} - {primera_seccion['titulo']}",
        description=primera_seccion["descripcion"],
        color=primera_seccion["color"]
    )
    embed_inicial.set_thumbnail(url=primera_seccion["imagen"])
    embed_inicial.set_footer(text="Umalator CM Helper • Usa el menú de abajo para cambiar de sección")

    view = CMView(cm_key)
    await interaction.followup.send(embed=embed_inicial, view=view)


import os

TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN is None:
    print("Error: No se encontró la variable DISCORD_TOKEN.")
else:
    bot.run(TOKEN)