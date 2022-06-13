import discord
import typing
from discord.ext import commands
from utils.musicplayer_utils import MusicPlayerUtils

# Play track input field
class LinkField(discord.ui.TextInput):
    def __init__(self):
        super().__init__(
            label='Search query',
            style=discord.TextStyle.short,
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

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        search = self.children[0].value
        
        await MusicPlayerUtils.play(user=self.user, ctx=self.ctx, tqueue=self.tqueue, search=search)
        await interaction.response.send_message('Adding track', ephemeral=True)
