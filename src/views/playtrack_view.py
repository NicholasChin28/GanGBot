import discord

# Play track input field
class LinkField(discord.ui.TextInput):
    def __init__(self):
        super().__init__(
            label='Youtube link',
            style=discord.TextInputStyle.short,
            placeholder='Only Youtube links supported',
            custom_id='pt_link'
        )

class PlaytrackInputModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title='Insert Youtube link')
        self.add_item(LinkField())

    async def callback(self, interaction: discord.Interaction):
        pass