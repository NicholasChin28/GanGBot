import discord
from utils.playsound_utils import PlaysoundUtils
from discord.ext import commands

# Upload playsound input fields
class LinkField(discord.ui.TextInput):
    def __init__(self):
        super().__init__(
            label='Playsound link',
            style=discord.TextStyle.short,
            min_length=1, 
            placeholder='Only Youtube links supported', 
            custom_id='ps_link'
        )

class NameField(discord.ui.TextInput):
    def __init__(self):
        super().__init__(
            label='Playsound name', 
            style=discord.TextStyle.short, 
            min_length=1, 
            max_length=20,
            placeholder='Give a cool name for the playsound!', 
            custom_id='ps_name'
        )

class TimestampField(discord.ui.TextInput):
    def __init__(self):
        super().__init__(
            label='Playsound duration',
            style=discord.TextStyle.short,
            required=False,
            placeholder='Duration cannot be more than 20 seconds',
            custom_id='ps_duration'
        )

class PlaysoundInputModal(discord.ui.Modal):
    def __init__(self, bot: commands.Bot):
        super().__init__(title='Insert playsound')
        self.bot = bot
        self.add_item(LinkField())
        self.add_item(NameField())
        self.add_item(TimestampField())

    async def callback(self, interaction: discord.Interaction):
        # print(self['link'].value)
        print(self.children[0].value)

        link = self.children[0].value
        name = self.children[1].value
        timestamp = self.children[2].value
        ctx = await self.bot.get_context(interaction.message)
        user = interaction.user
        # print(modal['link'].value)
        # await interaction.response.send_message(f'Playsound link is: {interaction.message}')
        await interaction.response.send_message(f'Adding playsound')
        await PlaysoundUtils.addps(bot=self.bot, link=link, name=name, ctx=ctx, user=user, timestamp=timestamp)
