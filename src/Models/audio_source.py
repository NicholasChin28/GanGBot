from aiohttp import ClientSession

# Audio source from URL
class AudioSource():
    def __init__(self, *, data: dict):
        pass

    @classmethod
    async def create_source(cls, url: str):
        async with ClientSession() as session:
            async with session.get(url) as response:
                if not response.status == 200:
                    raise Exception('Invalid url')

                content_type = response.headers['content-type']
                if not content_type.startswith('audio/'):
                    raise Exception('Only audio files supported')

                