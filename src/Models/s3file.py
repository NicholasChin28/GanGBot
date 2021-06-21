# Represents a file from AWS S3 bucket
class S3File:
    def __init__(self, name, status) -> None:
        self._name = name
        self._status = status

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        self._status = status
