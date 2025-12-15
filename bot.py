import json
import discord
from discord.ext import commands

with open("config.json") as f:
    config = json.load(f)

TOKEN = config["DISCORD_TOKEN"]
BOT_ID = config["DISCORD_BOT_ID"]

MAX_GUESSES = 3
games = {}

bot = commands.Bot(
    command_prefix=None,
    help_command=None,
    is_case_insensitive=True,
    intents=discord.Intents.all(),
)

@bot.event
async def on_ready():
    print("Ready!")
    await bot.tree.sync()

@bot.tree.command(name="start_round")
async def start_round(interaction: discord.Interaction, secret_answer: str):
    games[interaction.channel_id] = {
        "answer": secret_answer.lower(),
        "attempts": MAX_GUESSES
    }
    await interaction.response.send_message(f"Round started! {MAX_GUESSES} attempts.")

@bot.tree.command(name="guess")
async def guess(interaction: discord.Interaction, query: str):
    if interaction.channel_id not in games:
        await interaction.response.send_message("No game running.")
        return

    data = games[interaction.channel_id]
    
    if query.lower() == data["answer"]:
        await interaction.response.send_message(f"Correct! It was {data['answer']}")
        del games[interaction.channel_id]
    else:
        data["attempts"] -= 1
        left = data["attempts"]

        if left > 0:
            await interaction.response.send_message(f"Wrong. {left} attempts left.")
        else:
            await interaction.response.send_message(f"Game over. The song was {data['answer']}")
            del games[interaction.channel_id]

bot.run(TOKEN)