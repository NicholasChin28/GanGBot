import discord
import typing
from discord.ext import commands
from utils.musicplayer_utils import MusicPlayerUtils

# Play track input field
class LinkField(discord.ui.TextInput):
    def __init__(self):
        super().__init__(
            label='Search query',
            style=discord.TextInputStyle.short,
            placeholder='Only Youtube links supported',
            min_length=1,
            custom_id='pt_link'
        )

class PlaytrackInputModal(discord.ui.Modal):
    def __init__(self, user: typing.Union[discord.User, discord.Member], ctx: commands.Context, tqueue):
        super().__init__(title='Play something')
        self.user = user
        self.ctx = ctx
        self.tqueue = tqueue
        self.add_item(LinkField())

    async def callback(self, interaction: discord.Interaction):
        test = interaction
        test2 = self.children
        search = self.children[0].value
        
        await MusicPlayerUtils.play_new(user=self.user, ctx=self.ctx, tqueue=self.tqueue, search=search)