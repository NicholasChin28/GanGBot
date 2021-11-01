# TODO: Pass context between different cogs
# TODO: Add an emoji to cancel votes
# TODO: Generate a helper decorator function to calculate the execution time of a function
# Reference link for helper decorator function: https://dev.to/s9k96/calculating-run-time-of-a-function-using-python-decorators-148o
# https://stackoverflow.com/questions/56796991/discord-py-changing-prefix-with-command
# For editing / removing help command: https://stackoverflow.com/questions/45951224/how-to-remove-default-help-command-or-change-the-format-of-it-in-discord-py

# Lookup command grouping in the future: https://stackoverflow.com/questions/62460182/discord-py-how-to-invoke-another-command-inside-another-one
# Use tasks, etc. @task.loop for automating timed tasks

# TODO: Generate custom help command for the bot
# TODO: Add permissions error: https://stackoverflow.com/questions/52593777/permission-check-discord-py-bot
# from spotify_player import SpotifyCog, SpotTrack, SpotifyRealSource, SpotError
# from spotify_player import SpotifyCog
# from custom_poll import MyMenu
import os
from dotenv import load_dotenv, find_dotenv
import pathlib

import discord
from discord.ext import commands
from helper import helper

bot = commands.Bot(command_prefix=['.', '?'], description='GanG スター Bot')


@bot.event
async def on_ready():
    print('Logged in as \n{0.user.name}\n{0.user.id}'.format(bot))
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='yumans'))
    # Loads all cogs
    for filename in helper.get_cogs():
        bot.load_extension(f'cogs.{filename}')

# Load environment variables
load_dotenv(find_dotenv())
TOKEN = os.getenv('DISCORD_TOKEN')

bot.run(TOKEN)
