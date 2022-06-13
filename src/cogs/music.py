import asyncio
from contextlib import suppress
import aiofiles
from pathlib import Path
from aiohttp import ClientSession
import async_timeout
import discord
import wavelink
from discord.ext import commands
from wavelink.player import Player
from wavelink.pool import Node
from wavelink.tracks import Track
import typing
import urllib.parse
from base64 import urlsafe_b64encode
from helper.s3_bucket import S3Bucket
from views.musicplayer_view import MusicPlayerView

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        bot.loop.create_task(self.connect_nodes())

    @property
    def tqueue(self):
        return self.bot.tqueuenew

    async def connect_nodes(self):
        '''Connect to Lavalink nodes.'''
        await self.bot.wait_until_ready()

        await wavelink.NodePool.create_node(bot=self.bot,
                                            host='127.0.0.1',
                                            port=2333,
                                            password='youshallnotpass')

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: Node):
        '''Event fired when a node has finished connecting.'''
        print(f'Node: <{node.identifier}> is ready')

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, player: Player, track: Track):
        if track.id in self.tqueue.keys():
            text_channel = self.bot.get_channel(self.tqueue.get(track.id).channel.id)
            await text_channel.send(embed=self.track_embed(self.tqueue.pop(track.id), track, title='Now playing'))

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: Player, track: Track, reason):
        try:
            with async_timeout.timeout(60):
                next_track = await player.queue.get_wait()
        except asyncio.TimeoutError:
            return await player.disconnect()
        finally:
            with suppress(UnboundLocalError):
                if next_track:
                    return await player.play(next_track)

    async def cog_load(self) -> None:
        print("Music cog loaded! from 2.0")

    async def cog_unload(self) -> None:
        print("Music cog unloaded! from 2.0")

    @commands.command()
    async def play(self, ctx: commands.Context, *, search: wavelink.YouTubeTrack):
        '''Play a song with the given search query
        
        If not connected, connect to our voice channel.
        '''
        if not ctx.voice_client:
            if ctx.author.voice is None:
                return await ctx.send('Please connect to a voice channel')
            vc: Player = await ctx.author.voice.channel.connect(cls=Player)
        else:
            vc: Player = ctx.voice_client

        if vc.queue.is_empty and not vc.is_playing():
            await vc.queue.put_wait(search)
            self.tqueue.update({search.id: ctx})
            await ctx.send(embed=self.track_embed(ctx, search, title='Added track'))
            await vc.play(await vc.queue.get_wait())
        else:
            await vc.queue.put_wait(search)
            self.tqueue.update({search.id: ctx})
            await ctx.send(embed=self.track_embed(ctx, search, title='Added track'))

    @commands.command()
    async def volume(self, ctx: commands.Context, *, volume: int = None):
        '''Sets or gets the volume'''
        vc: Player = ctx.voice_client

        if not vc:
            return await ctx.send('Not currently connected to voice channel', delete_after=5)

        if volume is None:
            return await ctx.send(f'Current volume is {vc.volume}')
        
        if 0 <= volume <= 100:
            await vc.set_volume(volume)
            await ctx.send(f'Volume set to {volume}')
        else:
            raise commands.BadArgument()

    @volume.error
    async def volume_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(f'```css\nPass a number between 0 to 100\nLike so: .volumew 20\n```')

    @commands.command()
    async def queue(self, ctx: commands.Context):
        '''Shows all tracks in queue'''
        vc: Player = ctx.voice_client

        if not vc:
            return await ctx.send('No queue as not connected', delete_after=5)

        queue_embed = self.queue_embed(ctx)
        if queue_embed is None:
            return await ctx.send('Empty queue')
        
        return await ctx.send(embed=queue_embed)

    @commands.command()
    async def stop(self, ctx: commands.Context):
        '''Stops current track and removes all tracks from queue'''
        vc: Player = ctx.voice_client

        if not vc:
            return await ctx.send('Bot not connected to voice channel', delete_after=10)

        if vc.queue.is_empty and not vc.is_playing():
            await ctx.send('Nothing to clear')
        else:
            vc.queue.clear()
            await vc.stop()
            await ctx.send('Tracks cleared')
        
    @commands.command()
    async def skip(self, ctx: commands.Context):
        '''Skip currently playing track'''
        vc: Player = ctx.voice_client

        if not ctx.voice_client:
            return await ctx.send('Not currently connected to voice channel')
        
        if vc.is_playing():
            await vc.stop()
            await ctx.send('Track skipped')
        else:
            return await ctx.send('Not playing anything right now')

    @commands.command()
    async def pause(self, ctx: commands.Context):
        '''Pauses the player'''
        vc: Player = ctx.voice_client

        if not ctx.voice_client:
            return await ctx.send('Not currently connected to voice channel')

        if not vc.is_playing():
            return await ctx.send('Not playing any track currently')
        
        if vc.is_paused():
            await ctx.send('Player was paused. Resuming now')
        else:
            await ctx.send('Player was playing. Pausing now')

        await vc.set_pause(not vc.is_paused())

    @commands.command()
    async def player(self, ctx: commands.Context):
        '''Alternative UI to perform bot music actions'''
        await ctx.send(view=MusicPlayerView(self.bot))

    def track_embed(self, ctx: commands.Context, track: wavelink.Track, title: typing.Optional[str] = 'Track') -> discord.Embed:
        if type(track) == wavelink.tracks.YouTubeTrack:
            embed = discord.Embed(title=title, description=f'```css\n{track.title}\n```', color=discord.Color.blurple())

            embed.add_field(name='Duration', value=track.duration)
            embed.add_field(name='Requested by', value=ctx.author.mention)
            embed.add_field(name='Source', value=track.author)
            
            embed.set_thumbnail(url=f'https://img.youtube.com/vi/{track.identifier}/maxresdefault.jpg')
        else:
            # Playsound
            embed = discord.Embed(title=title, description=f'```css\n{track.title}\n```', color=discord.Color.blurple())

            embed.add_field(name='Duration', value=f'{round(track.duration)} seconds')
            embed.add_field(name='Requested by', value=ctx.author.mention)
            embed.add_field(name='Source', value='Custom playsound')
            
        return embed

    def queue_embed(self, ctx: commands.Context, title: typing.Optional[str] = 'Track queue') -> discord.Embed:
        vc: Player = ctx.voice_client
        if vc.track is None and vc.queue.count == 0:
            return None

        embed = discord.Embed(title=title, description='```css\nList of tracks in queue\n```', color=discord.Color.blurple())
        tracks_value = []
        tracks_value.append(f'{vc.track.info.get("title")} (NOW PLAYING)')

        for track in vc.queue:
            tracks_value.append(track.info.get('title'))

        desc_string = ""
        for idx, val in enumerate(tracks_value, start=1):
            desc_string += f'\n`{idx}.` {val}\n'

        embed.add_field(name='Tracks', value=desc_string)
        
        return embed

async def setup(bot):
    await bot.add_cog(Music(bot))
