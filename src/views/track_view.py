import discord
from discord.ext import commands
from wavelink.player import Player

class TrackSelect(discord.ui.Select):
    def __init__(self, ctx: commands.Context):
        # vc: Player = ctx.voice_client
        self.vc : Player = ctx.voice_client
        self.ctx = ctx

        # Set the options that will be presented inside the dropdown
        options = []
        options.append(discord.SelectOption(label='Track 1 (Now playing)', description=self.vc.track.info.get('title')))

        for idx, track in enumerate(self.vc.queue, start=2):
            options.append(discord.SelectOption(label=f'Track {idx}', description=track.info.get('title')))

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(placeholder='Select track for more info...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # Use the interaction object to send a response message containing
        # the user's favourite colour or choice. The self object refers to the
        # Select object, and the values attribute gets a list of the user's 
        # selected options. We only want the first one.
        # vc.queue
        await interaction.response.send_message(f'Your favourite colour is {self.values[0]}')

class TrackView(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__(timeout=10)

        # Adds the dropdown to the view object
        self.add_item(TrackSelect(ctx))

    async def on_timeout(self) -> None:
        print('TrackView timeout')
        self.clear_items()
        return await super().on_timeout()
