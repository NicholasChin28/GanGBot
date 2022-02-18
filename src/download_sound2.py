# Testing code for external_downloader
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
    'outtmp1': '%(title)s.%(ext)s',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'external_downloader': 'ffmpeg',
    'external_downloader_args': [
        '-ss', '120', '-to', '140'
    ],
    'logger': MyLogger(),
    'progress_hooks': [my_hook],
}



with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    ydl.download(['https://www.youtube.com/watch?v=nEx3elskvJY'])



# ffmpeg -i performance.mp3 -ss 00:00:08 -to 00:00:19 -c copy performance_new.mp3

