import discord

# Upload playsound input fields
class LinkField(discord.ui.TextInput):
    def __init__(self):
        super().__init__(
            label='Playsound link',
            style=discord.TextInputStyle.short,
            min_length=1, 
            max_length=10, 
            placeholder='Only Youtube links supported', 
            custom_id='ps_link'
        )

class NameField(discord.ui.TextInput):
    def __init__(self):
        super().__init__(
            label='Playsound name', 
            style=discord.TextInputStyle.short, 
            min_length=1, 
            max_length=20,
            placeholder='Give a cool name for the playsound!', 
            custom_id='ps_name'
        )

class DurationField(discord.ui.TextInput):
    def __init__(self):
        super().__init__(
            label='Playsound duration',
            style=discord.TextInputStyle.short,
            required=False,
            placeholder='Duration cannot be more than 20 seconds',
            custom_id='ps_duration'
        )

class PlaysoundInputModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title='Insert playsound')
        self.add_item(LinkField())
        self.add_item(NameField())
        self.add_item(DurationField())

    async def callback(self, interaction: discord.Interaction):
        # print(self['link'].value)
        print(self.children[0].value)
        # print(modal['link'].value)
        await interaction.response.send_message(f'Playsound link is: {interaction.message}')
