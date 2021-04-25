from discord.ext import commands


# Cog for owner utilities
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
        self.bot.load_extension(f'cogs.{extension}')
        await ctx.send(f"Loaded {extension} cog")

    @commands.command(name='unload')
    @commands.is_owner()
    async def _unload(self, ctx: commands.Context, extension):
        """Unloads cog"""
        self.bot.unload_extension(f'cogs.{extension}')
        await ctx.send(f"Unloaded {extension} cog")

    # Error handling
    @_load.error
    async def load_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Sorry, only the bot owner can use this command")

    @_unload.error
    async def unload_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Sorry, only the bot owner can use this command")


def setup(bot):
    bot.add_cog(Owner(bot))
