from tortoise.models import Model
from tortoise import fields

class Playsound(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()
    duration = fields.FloatField()
    uploader = fields.BigIntField()
    file_location = fields.TextField()
    played = fields.IntField()
    guild = fields.BigIntField()

    class Meta:
        table = 'playsound'