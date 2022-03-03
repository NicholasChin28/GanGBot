import discord
from discord.ext import commands
import wavelink
from wavelink.player import Player
import typing

class MusicPlayerUtils():
    def __init__(self):
        pass

    @classmethod
    async def play(cls, user: typing.Union[discord.User, discord.Member], ctx: commands.Context, tqueue: typing.Dict, *, search):
        if not ctx.voice_client:
            if user.voice is None:
                return await ctx.send('Please connect to a voice channel')
            vc: Player = await user.voice.channel.connect(cls=Player)
        else:
            vc: Player = ctx.voice_client

        track = await wavelink.YouTubeTrack.search(query=search, return_first=True)

        if vc.queue.is_empty and not vc.is_playing():
            await vc.queue.put_wait(track)
            tqueue.update({track.id: ctx})  # TODO: Update with user ctx and not bot ctx
            await ctx.send(embed=cls.track_embed(cls, track, user, title='Added track'))
            await vc.play(await vc.queue.get_wait())
        else:
            await vc.queue.put_wait(track)
            tqueue.update({track.id: ctx})
            await ctx.send(embed=cls.track_embed(cls, track, user, title='Added track'))            

    @classmethod
    async def stop(cls, ctx: commands.Context):
        vc: Player = ctx.voice_client

        if not vc:
            return await ctx.send('Bot not connected to voice channel', delete_after=10)

        if vc.queue.is_empty and not vc.is_playing():
            await ctx.send('Nothing to clear')
        else:
            vc.queue.clear()
            await vc.stop()
            await ctx.send('Tracks cleared')

    @classmethod
    async def skip(cls, ctx: commands.Context):
        vc: Player = ctx.voice_client

        if not ctx.voice_client:
            return await ctx.send('Not currently connected to voice channel')

        if vc.is_playing():
            await vc.stop()
            await ctx.send('Track skipped')
        else:
            return await ctx.send('Not playing anything right now')

    @classmethod
    async def queue(cls, ctx: commands.Context):
        vc: Player = ctx.voice_client

        if not vc:
            return await ctx.send('No queue as not connected', delete_after=5)

        queue_embed = cls.queue_embed(cls, ctx)
        if queue_embed is None:
            return await ctx.send('Empty queue')
        
        return await ctx.send(embed=queue_embed, delete_after=60)

    @classmethod
    async def pause(cls, ctx: commands.Context) -> typing.Union[discord.Message, bool]:
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

    def track_embed(self, track: wavelink.Track, user: typing.Union[discord.User, discord.Member], title: typing.Optional[str] = 'Track') -> discord.Embed:
        if type(track) == wavelink.tracks.YouTubeTrack:
            embed = discord.Embed(title=title, description=f'```css\n{track.title}\n```', color=discord.Color.blurple())

            embed.add_field(name='Duration', value=track.duration)
            embed.add_field(name='Requested by', value=user.mention)
            embed.add_field(name='Source', value=track.author)
            
            embed.set_thumbnail(url=f'https://img.youtube.com/vi/{track.identifier}/maxresdefault.jpg')
        else:
            # Playsound
            embed = discord.Embed(title=title, description=f'```css\n{track.title}\n```', color=discord.Color.blurple())

            embed.add_field(name='Duration', value=f'{round(track.duration)} seconds')
            embed.add_field(name='Requested by', value=user.mention)
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
