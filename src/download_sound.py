import asyncio
import youtube_dl
from pathlib import Path
import concurrent.futures

# How to use postprocessor_args / external_downloader_args
# https://stackoverflow.com/questions/27473526/download-only-audio-from-youtube-video-using-youtube-dl-in-python-script

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
    # 'outtmpl': 'C:/Users/nicho/miniconda3/envs/GanGBot/themes/%(title)s.%(ext)s',
    # 'outtmp1': Path('/themes/%(title)s.%(ext)s').mkdir(parents=True, exist_ok=True),
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'external_downloader': 'ffmpeg',
    'external_downloader_args': [
        '-ss', '00:00:10.00', '-to', '00:00:16.00'
    ],
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
def cpu_bound2():
    ydl_opts2 = {
        'format': 'bestaudio/best',
        # 'outtmpl': 'C:/Users/nicho/miniconda3/envs/GanGBot/themes/%(title)s.%(ext)s',
        # 'outtmp1': Path('/themes/%(title)s.%(ext)s').mkdir(parents=True, exist_ok=True),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'logger': MyLogger(),
        'progress_hooks': [my_hook],
    }

    with youtube_dl.YoutubeDL(ydl_opts2) as ydl:
        info = ydl.extract_info("https://file-examples-com.github.io/uploads/2017/04/file_example_MP4_480_1_5MG.mp4", download=False)
        print(info)
        ydl.download(['https://file-examples-com.github.io/uploads/2017/04/file_example_MP4_480_1_5MG.mp4'])
    
    return True
        
    

async def main():
    loop = asyncio.get_running_loop()

    # result = await loop.run_in_executor(None, cpu_bound2)
    
    with concurrent.futures.ProcessPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, cpu_bound2)
        # await loop.run_in_executor(pool, cpu_bound2)
        # print(result)
    


with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    # info = ydl.extract_info("https://www.youtube.com/watch?v=c3L0fbtftRY", download=False)
    

    # ydl.download(['https://www.youtube.com/watch?v=LXvO_lQ_6KA'])
    # info = ydl.extract_info("https://cdn.discordapp.com/attachments/694753759091359825/864366367558074405/Thor_-_God_of_Thunder_Angry_Review_Video_Game-m8e39b1G93Q.mp3", download=False)
    ydl.download(['https://cdn.discordapp.com/attachments/694753759091359825/864366367558074405/Thor_-_God_of_Thunder_Angry_Review_Video_Game-m8e39b1G93Q.mp3'])
    # print(info)


"""
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    # loop.run_until_complete(run_length_test("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))
    loop.run_until_complete(main())
    loop.close()
"""


# ffmpeg -i performance.mp3 -ss 00:00:08 -to 00:00:19 -c copy performance_new.mp3

