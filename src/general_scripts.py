from codecs import encode
from botocore.exceptions import ClientError
import psycopg2
from dotenv import load_dotenv
import os
import io
import asyncpg
import concurrent.futures
import time
import pathlib
import boto3
import botocore
import re
import json
import logging
from pydub import AudioSegment
from Models.aws_s3 import AwsS3
import asyncio
from youtube_dl import YoutubeDL
from aiohttp import ClientSession
import pydub
from mutagen.mp3 import MP3
import mutagen
from pyaml_env import parse_config
from tortoise import Tortoise, run_async
from src.Models.playsound import Playsound
from src.Models.role import Role

load_dotenv()

async def init():
    tortoise_config = parse_config('./tortoise-config.yaml')
    await Tortoise.init(config=tortoise_config)

    await Tortoise.generate_schemas()

    item = await Role.filter(id=3)
    print(item[0].guild)
    
    full_list = await Role.first()
    print(full_list.guild)

    # Insert value into playsound table
    """
    await Playsound.create(
        name='test',
        duration=18.000,
        uploader=12739182,
        played=0,
        guild=81823,
    )
    """

    playsounds = await Playsound.all()
    for ps in playsounds:
        print(ps.duration)


run_async(init())


