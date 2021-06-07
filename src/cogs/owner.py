# Cog to store commands for bot owner
import os
import discord
from discord.ext import commands
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
        x_emoji = '❌'
        tick_emoji = '✅'

        all_cogs = helper.get_all_cogs()
        # Remove leading text "cogs." from bot extensions
        loaded_cogs = [i.replace("cogs.", "") for i in self.bot.extensions.keys()]
        
        # Prepare discord embed
        embed = discord.Embed(title='__**Cog status**__', description='List of cogs and their status', color=discord.Color.blurple())

        cogs_status = []

        for x in all_cogs:
            if x in loaded_cogs:
                cogs_status.append(f'{tick_emoji}')
            else:
                cogs_status.append(f'{x_emoji}')

        embed.add_field(name='__Cogs__', value=f'{os.linesep.join(all_cogs)}', inline=True)
        embed.add_field(name='__Loaded__', value=f'{os.linesep.join(cogs_status)}', inline=True)

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
