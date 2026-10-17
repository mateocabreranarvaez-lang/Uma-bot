# ===== COMANDOS /skill Y /support =====

import json
from pathlib import Path
import discord
from discord import app_commands

DATA_DIR = Path(__file__).parent / "data"


def load_dataset(filename: str) -> list[dict]:
    path = DATA_DIR / filename
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def find_matches(dataset: list[dict], query: str) -> list[dict]:
    query = query.casefold().strip()
    if not query:
        return []

    results = []
    for item in dataset:
        searchable = [
            item.get("name", ""),
            item.get("character", ""),
            *item.get("aliases", []),
        ]
        if any(query in str(value).casefold() for value in searchable):
            results.append(item)

    return results


def make_embed(title: str, description: str = "") -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=description or "Descripción no disponible.",
        color=discord.Color.from_rgb(41, 67, 91),
    )
    embed.set_footer(text="Umalator CM Helper")
    return embed


# /skill: búsqueda independiente de skills
@bot.tree.command(
    name="skill",
    description="Busca una habilidad de Umamusume Global"
)
@app_commands.describe(nombre="Nombre de la skill")
async def skill(
    interaction: discord.Interaction,
    nombre: str
):
    skills = load_dataset("skills.json")
    matches = find_matches(skills, nombre)

    if not matches:
        await interaction.response.send_message(
            f"No encontré **{discord.utils.escape_markdown(nombre)}** "
            "en los datos locales de skills.",
            ephemeral=True
        )
        return

    if len(matches) > 1:
        choices = "\n".join(
            f"• {item.get('name', 'Nombre desconocido')}"
            for item in matches[:10]
        )
        await interaction.response.send_message(
            f"Encontré varias coincidencias:\n{choices}\n"
            "Prueba con un nombre más específico.",
            ephemeral=True
        )
        return

    item = matches[0]
    embed = make_embed(
        f"✨ {item.get('name', 'Skill')}",
        item.get("description", "Descripción no disponible.")
    )

    embed.add_field(
        name="Tipo",
        value=item.get("type", "Sin datos"),
        inline=True
    )
    embed.add_field(
        name="Coste SP",
        value=str(item.get("sp_cost", "Sin datos")),
        inline=True
    )
    embed.add_field(
        name="Rating ○",
        value=str(item.get("rating_o", "Pendiente de verificar")),
        inline=True
    )
    embed.add_field(
        name="Rating ◎",
        value=str(item.get("rating_oo", "Pendiente de verificar")),
        inline=True
    )

    variants = item.get("variants", [])
    if variants:
        embed.add_field(
            name="Variantes",
            value="\n".join(f"• {v}" for v in variants[:10]),
            inline=False
        )

    source = item.get("source_url")
    if source:
        embed.add_field(
            name="Fuente",
            value=f"[Consultar fuente]({source})",
            inline=False
        )

    await interaction.response.send_message(embed=embed)


# /support: búsqueda independiente de support cards
@bot.tree.command(
    name="support",
    description="Busca una Support Card de Umamusume Global"
)
@app_commands.describe(nombre="Nombre de la carta o personaje")
async def support(
    interaction: discord.Interaction,
    nombre: str
):
    supports = load_dataset("supports.json")
    matches = find_matches(supports, nombre)

    if not matches:
        await interaction.response.send_message(
            f"No encontré **{discord.utils.escape_markdown(nombre)}** "
            "en los datos locales de supports.",
            ephemeral=True
        )
        return

    if len(matches) > 1:
        choices = "\n".join(
            f"• {item.get('name', 'Nombre desconocido')}"
            for item in matches[:10]
        )
        await interaction.response.send_message(
            f"Encontré varias cartas:\n{choices}\n"
            "Usa un nombre más específico.",
            ephemeral=True
        )
        return

    item = matches[0]
    embed = make_embed(
        f"🃏 {item.get('name', 'Support Card')}",
        f"**Personaje:** {item.get('character', 'Sin datos')}"
    )

    embed.add_field(
        name="Rareza",
        value=item.get("rarity", "Sin datos"),
        inline=True
    )
    embed.add_field(
        name="Tipo",
        value=item.get("type", "Sin datos"),
        inline=True
    )
    embed.add_field(
        name="Limit Break",
        value=item.get("limit_break", "Sin datos"),
        inline=True
    )

    effects = item.get("effects", [])
    if effects:
        embed.add_field(
            name="Efectos",
            value="\n".join(f"• {effect}" for effect in effects[:8]),
            inline=False
        )

    hints = item.get("hints", [])
    if hints:
        embed.add_field(
            name="Hints",
            value="\n".join(f"• {hint}" for hint in hints[:8]),
            inline=False
        )

    source = item.get("source_url")
    if source:
        embed.add_field(
            name="Fuente",
            value=f"[Consultar carta]({source})",
            inline=False
        )

    await interaction.response.send_message(embed=embed)
