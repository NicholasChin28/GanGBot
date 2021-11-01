import io
import functools
import youtube_dl
import asyncio
import discord
from discord.ext import commands
from pydub import AudioSegment
import validators
from aiohttp import ClientSession
import aiofiles
import mutagen
from mutagen.mp3 import EasyMP3
import pathlib
from helper import helper
from helper.s3_bucket import S3Bucket
from pathlib import Path
import concurrent.futures
import base64

# TODO: Add another playsound class for compatibility with current Sound class and queue

# Temporary class for playing audio
class PlaysoundSource_supernew(discord.PCMVolumeTransformer):
    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.title = 'test'
        self.duration = 90

    @classmethod
    async def get_source(cls, ctx: commands.Context, playsound: str, *, loop: asyncio.BaseEventLoop):
        loop = asyncio.get_running_loop()

        test_con = S3Bucket()
        partial = functools.partial(test_con.get_playsound, name=playsound)
        s3_playsound = await loop.run_in_executor(None, partial)

        # Test getting the value of playsound
        print(f'Type of playsound: {type(s3_playsound)}')
        print(f'Value of playsound: {s3_playsound}')

        # return playsound
        base64_string = b'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'
        return cls(ctx, discord.FFmpegPCMAudio(s3_playsound), data=None)


class PlaysoundSource():
    def __init__(self, ctx: commands.Context, *, data: dict):
        self.uploader = ctx.author
        self.guild = ctx.guild
        self.data = data

        self.type = data.get('type')
        self.url = data.get('url')
        self.start_time = data.get('start_time')
        self.end_time = data.get('end_time')
        self.duration = data.get('duration')
        self.filename = data.get('filename')
        
    @classmethod
    async def create_source(cls, ctx: commands.Context, timestamp: str, file_upload=False, url=None):
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            url = attachment.url
            filename = f'{Path(attachment.filename).stem}_playsound{Path(attachment.filename).suffix}'
            file_ext = Path(filename).suffix
        else:
            url = url

        loop = asyncio.get_running_loop()

        if not validators.url(url):
            raise Exception("Invalid url")


        if file_upload:
            # Download file to temp file to get the duration
            async with ClientSession() as session:
                async with session.get(url) as response:
                    if not response.status == 200:
                        raise Exception("Url not found")
                    async with aiofiles.tempfile.NamedTemporaryFile('wb+', delete=False, suffix=file_ext) as f:
                        print(f'filename: {filename}')
                        await f.write(await response.read())
                        audio_file = mutagen.File(f.name)
                        duration = audio_file.info.length

                        type = "File"
                        try:
                            start_time, end_time = helper.parse_time2(timestamp, duration)
                            playsound_duration = (end_time.datetime - start_time.datetime).total_seconds()

                            if not helper.valid_filesize(playsound_duration):
                                return None

                            segment = AudioSegment.from_mp3(f.name)
                            cropped_segment = segment[start_time.to_ms():end_time.to_ms()]
                            print(f'start_time: {start_time.to_ms()}')
                            print(f'end_time: {end_time.to_ms()}')
                            
                            cropped_segment.export(filename, format=file_ext[1:])

                            data = {
                                "type": type,
                                "url": url,
                                "start_time": start_time,
                                "end_time": end_time,
                                "duration": playsound_duration,
                                "filename": filename,
                            }

                            # cropped_playsound = discord.File(filename)
                            # message = await ctx.send(file=cropped_playsound)
                            print('Finished cropping file')
                            
                            return cls(ctx, data=data)
                        except Exception as e:
                            return await ctx.send(e)
        else:
            info = None

            async with ClientSession() as session:
                async with session.get(url) as response:
                    if not response.status == 200:
                        raise Exception("Url not found")
                    print(f'headers: {response.headers}')

                    # For now assume, that user will give a valid url
                    with youtube_dl.YoutubeDL() as ydl:
                        info = ydl.extract_info(url, download=False)
                        duration = info['duration']
                        print(f'info: {info}')

                    # YoutubeDL could not extract url duration
                        if duration is None:
                            return await ctx.send("Youtube link does not have a duration.")

                        type = "Youtube"
                        try:
                            start_time, end_time = helper.parse_time2(timestamp, duration)
                            playsound_duration = (end_time.datetime - start_time.datetime).total_seconds()
                            
                            if not helper.valid_filesize(playsound_duration):
                                return None

                            diff = end_time.datetime - start_time.datetime
                            print(f'total_seconds: {diff.total_seconds()}')
                            
                            await ctx.send('Magically creating the playsound...')
                            partial = functools.partial(helper.download_playsound, url, start_time, end_time)
                            
                            download_result = await loop.run_in_executor(None, partial)
                            
                            if download_result.get('download_result'):
                                filename = download_result.get("filename")
                                # Verify playsound duration
                                # playsound = mutagen.File(Path(f'{info["title"]}_playsound.mp3'))
                                playsound = mutagen.File(Path(filename))
                                playsound_duration = playsound.info.length
                                print(f'Duration of cropped playsound: {playsound_duration}')

                                # If playsound duration is longer than requested length, crop the playsound duration to match requested length
                                if playsound_duration > diff.total_seconds():
                                    print('Double cropping beginning')
                                    # segment = AudioSegment.from_mp3(Path(f'{info["title"]}_playsound.mp3'))
                                    segment = AudioSegment.from_mp3(Path(filename))

                                    # Conversion logic here
                                    start_crop = (playsound_duration - diff.total_seconds()) * 1000
                                    end_crop = playsound_duration * 1000

                                    print(f'value of start_crop: {start_crop}')
                                    print(f'value of end_crop: {end_crop}')

                                    cropped_segment = segment[start_crop:end_crop]

                                    # cropped_segment.export(Path(f'{info["title"]}_playsound.mp3'), format="mp3")
                                    cropped_segment.export(Path(filename), format="mp3")
                                    
                                    # cropped_playsound = mutagen.File(Path(filename))
                                    cropped_playsound = mutagen.File(Path(filename))

                                    # cropped_playsound = discord.File(Path(f'{info["title"]}_playsound.mp3'))
                                    # cropped_playsound = discord.File(Path(filename))
                                    # message = await ctx.send(file=cropped_playsound)

                                data = {
                                        "type": type,
                                        "url": url,
                                        "start_time": start_time,
                                        "end_time": end_time,
                                        "duration": cropped_playsound.info.length,
                                        "filename": filename,
                                }
                                
                                return cls(ctx, data=data)
                        except Exception as e:
                            return await ctx.send(e)

                    # TODO: Find a way to create and close event loop. Current method causes multiple event loops to be open and not closed

    # Run from loop 
    @classmethod
    async def double_crop(cls, segment, start_crop, end_crop, filename):
        cropped_segment = segment[start_crop:end_crop]

        # cropped_segment.export(Path(f'{info["title"]}_playsound.mp3'), format="mp3")
        cropped_segment.export(Path(filename), format="mp3")

        return True

    # Get playsound from AWS S3 bucket
    @classmethod
    async def get_source(cls, ctx: commands.Context, name):
        loop = asyncio.get_running_loop()

        # test_con = S3Bucket()
        test_con = S3Bucket()
        partial = functools.partial(test_con.get_playsound, name=name)
        playsound = await loop.run_in_executor(None, partial)

        # Test getting the value of playsound
        print(f'Type of playsound: {type(playsound)}')
        print(f'Value of playsound: {playsound}')

        # return playsound
        return cls(ctx, discord.FFmpegPCMAudio(playsound), data=None)

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
                

        