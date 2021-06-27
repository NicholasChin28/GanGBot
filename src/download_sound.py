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

"""
with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    # info = ydl.extract_info(["https://www.youtube.com/watch?v=n8X9_MgEdCg"])
    info = ydl.extract_info("https://www.youtube.com/watch?v=n8X9_MgEdCg", download=False)

    video_duration = info["duration"]
    best_audio_format_for_real = max([i["abr"] for i in info["formats"] if "audio only" in i["format"]])

    print(f'Value of best_audio_format_for_real: {best_audio_format_for_real}')

    print(f'Value of info: {(info["duration"])}')
    formats = info['formats']

    # the_best_audio_format = max([i[""]])

    audio_formats = [i for i in info["formats"] if "audio only" in i["format"]]

    print(f'Value of audio_formats: {audio_formats}')

    # TODO: Extract the filesize of best audio from audio_formats
    # best_audio_format = [i["abr"] for i in audio_formats]
    best_audio_format = max([i["abr"] for i in audio_formats])
    print(f'Value of best_audio_format: {best_audio_format}')

    # best_audio_format = ""

    # print(f'Value of audio_formats: {len(audio_formats)}')

    # print(f'audio_formats: {audio_formats}')
    
    format = formats[3]
    print('Filesize: ', format['filesize'])
    print('Bitrate: ', format["format"])
"""


with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    ydl.download(['https://www.youtube.com/watch?v=n8X9_MgEdCg'])



# ffmpeg -i performance.mp3 -ss 00:00:08 -to 00:00:19 -c copy performance_new.mp3

