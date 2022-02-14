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
import os
import pathlib
from dotenv import load_dotenv, find_dotenv

import discord
from discord.ext import commands
from helper import helper
from views.musicplayer_view import MusicPlayerView

intents = discord.Intents(messages=True, guilds=True, members=True, voice_states=True)

class MaldBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or('.', '?'), description='GanG スター Bot', intents=intents)
        self.musicplayer_view_added = False

    async def on_ready(self):
        print(f'Logged in as \n{self.user.name}\n{self.user.id}')
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='yumans'))
        # Load cogs
        for filename in self.get_cogs():
            self.load_extension(f'cogs.{filename}')

        if not self.musicplayer_view_added:
            self.add_view(MusicPlayerView(self))
            self.musicplayer_view_added = True

    def get_cogs(self):
        cogs_path = pathlib.Path(pathlib.Path.cwd() / 'cogs').glob('**/*')
        cogs = [x.stem for x in cogs_path if x.is_file() and x.suffix == '.py' and x.stem != 'custom_help']
        return cogs


bot = MaldBot()

# Load environment variables
load_dotenv(find_dotenv())
TOKEN = os.getenv('DISCORD_TOKEN')

bot.run(TOKEN)
