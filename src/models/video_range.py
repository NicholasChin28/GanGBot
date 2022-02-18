import time

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
        self._end_time = self.validate_time(time)

    def validate_time(timestamp):
        time_formats = ['%M:%S', '%H:%M:%S']
        for format in time_formats:
            try:
                valid_timestamp = time.strptime(timestamp, format)
                return valid_timestamp
            except ValueError:
                return None

    # Converts VideoRange structtime to seconds
    def custom_convert_to_seconds(time: time.struct_time):
        to_return = (time.tm_hour * 3600) + (time.tm_min * 60) + time.tm_sec
        return to_return

    # Temp functions to return the timedelta of start_time and end_time
    def start_time_seconds(self):
        if self._start_time is not None:
            # return timedelta(hours=self._start_time.tm_hour, minutes=self._start_time.tm_min, seconds=self._start_time.tm_sec)
            return self.custom_convert_to_seconds(self._start_time)
        return None

    def end_time_seconds(self):
        if self._end_time is not None:
            # return timedelta(hours=self._end_time.tm_hour, minutes=self._end_time.tm_min, seconds=self._end_time.tm_sec)
            return self.custom_convert_to_seconds(self._end_time)
        return None

    def __init__(self, start_time=0, end_time=None) -> None:
        self._start_time = start_time
        self._end_time = end_time

    # Converts VideoRange start_time / end_time to seconds
    @classmethod
    async def parse_in_seconds(self, time_obj):
        return (time_obj)