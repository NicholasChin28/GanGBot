from tortoise.models import Model
from tortoise import fields

class Playsound(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()
    duration = fields.FloatField()
    extension = fields.TextField(null=True)
    uploader = fields.BigIntField()
    played = fields.IntField()
    guild = fields.BigIntField()

    class Meta:
        table = 'playsound'