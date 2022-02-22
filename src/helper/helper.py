# TODO: Use optional arguments for @property decorators: https://stackoverflow.com/questions/58433807/property-decorator-with-optional-argument
import asyncio
import time
from datetime import datetime, timedelta
from pathlib import Path
from pydub import AudioSegment
from typing import Dict, List
import typing
from aiohttp.client import request
import validators
import mutagen
import youtube_dl
from models import ytdl_source
from models.video_range import VideoRange
from humanfriendly import parse_size
from youtube_dl.postprocessor.common import PostProcessor

class MyLogger(object):
    def debug(self, msg):
        pass
    
    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)

# Gets the filename of downloaded youtube_dl file
# Inspiration code: https://stackoverflow.com/questions/64759263/how-to-get-filename-of-file-downloaded-with-youtube-dl
class FilenameCollectorPP(PostProcessor):
    def __init__(self):
        super(FilenameCollectorPP, self).__init__(None)
        self.filenames = []

    def run(self, information):
        self.filenames.append(information['filepath'])
        return [], information

# TODO: Rewrite VideoTime class
class VideoTimeNew:
    def parse_time(self, time_str: str):
        TIME_FORMATS = ['%S.%f', '%S', '%M:%S.%f', '%M:%S', '%H:%M:%S', '%H:%M:%S.%f']
        for format in TIME_FORMATS:
            try:
                valid_timestamp = datetime.strptime(time_str, format)
                return valid_timestamp
            except ValueError:
                pass
        return None

    def __init__(self, time: str):
        parsed_time = self.parse_time(time)

class PlaysoundSourceNew:
    def __init__(self, start_time: str, end_time: str):
        self.start_time = start_time
        self.end_time = end_time
        self.duration = end_time - start_time

class PlaysoundLocal:
    def __init__(self, filename: str, duration: int):
        self.filename = filename
        self.duration = duration

    @classmethod
    def fix_file(cls, filename: str):
        return cls('test', 20)

class VideoTime:
    _time_formats = ['%S.%f', '%S', '%M:%S.%f', '%M:%S', '%H:%M:%S', '%H:%M:%S.%f']

    def parse_time(self, time_str: str):
        print(f'Value of time_str: {time_str}')
        for format in self._time_formats:
            try:
                print(f'Value of format: {format}')
                valid_timestamp = datetime.strptime(time_str, format)
                return valid_timestamp
            except ValueError:
                pass
        
        print('No valid time formats found, should raise Exception next')
        raise Exception("No valid time formats found")

    def __init__(self, time: str):
        parsed_time = self.parse_time(time)
        self.second = parsed_time.second
        self.minute = parsed_time.minute
        self.hour = parsed_time.hour
        self.microsecond = parsed_time.microsecond
        self.datetime = parsed_time
        self.datetime_str = time

    # Convert datetime to microsecond 
    def to_ms(self):
        return (self.hour * 3600 + self.minute * 60 + self.second) * 1000 + (self.microsecond / 1000)

    def __str__(self):
        return self.datetime_str

    # Get duration in seconds
    def get_duration(self):
        return (self.hour * 3600 + self.minute * 60 + self.second)
        
class FileRange:
    def __init__(self, data: dict):
        self.start_time = data.get('start_time')
        self.end_time = data.get('end_time')
        self.duration = data.get('end_time').parsed_time - data.get('start_time').parsed_time

    @classmethod
    def parse_time(cls, timestamp: str, url_duration: str):
        print('FileRange.parse_time called')
        time_ranges = timestamp.split('-')
        struct_time_range = []

        if len(time_ranges) > 2:
            raise Exception("Invalid timestamp format")

        try:
            for i in time_ranges:
                struct_time_range.append(VideoTime(i))
            if len(struct_time_range) == 1:     # User did not provide end time. So, use video end timestamp
                struct_time_range.append(VideoTime(url_duration))
                if not struct_time_range[-1].datetime > struct_time_range[0].datetime:
                    raise Exception("Starting time greater than video length!")
            else:
                # User provided start and end time.  Make sure they are valid 
                user_video = VideoTime(url_duration)
                if not struct_time_range[-1].datetime > struct_time_range[0].datetime and not user_video.datetime >= struct_time_range[-1].datetime:
                    raise Exception("Invalid timestamp")

            # Dictionary to return
            data = {
                "start_time": struct_time_range[0],
                "end_time": struct_time_range[1]
            }

            return struct_time_range
        except ValueError:
            raise Exception("Error ValueError from validate_time")

# Creates playsound in current folder
def create_playsound(url, name, timestamp):
    print(f'Values to receive: {url}\n{name}\n{timestamp}')

    ydl_opts = create_ytdl_options(name, timestamp)

    print(f'Value of ydl_opts: {ydl_opts}')

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        ydl.download([url])

    return True

# Extracts duration from Youtube link
def extract_duration(link: str):
    try:
        with youtube_dl.YoutubeDL() as ydl:
            info = ydl.extract_info(link, download=False)
            return info['duration']
    except Exception as e:
        print(e)
        raise Exception("Youtubedl encountered an unexpected error")

# Constructs the youtube_dl options
def create_ytdl_options(filename: str, timestamp: VideoRange):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'external_downloader': 'ffmpeg',
        'external_downloader_args': [],
        'logger': MyLogger(),
        'progress_hooks': [my_hook],
    }
    
    if timestamp.end_time == None:
        ydl_opts['external_downloader_args'].extend(['-ss', f"{timestamp.start_time.tm_hour}:{timestamp.start_time.tm_min}:{timestamp.start_time.tm_sec}"])
    else:
        ydl_opts['external_downloader_args'].extend(
            ['-ss', f"{timestamp.start_time.tm_hour}:{timestamp.start_time.tm_min}:{timestamp.start_time.tm_sec}",
             '-to', f"{timestamp.end_time.tm_hour}:{timestamp.end_time.tm_min}:{timestamp.end_time.tm_sec}"]
        )

    """
    if len(timestamp) == 1:
        ydl_opts['external_downloader_args'].extend(["-ss", f"{timestamp[0]}"])
    else:
        ydl_opts['external_downloader_args'].extend(["-ss", f"{timestamp[0]}", "-to", f"{timestamp[1]}"])
    """

    return ydl_opts


# Validates start time and end time is within Youtube source duration
def validate_range(video_range: VideoRange, ytdl_source: ytdl_source.YTDLSource):
    if video_range.start_time_seconds() > ytdl_source.duration:
        raise Exception("Starting time is greater than video duration")
    
    if video_range.end_time is not None:
        if video_range.end_time_seconds() > ytdl_source.duration:
            raise Exception("End time is greater than video duration")

# Gets all initial cogs to be loaded
# Excludes custom_help cog
def get_cogs():
    cogs_path = Path(Path.cwd() / 'cogs').glob('**/*')
    cogs = [x.stem for x in cogs_path if x.is_file() and x.suffix == '.py' and x.stem != 'custom_help']
    return cogs


# Gets a list of all cogs. Including custom_help cog
def get_all_cogs():
    cogs_path = Path(Path.cwd() / 'cogs').glob('**/*')
    cogs = [x.stem for x in cogs_path if x.is_file() and x.suffix == '.py']
    return cogs

# Checks if string is a valid time format
# Returns None if timestamp is not a valid time format
def validate_time(timestamp):
    time_formats = ['%M:%S', '%H:%M:%S']
    for format in time_formats:
        try:
            valid_timestamp = time.strptime(timestamp, format)
            return valid_timestamp
        except ValueError:
            return None

# Parses timestamp input by user from music play command
# TODO: Throw error messages so that bot can display to user the error
def parse_time(timestamp):
    print('parse_time function called')
    time_ranges = timestamp.split('-')  # Split time range
    struct_time_range = []

    if len(time_ranges) == 1:   # Starting time range only
        print('condition 1')
        print(f'Value of time_ranges: {time_ranges}')
        for i in time_ranges:
            if validate_time(i) is not None:
                # struct_time_range.append(validate_time(i))
                return VideoRange(start_time=validate_time(i))
        
        # return VideoRange(start_time=struct_time_range[0])
    elif len(time_ranges) == 2:
        print('condition 2')
        for i in time_ranges:
            if validate_time(i) is not None:
                struct_time_range.append(validate_time(i))

        if len(struct_time_range) != 2: # One of the range format is invalid
            # return VideoRange()
            return None
            
        # Compare the first and second time ranges
        # The second range which is the end time must be greater than the first range
        if not struct_time_range[-1] > struct_time_range[0]:    # End time is before the start time
            # return VideoRange() 
            return None

        return VideoRange(start_time=struct_time_range[0], end_time=struct_time_range[-1])

    return None

def get_seconds(time_string: str):
    time_formats = ['%S.%f', '%S', '%M:%S.%f', '%M:%S', '%H:%M:%S', '%H:%M:%S.%f']

    for format in time_formats:
        try:
            dt_object = datetime.strptime(time_string, format)
            return dt_object.hour * 3600 + dt_object.minute * 60 + dt_object.second
        except ValueError:
            pass
    """
    try:
        for format in time_formats:
            return datetime.strptime(time_string, format)
    except ValueError:
        pass
    """
    

    # None could mean either error or it was not found?
    return None

def parse_time_new(timestamp: str, duration: int):
    time_range = timestamp.split('-')

    end_time = None

    # Try to convert based on time_format
    if len(time_range) > 2:
        raise Exception('Invalid timestamp format')

    start_time = get_seconds(time_range[0])
    if len(time_range) == 2:
        end_time = get_seconds(time_range[1])
    else:
        end_time = duration

    # TODO: Check to make sure that start_time is not greater than duration and less than end time
    # Vice versa as well

    if start_time is None:
        raise Exception('Invalid start time')
    if end_time is None:
        raise Exception('Invalid end time')

    if (end_time - start_time <= 20) is not True:
        raise Exception('Playsound cannot be longer than 20 seconds')

    return PlaysoundSourceNew(start_time=start_time, end_time=end_time)

def parse_time2(timestamp: str, url_duration: float) -> List[VideoTime]:
# def parse_time2(duration: float, timestamp: typing.Optional[str] = None) -> List[VideoTime]:
    time_ranges = timestamp.split('-')
    struct_time_range = []

    if len(time_ranges) > 2:
        raise Exception("Invalid timestamp format")

    try:
        for i in time_ranges:
            struct_time_range.append(VideoTime(i))
        if len(struct_time_range) == 1:     # User did not provide end time. So, use video end timestamp
            struct_time_range.append(VideoTime(url_duration))
            if not struct_time_range[-1].datetime > struct_time_range[0].datetime:
                raise Exception("Starting time greater than video length!")
        else:
            conv_duration = str(timedelta(seconds=round(url_duration, 1)))  
            user_video = VideoTime(conv_duration)

            if not struct_time_range[-1].datetime > struct_time_range[0].datetime and not user_video.datetime >= struct_time_range[-1].datetime:
                raise Exception("Invalid timestamp")

        return struct_time_range
    except ValueError:
        raise Exception("Error ValueError from validate_time")
    except Exception as e:
        print('re-raising exception from VideoTime.parse_time')
        raise e
     

def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now converting ...')

def download_playsound_new(url, start_time: int = None, end_time: int = None, duration: int = None):
    ytdl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': './%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'external_downloader': 'ffmpeg',
        'external_downloader_args': [],
        'logger': MyLogger(),
        'progress_hooks': [my_hook],
    }

    if start_time is not None:
        ytdl_opts['external_downloader_args'].extend(['-ss', str(start_time)])
    if end_time is not None:
        ytdl_opts['external_downloader_args'].extend(['-to', str(end_time)])

    try:
        with youtube_dl.YoutubeDL(ytdl_opts) as ydl:
            filename_collector = FilenameCollectorPP()
            ydl.add_post_processor(filename_collector)

            ydl.download([url])
            filename = filename_collector.filenames[0]

            downloaded_file = mutagen.File(Path(filename))
            # Set title
            downloaded_file.info.title = filename
            downloaded_file.save()

            if int(downloaded_file.info.length) > duration:
                # Crop the playsound to correct duration
                segment = AudioSegment.from_mp3(filename)
                start = (int(downloaded_file.info.length) - duration) * 1000
                segment[start:].export(Path(filename), format='mp3')
            
            data = {
                'download_result': True,
                'filename': filename,
            }
    except Exception as e:
        data = {
            'download_result': False,
            'filename': None,
            'error': e,
        }

    return data

# Downloads playsound
def download_playsound(url, start_time, end_time) -> Dict:
    print('From download_playsound')
    print(f'start_time datetime_str: {start_time.datetime_str}')
    print(f'end_time datetime_str: {end_time.datetime_str}')

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': './%(title)s_playsound.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'external_downloader': 'ffmpeg',
        'external_downloader_args': [
            '-ss', start_time.datetime_str, '-to', end_time.datetime_str
        ],
        'logger': MyLogger(),
        'progress_hooks': [my_hook],
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            filename_collector = FilenameCollectorPP()
            ydl.add_post_processor(filename_collector)

            ydl.download([url])
            
            data = {
                "download_result": True,
                "filename": filename_collector.filenames[0],
            }

            return data
    except Exception as e:
        data = {
            "download_result": False,
            "filename": None,
        }

        return data
        
# Check if created playsound size is valid
def valid_filesize(duration: int) -> bool:
    max_size = '500KB'
    bitrate = 192       # 192 kilobit per second
    bit_to_byte = 8     # Number of bits in a byte
    """
    Calculation formula:
    bitrate * duration in seconds / 8 
    8 refers to number of bits in a bit
    Return value is in kilobyte
    """
    playsound_size = bitrate * duration / bit_to_byte
    if parse_size(f'{playsound_size}KB') > parse_size(max_size):
        return False
    
    return True
