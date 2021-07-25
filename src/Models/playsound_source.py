import asyncio
import discord
from discord.ext import commands
import validators


class PlaysoundSource(discord.PCMVolumeTransformer):
    def __init__(self, ctx: commands.Context, *, data: dict):
        pass

    @classmethod
    async def create_source(cls, url: str, timestamp: str, requester: discord.Member, guild: discord.Guild):
        loop = asyncio.get_event_loop()

        if not validators.url(url):
            raise Exception("Invalid url")

        