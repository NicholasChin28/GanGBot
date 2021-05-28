# TODO: Pass context between different cogs
# TODO: Add an emoji to cancel votes
# TODO: Generate a helper decorator function to calculate the execution time of a function
# Reference link for helper decorator function: https://dev.to/s9k96/calculating-run-time-of-a-function-using-python-decorators-148o
# https://stackoverflow.com/questions/56796991/discord-py-changing-prefix-with-command
# For editing / removing help command: https://stackoverflow.com/questions/45951224/how-to-remove-default-help-command-or-change-the-format-of-it-in-discord-py

# TODO: Generate custom help command for the bot
# TODO: Generate embed for loaded and unloaded cogs: https://stackoverflow.com/questions/63036583/is-there-a-way-to-find-all-the-loaded-and-unloaded-cogs-in-discord-py-rewrite
# TODO: Add permissions error: https://stackoverflow.com/questions/52593777/permission-check-discord-py-bot
# from spotify_player import SpotifyCog, SpotTrack, SpotifyRealSource, SpotError
# from spotify_player import SpotifyCog
# from custom_poll import MyMenu
import os
import random
from dotenv import load_dotenv, find_dotenv
import time

import asyncio
import itertools
import functools
import math
from datetime import datetime

import discord
from discord.ext import commands
from discord.utils import get
import typing

from async_timeout import timeout

# Logging errors to the console
import logging

import youtube_dl

# Import Spotify source custom class
# import spotify_source

# For voting
import re
import string
import emoji

from helper import helper

# Inspiration code from: https://gist.github.com/vbe0201/ade9b80f2d3b64643d854938d40a0a2d
# Lookup command grouping in the future: https://stackoverflow.com/questions/62460182/discord-py-how-to-invoke-another-command-inside-another-one
# Use tasks, etc. @task.loop for automating timed tasks




bot = commands.Bot(command_prefix=['.', '?'], description='GanG スター Bot')
# Custom help embed


# bot.add_cog(Music(bot))
# bot.add_cog(Playsound(bot))
# bot.add_cog(CustomHelp(bot))

# Temporary cog for SpotifyCog
# bot.add_cog(SpotifyCog(bot))

# bot.add_cog(Greetings(bot))

'''
@bot.event
async def on_connect():
    # Set avatar of bot
    with open('Maldbot-01.jpg', 'rb') as f:
        image = f.read()
    await bot.user.edit(avatar=image)
'''

# Loads all cogs 
@bot.event
async def on_connect():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and not filename.startswith('custom_help'):
            bot.load_extension(f'cogs.{filename[0:-3]}')
    
    cogs = helper.get_cogs()
    print(f'Value of cogs: {cogs}')



@bot.event
async def on_ready():
    print('Logged in as \n{0.user.name}\n{0.user.id}'.format(bot))
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='yumans'))

# Load environment variables
load_dotenv(find_dotenv())
TOKEN = os.getenv('DISCORD_TOKEN')

bot.run(TOKEN)



