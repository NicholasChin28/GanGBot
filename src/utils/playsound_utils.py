from discord.ext import commands
from urllib.parse import urlparse
import mutagen
from mutagen.id3 import ID3, TIT2, TPE1
import validators
import discord
from pathlib import Path
from helper import helper
from helper.s3_bucket import S3Bucket
import asyncio
import typing
from models.playsound import Playsound as PsObject
from pyaml_env import parse_config
from tortoise import Tortoise, run_async
from views.confirm import Confirm
from aiohttp import ClientSession

class PlaysoundUtils():
    def __init__(self):
        pass

    @classmethod
    # async def addps(cls, bot, user, link: str, ctx: commands.Context):
    async def addps(cls, bot: commands.Bot, link: str, name: str, ctx: commands.Context, user: typing.Union[discord.User, discord.Member], timestamp: typing.Optional[str] = None):
        # Get all playsounds
        loop = asyncio.get_event_loop()
        s3_con = S3Bucket()
        playsound_names = await loop.run_in_executor(None, s3_con.get_files, ctx)

        if name in playsound_names:
            return await ctx.send('A playsound with that name already exists. Try something else')

        video_unavailable = '"playabilityStatus:":{"status":"ERROR","reason":"Video unavailable"}'

        # Verify link provided
        if not validators.url(link) and 'youtube.com' in urlparse(link).netloc:
            return await ctx.send('Only Youtube links supported')

        async with ClientSession() as session:
            async with session.get(link) as resp:
                if video_unavailable in await resp.text():
                    return await ctx.send('Invalid Youtube link')
                try:
                    duration = await loop.run_in_executor(None, helper.extract_duration, link)
                except Exception as e:
                    return await ctx.send('Uh oh. An unexpected error occurred')

                # Construct the timestamp
                if timestamp:
                    try:
                        playsound_source_new = await loop.run_in_executor(None, helper.parse_time_new, timestamp, duration)
                        download_playsound = await loop.run_in_executor(None, helper.download_playsound_new, link, playsound_source_new.start_time, playsound_source_new.end_time, playsound_source_new.duration)
                    except Exception as e:
                        print(e)
                        return await ctx.send(e)
                else:
                    if duration > 20:
                        return await ctx.send('Only playsounds 20 seconds or less can be added')
                    
                    download_playsound = await loop.run_in_executor(None, helper.download_playsound_new, link, None, None, duration)

                if download_playsound.get('download_result'):
                    playsound = discord.File(download_playsound.get('filename'))
                    await ctx.send(file=playsound)

                    confirm_view = Confirm()
                    await ctx.send('Is this the correct playsound?', view=confirm_view)

                    await confirm_view.wait()

                    playsound_name = download_playsound.get('filename')
                    playsound_path = Path(playsound_name)

                    if confirm_view.value is None:
                        print('Timed out')
                        playsound_path.unlink()
                        await ctx.send('Timeout exceeded. Removing playsound')
                    elif confirm_view.value:
                        # Set playsound name
                        # await ctx.send('Give a cool name for the playsound!')

                        # Approve the playsound
                        try:
                            playsound_path = playsound_path.rename(f'{name}.mp3')

                            # Update the metadata
                            # https://en.wikipedia.org/wiki/ID3
                            # TPE1 = Artist
                            # TIT2 = Title
                            file = mutagen.id3.ID3(Path(f'{playsound_path.name}'))
                            file.add(TIT2(encoding=3, text=playsound_path.stem))
                            file.add(TPE1(encoding=3, text='Playsound'))
                            file.save()

                            print('Approving the playsound')
                            await ctx.send('Approving playsound')
                            # test_con = S3Bucket()
                            upload_results = await loop.run_in_executor(None, s3_con.upload_files, user.guild.id, playsound_path.name)
                            print(f'upload_results: {upload_results}')

                            # Save playsound details in database
                            tortoise_config = parse_config('./tortoise-config.yaml')
                            await Tortoise.init(config=tortoise_config)

                            await PsObject.create(
                                name=playsound_path.stem,
                                extension=playsound_path.suffix,
                                duration=download_playsound.get('file').info.length,
                                uploader=user.id,
                                played=0,
                                guild=user.guild.id,
                            )

                            await ctx.send('Playsound added!')
                            playsound_path.unlink()
                            
                            await Tortoise.close_connections()
                        except Exception as e:
                            print(e)
                            playsound_path.unlink()
                            return await ctx.send('Error when approving playsound. Check the logs')
                    else:
                        # Reject the playsound
                        await ctx.send('Rejecting playsound')
                        print('Rejecting the playsound')
                        playsound_path.unlink()
                        await ctx.send('Playsound rejected')
                else:
                    return await ctx.send('Unexpected error occurred. Please check logs')