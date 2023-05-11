import os
import pathlib
from dotenv import load_dotenv, find_dotenv
import logging
from pathlib import Path

import discord
from discord.ext import commands
from helper import helper
from views.musicplayer_view import MusicPlayerView

intents = discord.Intents(message_content=True, messages=True, guilds=True, members=True, voice_states=True)

class MaldBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or('.', '?'), description='GanG スター Bot', intents=intents)
        self.musicplayer_view_added = False
        self.__tqueuenew = {}

    @property
    def tqueuenew(self):
        return self.__tqueuenew

    async def setup_hook(self) -> None:
        self.add_view(MusicPlayerView(self))
        self.musicplayer_view_added = True
        for filename in self.get_cogs():
            await self.load_extension(f'cogs.{filename}')

    async def on_ready(self):        
        logging.info(f'Logged in as \n{self.user.name}\n{self.user.id}')
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='yumans'))
        
        """
        if not self.musicplayer_view_added:
            self.add_view(MusicPlayerView(self))
            self.musicplayer_view_added = True
        """

    async def close(self):        
        logging.info('Bot is closing!')
        await super().close()

    def get_cogs(self):
        cogs_path = pathlib.Path(pathlib.Path.cwd() / 'cogs').glob('**/*')
        cogs = [x.stem for x in cogs_path if x.is_file() and x.suffix == '.py' and x.stem != 'custom_help']
        return cogs


bot = MaldBot()

# Load environment variables
load_dotenv(find_dotenv())
TOKEN = os.getenv('DISCORD_TOKEN')

log_path = Path('logs/maldbot.log')
log_path.parent.mkdir(parents=True, exist_ok=True)
handler = logging.FileHandler(filename=str(log_path), encoding='utf-8', mode='a')

bot.run(TOKEN, log_handler=handler, log_level=logging.INFO, root_logger=True)
