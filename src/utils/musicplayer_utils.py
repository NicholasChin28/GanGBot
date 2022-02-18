import discord
from discord.ext import commands
import wavelink
from wavelink.player import Player
import typing

class MusicPlayerUtils():
    def __init__(self):
        pass

    @classmethod
    async def play_new(cls, ctx: commands.Context, *, search: wavelink.YouTubeTrack):
        if not ctx.voice_client:
            vc: Player = await ctx.author.voice.channel.connect(cls=Player)
        else:
            vc: Player = ctx.voice_client

    @classmethod
    async def skip_new(cls, ctx: commands.Context):
        vc: Player = ctx.voice_client

        if not ctx.voice_client:
            return await ctx.send('Not currently connected to voice channel')

        if vc.is_playing():
            await vc.stop()

    @classmethod
    async def queue_new(cls, ctx: commands.Context):
        vc: Player = ctx.voice_client

        if not vc:
            return await ctx.send('No queue as not connected', delete_after=5)

        queue_embed = cls.queue_embed(cls, ctx)
        if queue_embed is None:
            return await ctx.send('Empty queue from newmusic')
        
        return await ctx.send(embed=queue_embed, delete_after=60)

    @classmethod
    async def pause_new(cls, ctx: commands.Context) -> typing.Union[discord.Message, bool]:
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

        return vc.is_paused()

    def queue_embed(self, ctx: commands.Context, title: typing.Optional[str] = 'Track queue') -> discord.Embed:
        vc: Player = ctx.voice_client
        if vc.track is None and vc.queue.count == 0:
            return None

        embed = discord.Embed(title=title, description='```css\nList of tracks in queue\n```', color=discord.Color.blurple())
        tracks_value = []
        tracks_value.append(vc.track.info.get('title'))

        for track in vc.queue:
            tracks_value.append(track.info.get('title'))

        desc_string = ""
        for idx, val in enumerate(tracks_value, start=1):
            desc_string += f'\n`{idx}.` {val}\n'

        embed.add_field(name='Tracks', value=desc_string)
        
        return embed
