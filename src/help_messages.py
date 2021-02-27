# Custom embed for each command
import discord

def Vote():
    embed = (discord.Embed(title='Vote',
                                description='```css\nHow to use\n```',
                                color=discord.Color.blurple())
                .add_field(name='test', value='test value'))

    return embed