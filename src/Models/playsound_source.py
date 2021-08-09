import youtube_dl
import asyncio
import discord
from discord.ext import commands
from pydub import AudioSegment
import validators
from aiohttp import ClientSession
import aiofiles
import mutagen
import pathlib
from helper import helper
from pathlib import Path


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
    async def create_source(cls, ctx: commands.Context, timestamp: str, file_upload=False, url=None):
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            url = attachment.url
            filename = attachment.filename
            file_ext = pathlib.Path(filename).suffix
        else:
            url = url

        loop = asyncio.get_event_loop()

        if not validators.url(url):
            raise Exception("Invalid url")


        if file_upload:
            # Download file to temp file to get the duration
            async with ClientSession() as session:
                async with session.get(url) as response:
                    if not response.status == 200:
                        raise Exception("Url not found")
                    async with aiofiles.tempfile.NamedTemporaryFile('wb+', delete=False, suffix=file_ext) as f:
                        await f.write(await response.read())
                        audio_file = mutagen.File(f.name)
                        duration = audio_file.info.length

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
                        print(f'start_time: {start_time.to_ms()}')
                        print(f'end_time: {end_time.to_ms()}')
                        
                        cropped_segment.export(filename, format=file_ext[1:])
                        cropped_playsound = discord.File(filename)  # Continue here
                        print(f'Finished cropping file')
                        message = await ctx.send(file=cropped_playsound)

                        return cls(ctx, data=data)
        else:
            duration = None
            async with ClientSession() as session:
                async with session.get("https://file-examples-com.github.io/uploads/2017/11/file_example_MP3_5MG.mp3") as response:
                    if not response.status == 200:
                        raise Exception("Url not found")
                    print(f'headers: {response.headers}')

                    # Try to get the duration with YoutubeDL
                    ydl_opts = {
                        'format': 'bestaudio/best',
                    }

                    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url)
                        duration = info['duration']

                    # YoutubeDL could not extract url duration
                    if duration is None:
                        pass

            
            # Use YTDL to extract info from link
            
    
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
                

        