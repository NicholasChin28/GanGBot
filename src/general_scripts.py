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
from tortoise import Tortoise, run_async
from yaml import parse
from Models.aws_s3 import AwsS3
import aiohttp
import aiofiles
import asyncio
from youtube_dl import YoutubeDL
from aiohttp import ClientSession
import pydub
from mutagen.mp3 import MP3
import mutagen
from pyaml_env import parse_config
from src.Models.playsound import Playsound

load_dotenv()

# TODO: Dynamically populate the tortoise config values from .env file
async def main():
    tortoise_config = parse_config('./tortoise-config.yaml')
    await Tortoise.init(config=tortoise_config)

    playsound = await Playsound.filter(id=1)

run_async(main())
    