# TODO: Use optional arguments for @property decorators: https://stackoverflow.com/questions/58433807/property-decorator-with-optional-argument
import time
from datetime import datetime
import pathlib
from aiohttp.client import request
import validators
import youtube_dl
from datetime import timedelta
from Models import ytdl_source

class MyLogger(object):
    def debug(self, msg):
        pass
    
    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)

class VideoTime:
    _time_formats = ['%S.%f', '%S', '%M:%S', '%H:%M:%S']

    def parse_time(self, time_str: str):
        for format in self._time_formats:
            try:
                valid_timestamp = datetime.strptime(time_str, format)
                return valid_timestamp
            except ValueError:
                pass
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
        return (self.hour * 3600 + self.minute * 60 + self.second) * 1000    

    def __str__(self):
        return self.datetime_str
        
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

class VideoRange:
    _start_time = None
    _end_time = None
    _supported_formats = ['%M:%S', '%H:%M:%S']

    @property
    def start_time(self):
        return self._start_time

    @property
    def end_time(self):
        return self._end_time

    @end_time.setter
    def end_time(self, time: str):
        self._end_time = validate_time(time)

    # Temp functions to return the timedelta of start_time and end_time
    def start_time_seconds(self):
        if self._start_time is not None:
            # return timedelta(hours=self._start_time.tm_hour, minutes=self._start_time.tm_min, seconds=self._start_time.tm_sec)
            return custom_convert_to_seconds(self._start_time)
        return None

    def end_time_seconds(self):
        if self._end_time is not None:
            # return timedelta(hours=self._end_time.tm_hour, minutes=self._end_time.tm_min, seconds=self._end_time.tm_sec)
            return custom_convert_to_seconds(self._end_time)
        return None

    def __init__(self, start_time=0, end_time=None) -> None:
        self._start_time = start_time
        self._end_time = end_time

    # Converts VideoRange start_time / end_time to seconds
    @classmethod
    async def parse_in_seconds(self, time_obj):
        return (time_obj)

# Converts VideoRange structtime to seconds
def custom_convert_to_seconds(time: time.struct_time):
    to_return = (time.tm_hour * 3600) + (time.tm_min * 60) + time.tm_sec
    return to_return

# Creates playsound in current folder
def create_playsound(url, name, timestamp):
    print(f'Values to receive: {url}\n{name}\n{timestamp}')

    ydl_opts = create_ytdl_options(name, timestamp)

    print(f'Value of ydl_opts: {ydl_opts}')

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        ydl.download([url])

    return True

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
    cogs_path = pathlib.Path(pathlib.Path.cwd() / 'cogs').glob('**/*')
    cogs = [x.stem for x in cogs_path if x.is_file() and x.suffix == '.py' and x.stem != 'custom_help']
    return cogs


# Gets a list of all cogs. Including custom_help cog
def get_all_cogs():
    cogs_path = pathlib.Path(pathlib.Path.cwd() / 'cogs').glob('**/*')
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
            raise Exception('Invalid time format')

# Parses timestamp input by user from music play command
# TODO: Throw error messages so that bot can display to user the error
def parse_time(timestamp):
    print('parse_time function called')
    time_ranges = timestamp.split('-')  # Split time range
    struct_time_range = []

    if len(time_ranges) == 1:   # Starting time range only
        print('condition 1')
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

def parse_time2(timestamp: str, url_duration: float):
    print('parse_time2 function called')
    time_ranges = timestamp.split('-')
    struct_time_range = []

    if len(time_ranges) > 2:
        raise Exception("Invalid timestamp format")

    try:
        for i in time_ranges:
            print('line 250')
            struct_time_range.append(VideoTime(i))
            print('line 252')
        if len(struct_time_range) == 1:     # User did not provide end time. So, use video end timestamp
            struct_time_range.append(VideoTime(url_duration))
            if not struct_time_range[-1].datetime > struct_time_range[0].datetime:
                raise Exception("Starting time greater than video length!")
        else:
            # User provided start and end time.  Make sure they are valid 
            user_video = VideoTime(str(round(url_duration, 1)))
            if not struct_time_range[-1].datetime > struct_time_range[0].datetime and not user_video.datetime >= struct_time_range[-1].datetime:
                raise Exception("Invalid timestamp")

        return struct_time_range
    except ValueError:
        raise Exception("Error ValueError from validate_time")
     
# Validates upload arguments from playsound cog upload command
def validate_upload_arguments(args):
    for i in args:
        if validators.url(i):
            pass

def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now converting ...')

# Extracts info from given youtube url
def extract_youtube_info(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        # 'outtmp1': '%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'external_downloader': 'ffmpeg',
        'external_downloader_args': [
            '-ss', '00:01:00.00', '-to', '00:01:50.00'
        ],
        'logger': MyLogger(),
        'progress_hooks': [my_hook],
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        # video_duration = info["duration"]

        return info
        # best_audio_format = max

# Check if timestamp is within url duration
def validate_time_range(url, time_range):
    info = youtube_dl.YoutubeDL().extract_info(url, download=False)
    request_time = parse_time(time_range)

    if request_time is not None:
        start_duration_seconds = request_time.start_time_seconds()
        end_duration_seconds = request_time.end_time_seconds()

    video_duration = info["duration"]   # Duration in seconds

# Calculate estimated size of cropped playsound source
def calc_filesize(duration: int) -> int:
    bitrate = 192       # 192 kilobit per second
    bit_to_byte = 8     # Number of bits in a byte
    """
    Calculation formula:
    bitrate * duration in seconds / 8 
    8 refers to number of bits in a bit
    Return value is in kilobyte
    """
    return bitrate * duration / bit_to_byte
