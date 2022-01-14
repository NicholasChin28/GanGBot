import wavelink
from discord.ext import commands
from wavelink.player import Player
from wavelink.pool import Node
from wavelink.tracks import Track

from helper.s3_bucket import S3Bucket

class NewMusic(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        bot.loop.create_task(self.connect_nodes())

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
    async def on_ready(self):
        print('New music cog loaded')

    @commands.command()
    async def playw(self, ctx: commands.Context, *, search: wavelink.YouTubeTrack):
        '''Play a song with the given search query.
        
        If not connected, connect to our voice channel.
        '''
        if not ctx.voice_client:
            vc: Player = await ctx.author.voice.channel.connect(cls=Player)
        else:
            vc: Player = ctx.voice_client

        await vc.play(search)

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

def setup(bot):
    bot.add_cog(NewMusic(bot))


        