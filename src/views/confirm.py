from socket import timeout
import discord

class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.value = None

    @discord.ui.button(label='Approve', style=discord.ButtonStyle.green)
    async def approve(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message('Confirming', ephemeral=True)
        self.value = True
        self.stop()

    @discord.ui.button(label='Reject', style=discord.ButtonStyle.red)
    async def reject(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message('Rejecting', ephemeral=True)
        self.value = False
        self.stop()
