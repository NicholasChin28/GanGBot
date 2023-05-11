# Cog to store general commands for bot
import discord
from discord.ext import commands
from discord.utils import get
import random
import logging

# For vote
import asyncio
from async_timeout import timeout
import re
import emoji
import string

class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self) -> None:        
        logging.info("General cog loaded! from 2.0")

    async def cog_unload(self) -> None:        
        logging.info("General cog unloaded! from 2.0")

    @commands.command(name='choose')
    async def _choose(self, ctx: commands.Context, *, choose: str):
        """ Chooses a random item """
        options = [x.strip() for x in choose.split(',') if len(x.strip()) > 0]
        print('options: ', options)
        if len(options) < 2:
            return await ctx.send('Two or more choices should be given')

        return await ctx.send('Maldbot chose: ' + random.choice(options))

    # Voting feature using embeds and reactions
    @commands.command(name='vote')
    async def _vote(self, ctx: commands.Context, *args):
        """Vote for options. Use ?vote for more information"""
        votes = set()
        print('Prefix of command: ', ctx.prefix)
        print('Starting of args: ')
        # Help details for vote command
        # TODO: Refactor help command to be in another location
        if ctx.prefix == '?':
            return await ctx.send("""To use the vote command, refer to this example: 
.vote {title} [option] [option] (duration)\n  
title: Insert your title here 
option: List as many options you want. Number of options can be up to 20 
duration: How long the vote should last. Currently the duration allowed is between 30 seconds - 5 minutes
The duration must be in seconds (eg. 300 for 5 minutes)""")

        arg_string = ' '.join(args)

        # Emojis for embed
        option_emoji = [''.join((':regional_indicator_', x, ':')) for x in list(string.ascii_lowercase)]

        # Actual emojis for reaction
        option_emoji2 = [emoji.emojize(x, use_aliases=True) for x in option_emoji]

        # Finds the title
        title = re.findall("^{.*}", arg_string)

        # Finds the options
        options = re.findall(r'\[.*?\]', arg_string)

        # Finds the voting duration
        vote_time = re.findall(r"\(\d*?\)", arg_string)

        # Allow voting duration between 30 seconds - 5 minutes
        try:
            vote_time = int(vote_time[0][1:-1])
        except ValueError:
            await ctx.send('Vote time must be a number')
            return

        if vote_time < 30 or vote_time > 300:
            await ctx.send('Vote time must be between 30 seconds - 5 minutes')        
            return

        formatted_options = []
        for x, option in enumerate(options):
            formatted_options += '\n {} {}'.format(option_emoji2[x], option[1:-1])

        # Create embed from title and options
        embed = discord.Embed(title=title[0][1:-1], color=3553599, description=''.join(formatted_options))

        react_message = await ctx.send(embed=embed)

        # For tracking the voters
        voter = ctx.message.author
        if voter.id not in votes:
            votes.add(voter.id)

        for option in option_emoji2[:len(options)]:
            print('Value of options: ', option)
            await react_message.add_reaction(option)

        await react_message.edit(embed=embed)

        # Check for reaction
        def check(reaction, user):
            return not user.bot and reaction.message.id == react_message.id

        try:
            # async with timeout(int(vote_time[0][1:-1])):
            async with timeout(vote_time):
                while True:
                    try:
                        reaction, _ = await self.bot.wait_for('reaction_add', check=check)
                    except Exception:
                        await ctx.send('Normal exception occurred. Should not happen')
        except asyncio.TimeoutError:
            # Display results here
            the_list = await ctx.channel.fetch_message(react_message.id)
            await ctx.send('Voting ended. Calculating results...')

            vote_counts = [x.count - 1 for x in the_list.reactions]
            print('vote_counts: ', vote_counts)
            highest_count = max(vote_counts)    # Highest vote count

            if sum(vote_counts) == 0:
                pepehands = get(ctx.guild.emojis, name='Pepehands')
                await ctx.send(f'No votes casted.. {pepehands} no one voted')    
            elif vote_counts.count(highest_count) > 1:
                await ctx.send('More than one vote has the highest votes. No winner :(')
            else:
                await ctx.send(f'The winning vote is "{(options[vote_counts.index(highest_count)])[1:-1]}" with a vote count of {highest_count}!')

async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))