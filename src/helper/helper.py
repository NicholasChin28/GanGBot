# TODO: Use optional arguments for @property decorators: https://stackoverflow.com/questions/58433807/property-decorator-with-optional-argument
import time
import pathlib
import validators
import youtube_dl

class MyLogger(object):
    def debug(self, msg):
        pass
    
    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)

class VideoRange:
    _start_time = None
    _end_time = None

    @property
    def start_time(self):
        return self._start_time

    @property
    def end_time(self):
        return self._end_time

    def __init__(self, start_time=0, end_time=None) -> None:
        self._start_time = start_time
        self._end_time = end_time


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
            pass

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
        # 'outtmpl': 'C:/Users/{username}/anaconda3/envs/GanGBot/themes/%(title)s.%(ext)s',
        # 'outtmp1': Path('/themes/%(title)s.%(ext)s').mkdir(parents=True, exist_ok=True),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'logger': MyLogger(),
        'progress_hooks': [my_hook],
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        # video_duration = info["duration"]

        return info
        # best_audio_format = max

# Validate commands using time range (eg. play and upload)
def validate_time_range(url, timerange):
    info = extract_youtube_info(url)
    video_duration = info["duration"]

    

# Calculate file size of Youtube playsound URL 
# TODO: Extract the filesize of bestaudio from -F argument of youtube-dl
