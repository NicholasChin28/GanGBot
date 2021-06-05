# Cog to store commands for bot owner
import discord
from discord.ext import commands
from discord.utils import get
from discord.ext.commands.core import command
from helper import helper

class Owner(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Owner cog loaded!')

    @commands.command(name='load')
    @commands.is_owner()
    async def _load(self, ctx: commands.Context, extension):
        """Loads cog"""
        try:
            self.bot.load_extension(f'cogs.{extension}')
            await ctx.send(f"Loaded {extension} cog")
        except commands.ExtensionNotFound:
            await ctx.send("Extension not found")
        except commands.ExtensionAlreadyLoaded:
            await ctx.send("Extension already loaded")

    @commands.command(name='unload')
    @commands.is_owner()
    async def _unload(self, ctx: commands.Context, extension):
        """Unloads cog"""
        try:
            self.bot.unload_extension(f'cogs.{extension}')
            await ctx.send(f"Unloaded {extension} cog")
        except commands.ExtensionNotFound:
            await ctx.send("Extension not found")
        except commands.ExtensionNotLoaded:
            await ctx.send("Extension is not loaded")

    @commands.command(name='reload')
    @commands.is_owner()
    async def _reload(self, ctx: commands.Context, extension):
        '''Reloads cog'''
        try:
            self.bot.reload_extension(f'cogs.{extension}')
            await ctx.send(f'Reloaded {extension} cog')
        except commands.ExtensionNotFound:
            await ctx.send(f'Failed to reload {extension} cog')
        except commands.NoEntryPointError:
            await ctx.send(f'{extension} cog does not have a setup function')

    @commands.command(name='cogs')
    @commands.is_owner()
    async def _cogs(self, ctx: commands.Context):
        '''Display status and list of cogs'''
        # cogs = self.bot
        x_emoji = '❌'
        tick_emoji = '✅'
        all_cogs = helper.get_all_cogs()
        # print(f'\nValue of all loaded bot extensions: {self.bot.extensions}')

        # Print the list of all available cogs
        # print(f"All cogs: {helper.get_all_cogs()}")

        # Gets the list of all loaded bot extensions
        # print(f'\n Value of all keys in self.bot.extensions variable: {self.bot.extensions.keys()}\n')

        # Print bot extensions without the leading text "cogs."
        loaded_cogs = [i.replace("cogs.", "") for i in self.bot.extensions.keys()]
        # print(f'\n Value of loaded_cogs variable: {loaded_cogs}')

        # Prepare discord embed
        embed = discord.Embed(title='Cog status', description='List of all cogs and their status')
        embed.add_field(name='Cog', value='Loaded')

        embed_value_list = []
        embed_value_field = ''

        for x in all_cogs:
            if x in loaded_cogs:
                embed_value_list.append(f'\n{x}\t{tick_emoji}\n')
            else:
                embed_value_list.append(f'\n{x}\t{x_emoji}\n')

        embed_value_field = ''.join(embed_value_list)
        embed.add_field(name='Cogs', value=embed_value_field, inline=False)

        await ctx.send(embed=embed)

    # Error handling
    @_load.error
    @_unload.error
    # @_reload.error
    async def role_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Sorry, only the bot owner can use this command")


def setup(bot):
    bot.add_cog(Owner(bot))
