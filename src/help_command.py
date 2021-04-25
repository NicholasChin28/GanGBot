import discord
from discord.ext import commands
import help_messages as hm

# Custom help for bot
# Reference code: https://gist.github.com/InterStella0/b78488fb28cadf279dfd3164b9f0cf96#start
class HelpCommand(commands.MinimalHelpCommand):
    async def send_bot_help(self, mapping):
        await self.context.send("This is help")

    async def send_cog_help(self, cog):
        await self.context.send("This is help cog")

    async def send_command_help(self, command):
        # embed = discord.Embed(title=self.get_command_signature(command))
        print('Value of get_command_signature: ', self.get_command_signature(command))
        print('Value of command.help: ', command.help)
        # embed.add_field(name="Help", value=command.help)

        # Add code here
        await self.context.send("This is help command")

        '''
        embed = hm.Vote()

        channel = self.get_destination()
        await channel.send(embed=embed)
        '''

    async def send_pages(self):
        destination = self.get_destination()
        for page in self.paginator.pages:
            emby = discord.Embed(description=page)
            await destination.send(embed=emby)

    def get_command_signature(self, command):
        print('Value of qualified_name: ', command.qualified_name)
        return '{0.clean_prefix}{1.qualified_name}{1.signature}'.format(self, command)