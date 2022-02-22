from discord.ext import commands
from urllib.parse import urlparse
import validators
from helper import helper
from helper.s3_bucket import S3Bucket
import asyncio
from models.playsound import Playsound as PsObject
from pyaml_env import parse_config
from tortoise import Tortoise, run_async
from views.confirm import Confirm
from aiohttp import ClientSession

class PlaysoundUtils():
    def __init__(self):
        pass

    @classmethod
    async def addps(cls, bot, user, link: str, ctx: commands.Context):
        def uploader_check(message):
            return message.author == user

        video_unavailable = '"playabilityStatus:":{"status":"ERROR","reason":"Video unavailable"}'

        # Verify link provided
        if not validators.url(link) and 'youtube.com' in urlparse(link).netloc:
            return await ctx.send('Only Youtube links supported')

        async with ClientSession() as session:
            async with session.get(link) as resp:
                print(await resp.text())
                if video_unavailable in await resp.text():
                    return await ctx.send('Invalid Youtube link')

                loop = asyncio.get_event_loop()
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
                    
                    download_playsound = await loop.run_in_executor(None, helper.download_playsound_new, link)

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
                        await ctx.send('Give a cool name for the playsound!')
                        try:
                            name = await self.bot.wait_for('message', timeout=15, check=uploader_check)
                        except asyncio.TimeoutError:
                            playsound_path.unlink()
                            return await ctx.send('Timeout exceeded. Removing playsound')

                        # Approve the playsound
                        try:
                            # playsound_path = playsound_path.rename(f'{name.content}')     # Throwing error here
                            playsound_path = playsound_path.rename(f'{name.content}.mp3')
                            print('Approving the playsound')
                            await ctx.send('Approving playsound')
                            test_con = S3Bucket()
                            upload_results = await loop.run_in_executor(None, test_con.upload_files, ctx, playsound_path.name)
                            print(f'upload_results: {upload_results}')

                            # Save playsound details in database
                            tortoise_config = parse_config('./tortoise-config.yaml')
                            await Tortoise.init(config=tortoise_config)

                            await PsObject.create(
                                name=download_playsound.get('filename'),
                                duration=10,
                                uploader=ctx.author.id,
                                played=0,
                                guild=ctx.author.guild.id,
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