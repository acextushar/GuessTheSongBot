import json
import discord
from discord.ext import commands
from discord import ui
import random
import time
import requests

# --- CONFIG LOADING ---
try:
    with open("config.json") as f:
        config = json.load(f)
except FileNotFoundError:
    exit()

TOKEN = config["DISCORD_TOKEN"]

# --- GLOBAL VARIABLES ---
MAX_GUESSES = 3
games = {} 

# --- DUMMY API FUNCTION (WITH ERROR HANDLING) ---
def get_songs_from_input(query: str):
    """
    Simulates fetching songs from a music API.
    Raises ValueError on invalid/empty input, fulfilling Issue #25 core logic.
    """
    if "invalid" in query.lower() or "broken" in query.lower():
        raise ValueError("The provided URL or ID is invalid or points to an empty resource.")
    
    time.sleep(1) 
    
    if "album" in query.lower():
        return ["Stairway to Heaven", "Bohemian Rhapsody", "Hotel California", "Imagine"]
    elif "playlist" in query.lower():
        return ["Happy Song", "Mellow Tune", "Banger"]
    else:
        raise ValueError("Input format not recognized. Please provide a valid album/playlist URL or ID.")


# --- MODALS AND VIEWS (UI ELEMENTS) ---
class StartRoundModal(ui.Modal, title="Start a New Round"):
    source_query = ui.TextInput(
        label="Album/Playlist URL or ID", 
        placeholder="e.g., spotify:album:1ASas...", 
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        query = self.source_query.value.strip()

        # ISSUE #25 IMPLEMENTATION: Try/except block for error handling
        try:
            song_list = get_songs_from_input(query)
            
            if not song_list:
                await interaction.followup.send("The provided link or ID did not contain any playable songs. Please try a different one.", ephemeral=True)
                return
            
            secret_answer = random.choice(song_list).lower()
            source_name = "from your input"
            
            games[interaction.channel_id] = {
                "answer": secret_answer,
                "attempts": MAX_GUESSES,
                "source": source_name 
            }
            
            await interaction.followup.send(
                f"Round started with a song from **{source_name}**! Guess the song! \nAttempts allowed: **{MAX_GUESSES}**"
            )

        except ValueError as e:
            await interaction.followup.send(f"**Input Error:** {e}\n\nPlease try again with a valid Spotify/music URL or ID.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"An unexpected error occurred while fetching songs. Please try again later.", ephemeral=True)


# --- BOT SETUP ---
bot = commands.Bot(
    command_prefix=None,
    help_command=None,
    is_case_insensitive=True,
    intents=discord.Intents.all(),
)


# --- BOT EVENTS ---
@bot.event
async def on_ready():
    await bot.tree.sync()

# --- BOT COMMANDS ---
@bot.tree.command(name="start_round", description="Starts a new song guessing round using an album or playlist.")
async def start_round(interaction: discord.Interaction):
    await interaction.response.send_modal(StartRoundModal())

@bot.tree.command(name="guess", description=f"Guess the secret song. You have {MAX_GUESSES} attempts.")
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