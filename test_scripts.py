'''
import discord
from mutagen.mp3 import MP3
from pathlib import Path

class Playsound():

    def __init__(self, filename: str):
        self.duration = self.parse_duration(int((MP3(filename).info.length)))
        self.name = filename.name.split('.mp3')[0]

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append(f'{days} days')
        if hours > 0:
            duration.append(f'{hours} hours')
        if minutes > 0:
            duration.append(f'{minutes} minutes')
        if seconds > 0:
            duration.append(f'{seconds} seconds')

        return ', '.join(duration)

p = Path('playsounds')
playsound_files = [x for x in p.glob('*.mp3')]
for i in playsound_files:
    
    
    playsound = Playsound(i)
    print('Filename: ', playsound.name)
    print('Duration: ', playsound.duration)
    

audio_file = MP3('./playsounds/test1.mp3')
print('Duration: ', int(audio_file.info.length))
'''

'''
import asyncio

# asyncio.get_running_loop()
async def myCoroutine():
    pass

loop = asyncio.get_event_loop()
loop2 = asyncio.get_event_loop()


# Test code 1
try:
    loop.run_forever()
finally:
    loop.close()
'''


'''
loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(myCoroutine())
finally:
    loop.close()
'''

''' Block
import asyncio

def hello_world(loop):
    """A callback to print 'Hello World' and stop the event loop"""
    print('Hello World')
    loop.stop()

def hello_world2(loop):
    """A callback to print 'Hello World' and stop the event loop"""
    print('Hello World version 2')
    # loop.stop()

loop = asyncio.get_event_loop()
# loop2 = asyncio.get_event_loop()
loop2 = asyncio.new_event_loop()

# Schedule a call to hello_world()
loop.call_soon(hello_world, loop)
loop2.call_soon(hello_world2, loop2)
loop2.call_at()

# Blocking call interrupted by loop.stop()
try:
    loop.run_forever()
    loop2.run_forever()
    print('End of try block')
    # loop2.stop()
    # loop2.call_soon(hello_world2, loop2)
    # loop2.run_forever()
finally:
    print('Start of finally block')
    loop2.close()
    loop.close()
    loop2.close()
    # loop2.close()
End block ''' 


'''
try:
    loop2.run_forever()
finally:
    loop2.close()
'''

  


