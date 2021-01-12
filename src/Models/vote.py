# Holds a vote object
# TODO: Link with db, so that long votes can be held
# TODO: Add a foreign key field for Guild
from tortoise.models import Model
from tortoise import fields

class Vote(Model):
    message_id = fields.BigIntField(pk=True)
    channel_id = fields.BigIntField()
    completed = fields.BooleanField(default=False)
    time = fields.DatetimeField()
    message = fields.TextField()
    options = fields.JSONField()
    votes = fields.JSONField(null=True)

    class Meta:
        table = 'vote'
        table_description = 'This table contains the votes casted'


