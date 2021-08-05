import asyncio
import discord
from discord.ext import commands
from pydub import AudioSegment
import validators
from aiohttp import ClientSession
import aiofiles
import mutagen
from helper import helper


class PlaysoundSource():
    def __init__(self, ctx: commands.Context, *, data: dict):
        self.requester = ctx.author
        self.guild = ctx.guild
        self.data = data

        self.type = data.get('type')
        self.url = data.get('url')
        self.start_time = data.get('start_time')
        self.end_time = data.get('end_time')
        
    @classmethod
    async def create_source(cls, ctx: commands.Context, url: str, timestamp: str, requester: discord.Member, guild: discord.Guild, suffix: str, file_upload=False):
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
                        duration = audio_file.info.length       # Problem is here. Duration is in seconds, eg. 19.238

                        type = "File"
                        start_time, end_time = helper.parse_time2(timestamp, duration)
                        
                        data = {
                            "type": type,
                            "url": url,
                            "start_time": start_time,
                            "end_time": end_time,
                        }

                        segment = AudioSegment.from_mp3(f.name)
                        cropped_segment = segment[start_time.to_ms():end_time.to_ms()]

                        cropped_segment.export("Superrandomname", format=".mp3")
                        cropped_playsound = discord.File(cropped_segment)
                        print(f'Finished cropping file')
                        message = await ctx.send(file=cropped_playsound)

                        return cls(ctx, data=data)
        else:
            pass
    
    # TODO: Extract from the actual downloaded file

    # Validates and parses timestamp
    def parse_timestamp(self, timestamp: str, video_duration: int):
        video_time = self.to_hms(video_duration)

    # Converts seconds to h:m:s representation
    @staticmethod 
    def to_hms(s):
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return f'{h}:{m}:{s}'
                

        