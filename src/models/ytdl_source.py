import yt_dlp
import asyncio
import functools

class YTDLError(Exception):
    pass

# Youtube-dl class
class YTDLSource():
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmp1': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': f'-vn -re',
    }

    ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, data: dict):
        # super().__init__(source, volume)

        # self.requester = ctx.author
        # self.channel = ctx.channel
        self.data = data

        self.id = data.get('id')
        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_id')        # May not exist anymore. Changed from 'uploader_url' to 'uploader_id' Check youtube-dl docs.
        date = data.get('upload_date')
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')              # May not exist anymore.
        self.description = data.get('description')  
        # self.duration = self.parse_duration(int(data.get('duration')))
        self.duration = int(data.get('duration'))
        self.tags = data.get('tags')
        self.url = data.get('url')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')
        self.dislikes = data.get('dislike_count')
        self.stream_url = data.get('url')

    def __str__(self):
        return '**{0.title}** by **{0.uploader}**'.format(self)

    @classmethod
    async def create_source(cls, search: str, timestamp: int = 0, *, loop: asyncio.BaseEventLoop = None):
        print('create_source function called')
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(cls.ytdl.extract_info, search, download=False, process=False)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError("Couldn't find anything that matches `{}`".format(search))

        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError("Couldn't find anything that matches `{}`".format(search))

        webpage_url = process_info['webpage_url']

        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError("Couldn't fetch `{}`".format(webpage_url))

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError("Couldn't retrieve any matches for `{}`".format(webpage_url))

        # Duration of the video
        # print(f'Total duration of the video: {info.get("duration")}')
        
        # Set the value of FFMPEG_OPTIONS options
        if not isinstance(timestamp, int):  # Means that timestamp is a VideoRange class
            if timestamp.end_time is not None:
                cls.FFMPEG_OPTIONS['options'] = (f'-vn -ss {timestamp.start_time.tm_hour}:{timestamp.start_time.tm_min}:{timestamp.start_time.tm_sec}'
                                                f' -to {timestamp.end_time.tm_hour}:{timestamp.end_time.tm_min}:{timestamp.end_time.tm_sec}')
            else:
                # Debug here
                print(f'Value of start hour: {timestamp.start_time.tm_hour}')
                print(f'Value of start minute: {timestamp.start_time.tm_min}')
                print(f'Value of start second: {timestamp.start_time.tm_sec}')
                cls.FFMPEG_OPTIONS['options'] = f'-vn -ss {timestamp.start_time.tm_hour}:{timestamp.start_time.tm_min}:{timestamp.start_time.tm_sec}'
        else:
            cls.FFMPEG_OPTIONS['options'] = f'-vn'

        print('Finish setting up options attribute for FFMPEG_OPTIONS')
        

        # Refer to: https://stackoverflow.com/questions/62354887/is-it-possible-to-seek-through-streamed-youtube-audio-with-discord-py-play-from
        return cls(data=info)

        # TODO: Try saving the ffmpeg seeked source to local file, then play from it, instead of 
        # TODO: Search in discord.py Discord group, "audio seek"
        # return cls(ctx, discord.FFmpegPCMAudio("./testing.mp3"), data=info)

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append('{} days'.format(days))
        if hours > 0:
            duration.append('{} hours'.format(hours))
        if minutes > 0:
            duration.append('{} minutes'.format(minutes))
        if seconds > 0:
            duration.append('{} seconds'.format(seconds))

        return ', '.join(duration)
