import youtube_dl
from pathlib import Path

class MyLogger(object):
    def debug(self, msg):
        pass
    
    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)

def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now converting ...')

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
    ydl.download(['https://www.youtube.com/watch?v=gbdXz53sV3w'])

# ffmpeg -i performance.mp3 -ss 00:00:08 -to 00:00:19 -c copy performance_new.mp3

