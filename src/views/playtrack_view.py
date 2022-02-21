import discord

# Play track input field
class LinkField(discord.ui.TextInput):
    def __init__(self):
        super().__init__(
            label='Search query',
            style=discord.TextInputStyle.short,
            placeholder='Only Youtube links supported',
            custom_id='pt_link'
        )

class PlaytrackInputModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title='Play music')
        self.add_item(LinkField())

    async def callback(self, interaction: discord.Interaction):
        # Call musicplayer_utils
        pass