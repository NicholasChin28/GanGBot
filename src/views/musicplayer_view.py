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

    @discord.ui.button(label='Play', style=discord.ButtonStyle.red, emoji=Emojis.play_button, custom_id='musicplayer_view:play')
    async def play(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        ctx = await self.bot.get_context(interaction.message)
        await interaction.response.send_modal(PlaytrackInputModal(user, ctx, self.bot.tqueuenew))

    @discord.ui.button(label='Add playsound', style=discord.ButtonStyle.green, emoji=Emojis.music_note, custom_id='musicplayer_view:add_ps')
    async def add_playsound(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PlaysoundInputModal(self.bot))
    
    @discord.ui.button(label='Skip', style=discord.ButtonStyle.red, emoji=Emojis.next_button, custom_id='musicplayer_view:skip')
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        ctx = await self.bot.get_context(interaction.message)
        await MusicPlayerUtils.skip(ctx)

    @discord.ui.button(label='Queue', style=discord.ButtonStyle.red, emoji=Emojis.clipboard, custom_id='musicplayer_view:queue')
    async def queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        ctx = await self.bot.get_context(interaction.message)
        await MusicPlayerUtils.queue(ctx)

    @discord.ui.button(label='Pause', style=discord.ButtonStyle.blurple, emoji=Emojis.play_pause, custom_id='musicplayer_view:pause_resume')
    async def pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        ctx = await self.bot.get_context(interaction.message)
        is_paused = await MusicPlayerUtils.pause(ctx)
        if is_paused:
            button.label = 'Resume'
            button.emoji = Emojis.resume_button
            await interaction.response.edit_message(view=self)
        elif not is_paused:
            button.label = 'Pause'
            button.emoji = Emojis.pause_button
            await interaction.response.edit_message(view=self)

    @discord.ui.button(label='Clear Queue', style=discord.ButtonStyle.red, emoji=Emojis.stop_button, custom_id='musicplayer_view:stop')
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        ctx = await self.bot.get_context(interaction.message)
        await MusicPlayerUtils.stop(ctx)
        