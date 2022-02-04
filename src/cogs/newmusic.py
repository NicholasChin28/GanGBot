import discord
import wavelink
from discord.ext import commands
from wavelink.player import Player
from wavelink.pool import Node
from wavelink.tracks import Track
import typing

from helper.s3_bucket import S3Bucket
from views.musicplayer_view import MusicPlayerView

class NewMusic(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.__tqueue = {}

        bot.loop.create_task(self.connect_nodes())

    @property
    def tqueue(self):
        return self.__tqueue

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
        if not player.queue.is_empty:
            await player.play(await player.queue.get_wait())

    @commands.Cog.listener()
    async def on_ready(self):
        print('New music cog loaded')
        self.bot.add_command('skip_new')

    @commands.command()
    async def playw(self, ctx: commands.Context, *, search: wavelink.YouTubeTrack):
        '''Play a song with the given search query.
        
        If not connected, connect to our voice channel.
        '''
        if not ctx.voice_client:
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
    async def volumew(self, ctx: commands.Context, *, volume: int = None):
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

    @volumew.error
    async def volumew_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(f'```css\nPass a number between 0 to 100\nLike so: .volumew 20\n```')

    @commands.command()
    async def queuew(self, ctx: commands.Context):
        vc: Player = ctx.voice_client

        if not vc:
            return await ctx.send('No queue as not connected', delete_after=5)

        # TODO: Create embed for queue. Use webhook to allow clicking on queue item to display track
        queue_embed = self.queue_embed(ctx)
        if queue_embed is None:
            return await ctx.send('Empty queue from newmusic')
        
        return await ctx.send(embed=queue_embed)
        
    @commands.command()
    async def skipw(self, ctx: commands.Context):
        vc: Player = ctx.voice_client

        if not ctx.voice_client:
            return await ctx.send('Not currently connected to voice channel')
        
        if vc.is_playing():
            await vc.stop()

    @commands.command()
    async def pausew(self, ctx: commands.Context):
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
    async def preparew(self, ctx: commands.Context):
        await ctx.send("Whats your favourite colour", view=MusicPlayerView(self.bot))

    @commands.command()
    async def localw(self, ctx: commands.Context):
        node = wavelink.NodePool.get_node()
        # track = await node.get_tracks(f'./sample.mp3')
        s3bucket = S3Bucket()
        playsound = await s3bucket.get_fileplaysound(ctx=ctx, query='mald')
        track = await node.get_tracks(cls=wavelink.Track, query=f'{playsound.name}')
        # track = await node.get_tracks(cls=wavelink.Track, query=f'https://discord-playsounds.s3.ap-southeast-1.amazonaws.com/693996821692940429/mald.mp3')
        # track = await self.bot.wavelink.get_tracks(f'./sample.mp3')
        the_track = Track(track[0].id, track[0].info)
        if not ctx.voice_client:
            vc: Player = await ctx.author.voice.channel.connect(cls=Player)
        else:
            vc: Player = ctx.voice_client

        await vc.play(the_track)
        print(the_track)

        """
        if not ctx.voice_client:
            vc: Player = await ctx.author.voice.channel.connect(cls=Player)
        else:
            vc: Player = ctx.voice_client

        await vc.play(the_track)
        """

    def track_embed(self, ctx: commands.Context, track: wavelink.Track, title: typing.Optional[str] = 'Track') -> discord.Embed:
        embed = discord.Embed(title=title, description=f'```css\n{track.title}\n```', color=discord.Color.blurple())

        embed.add_field(name='Duration', value=track.duration)
        embed.add_field(name='Requested by', value=ctx.author.mention)
        embed.add_field(name='Source', value=track.author)
        embed.set_thumbnail(url=f'https://img.youtube.com/vi/{track.identifier}/maxresdefault.jpg')

        return embed

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

def setup(bot):
    bot.add_cog(NewMusic(bot))

