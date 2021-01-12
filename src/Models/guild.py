from tortoise.models import Model
from tortoise import fields

class Guild(Model):
    message_id = fields.BigIntField(pk=True)
    channel_id = fields.BigIntField()
    completed = fields.BooleanField(default=False)
    time = fields.DatetimeField()
    message = fields.TextField()
    options = fields.JSONField()
    votes = fields.JSONField(null=True)

    class Meta:
        table = 'guild'