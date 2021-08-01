import asyncio
import discord
from discord.ext import commands
import validators
from aiohttp import ClientSession
import aiofiles
import mutagen
from helper import helper


class PlaysoundSource(discord.PCMVolumeTransformer):
    def __init__(self, ctx: commands.Context, *, data: dict):
        pass

    @classmethod
    async def create_source(cls, url: str, timestamp: str, requester: discord.Member, guild: discord.Guild, suffix: str, file_upload=False):
        loop = asyncio.get_event_loop()

        if not validators.url(url):
            raise Exception("Invalid url")

        if file_upload:
            # Download file to temp file to get the duration
            async with ClientSession() as session:
                async with session.get(url) as response:
                    if not response.status == 200:
                        raise Exception("Url not found")
                    async with aiofiles.tempfile.NamedTemporaryFile('wb+', delete=False, suffix=suffix) as f:
                        await f.write(await response.read())
                        audio_file = mutagen.File(f.name)
                        duration = audio_file.info.length

                        start_time, end_time = helper.parse_time2(timestamp, duration)
                        # TODO: Continue here
        else:
            pass

    # Validates and parses timestamp
    def parse_timestamp(self, timestamp: str, video_duration: int):
        video_time = self.to_hms(video_duration)

    # Converts seconds to h:m:s representation
    @staticmethod 
    def to_hms(s):
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return f'{h}:{m}:{s}'
                

        