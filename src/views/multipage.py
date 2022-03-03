from socket import timeout
import typing
import discord

class PreviousButton(discord.ui.Button):
    def __init__(self, disabled: typing.Optional[bool] = True):
        super().__init__(
            label='Previous',
            disabled=disabled,
            style=discord.ButtonStyle.red,
            custom_id='mp:previous'
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.page -= 1
        # Enable NextButton
        self.view.children[1].disabled = False

        if self.view.page == 1:
            self.disabled = True

        embed = discord.Embed(description=f'**{self.view.count} sounds:**\n\n{self.view.embeds[self.view.page - 1]}')
        embed.set_footer(text=f'Viewing page {self.view.page}/{len(self.view.embeds)}')

        await interaction.response.edit_message(embed=embed, view=self.view)

class NextButton(discord.ui.Button):
    def __init__(self, disabled: typing.Optional[bool] = True):
        super().__init__(
            label='Next',
            disabled=disabled,
            style=discord.ButtonStyle.green,
            custom_id='mp:next'
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.page += 1
        # Enable PreviousButton
        self.view.children[0].disabled = False

        if self.view.page == len(self.view.embeds):
            self.disabled = True

        embed = discord.Embed(description=f'**{self.view.count} sounds:**\n\n{self.view.embeds[self.view.page - 1]}')
        embed.set_footer(text=f'Viewing page {self.view.page}/{len(self.view.embeds)}')

        # await interaction.response.edit_message(embed=self.view.embeds[to_display], view=self.view)
        await interaction.response.edit_message(embed=embed, view=self.view)

class MultiPage(discord.ui.View):
    def __init__(self, message: discord.Message, embeds: typing.List[str], count: int):
        super().__init__(timeout=50)
        self.message = message
        self.embeds = embeds
        self.count = count
        self.page = 1

        self.add_item(PreviousButton())
        if len(embeds) > self.page:
            self.add_item(NextButton(disabled=False))
        else:
            self.add_item(NextButton())
