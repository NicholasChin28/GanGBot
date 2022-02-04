import discord
from discord.ext import commands
from utils.musicplayer_utils import MusicPlayerUtils
from models.emojis import Emojis

class MusicPlayerView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label='Green', style=discord.ButtonStyle.green, custom_id='musicplayer_view:green')
    async def green(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message('This is green')
        # button.label = 'Change to green'
        # button.refresh_component(button)

    @discord.ui.button(label='Red', style=discord.ButtonStyle.red, custom_id='persistent_view:red')
    async def red(self, button: discord.ui.Button, interaction: discord.Interaction):
        # await interaction.response.send_message('This is red.')
        button.label = "Now I am red"
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label='Grey', style=discord.ButtonStyle.grey, custom_id='persistent_view:grey')
    async def grey(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message('This is grey.')

    @discord.ui.button(label='Skip', style=discord.ButtonStyle.red, emoji=Emojis.next_button, custom_id='musicplayer_view:skip')
    async def skip(self, button: discord.ui.Button, interaction: discord.Interaction):
        ctx = await self.bot.get_context(interaction.message)
        await interaction.response.send_message('This is skip')
        await MusicPlayerUtils.skip_new(ctx)

    @discord.ui.button(label='Queue', style=discord.ButtonStyle.blurple, custom_id='musicplayer_view:queue')
    async def queue(self, button: discord.ui.Button, interaction: discord.Interaction):
        ctx = await self.bot.get_context(interaction.message)
        await interaction.response.send_message('This is queue')
        await MusicPlayerUtils.queue_new(ctx)

    @discord.ui.button(label='Pause', style=discord.ButtonStyle.blurple, emoji=Emojis.stop_button, custom_id='musicplayer_view:pause_resume')
    async def pause_resume(self, button: discord.ui.Button, interaction: discord.Interaction):
        ctx = await self.bot.get_context(interaction.message)
        is_paused = await MusicPlayerUtils.pause_new(ctx)
        if is_paused:
            button.label = 'Resume'
            button.emoji = Emojis.play_button
            await interaction.response.edit_message(view=self)
        elif not is_paused:
            button.label = 'Pause'
            button.emoji = Emojis.stop_button
            await interaction.response.edit_message(view=self)

class MusicPlayerViewNew(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Edited to green', style=discord.ButtonStyle.green, custom_id='musicplayer_view:edit_green')
    async def green(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message('This is an edited green')
        