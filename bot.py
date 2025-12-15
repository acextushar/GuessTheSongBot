import json
import discord
from discord.ext import commands
from discord import ui

with open("config.json") as f:
    config = json.load(f)

TOKEN = config["DISCORD_TOKEN"]

MAX_GUESSES = 3
games = {}

bot = commands.Bot(
    command_prefix=None,
    help_command=None,
    is_case_insensitive=True,
    intents=discord.Intents.all(),
)

class StartRoundModal(ui.Modal, title="Start a New Round"):
    answer = ui.TextInput(label="Secret Song Name", placeholder="Enter the song name here...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        secret_answer = self.answer.value.strip().lower()
        
        if not secret_answer:
            await interaction.response.send_message("Answer cannot be empty!", ephemeral=True)
            return

        games[interaction.channel_id] = {
            "answer": secret_answer,
            "attempts": MAX_GUESSES
        }
        
        await interaction.response.send_message(f"Round started! Guess the song! \nAttempts allowed: **{MAX_GUESSES}**")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync()

@bot.tree.command(name="start_round")
async def start_round(interaction: discord.Interaction):
    await interaction.response.send_modal(StartRoundModal())

@bot.tree.command(name="guess")
async def guess(interaction: discord.Interaction, query: str):
    query = query.strip()
    if not query:
        await interaction.response.send_message("Please enter a valid guess.", ephemeral=True)
        return

    if interaction.channel_id not in games:
        await interaction.response.send_message("No game running in this channel.", ephemeral=True)
        return

    data = games[interaction.channel_id]
    
    if query.lower() == data["answer"]:
        await interaction.response.send_message(f"Correct! The song was **{data['answer']}**!")
        del games[interaction.channel_id]
    else:
        data["attempts"] -= 1
        left = data["attempts"]

        if left > 0:
            await interaction.response.send_message(f"Wrong. **{left}** attempts left.")
        else:
            await interaction.response.send_message(f"Game over! The song was ||{data['answer']}||")
            del games[interaction.channel_id]

bot.run(TOKEN)