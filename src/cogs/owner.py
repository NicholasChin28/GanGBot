# Cog to store commands for bot owner
from discord.ext import commands

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

    # TODO: Reload extension
    """
    @commands.command(name='reload')
    @commands.is_owner()
    async def _reload(self, ctx: commands.Context, extension):
        '''Reloads cog'''
        await ctx.invoke(self.bot.get_command('unload'), query=extension)
        await ctx.invoke(self.bot.get_command('load'), query=extension)
        return await ctx.send(f"Reload {extension} cog")
    """

    # TODO: Display status and list of cogs
    """
    @commands.command(name='cogs')
    @commands.is_owner()
    async def _cogs(self, ctx: commands.Context):
        '''Display status and list of cogs'''
        cogs = get_cogs()
        await ctx.send(f'Value of all cogs:\n {cogs}')
        pass
    """

    # Error handling
    @_load.error
    @_unload.error
    # @_reload.error
    async def role_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Sorry, only the bot owner can use this command")


def setup(bot):
    bot.add_cog(Owner(bot))
