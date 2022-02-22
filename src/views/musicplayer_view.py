import discord
from discord.ext import commands
from utils.musicplayer_utils import MusicPlayerUtils
from views.playtrack_view import PlaytrackInputModal
from views.track_view import TrackView
from views.playsound_view import PlaysoundInputModal
from views.playtrack_view import PlaytrackInputModal
from models.emojis import Emojis

class MusicPlayerView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.queue_displays = []

    @discord.ui.button(label='Play', style=discord.ButtonStyle.red, custom_id='musicplayer_view:play')
    async def play(self, button: discord.ui.Button, interaction: discord.Interaction):
        ctx2 = interaction.user.voice.channel
        ctx = await self.bot.get_context(interaction.message)
        result = await interaction.response.send_modal(PlaytrackInputModal(ctx, self.bot.tqueuenew))
        print(f'Result from callback: {result}')

    @discord.ui.button(label='Modal', style=discord.ButtonStyle.green, custom_id='musicplayer_view:modal')
    async def modal(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(PlaysoundInputModal())

    @discord.ui.button(label='Skip', style=discord.ButtonStyle.red, emoji=Emojis.next_button, custom_id='musicplayer_view:skip')
    async def skip(self, button: discord.ui.Button, interaction: discord.Interaction):
        ctx = await self.bot.get_context(interaction.message)
        await interaction.response.send_message('This is skip')
        await MusicPlayerUtils.skip_new(ctx)

    @discord.ui.button(label='Queue', style=discord.ButtonStyle.blurple, emoji=Emojis.clipboard, custom_id='musicplayer_view:queue')
    async def queue(self, button: discord.ui.Button, interaction: discord.Interaction):
        ctx = await self.bot.get_context(interaction.message)
        await MusicPlayerUtils.queue_new(ctx)
        # track_info = await ctx.send('test')
        # self.queue_displays.append(track_info)
        # self.queue_displays.append(await ctx.send('Track info:', view=TrackView(ctx)))

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
        