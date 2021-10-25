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
        print(f'Type of playsound: {type(playsound)}')
        print(f'Value of playsound: {playsound}')

        # return playsound
        return cls(ctx, discord.FFmpegPCMAudio(playsound), data=None)


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
                

        