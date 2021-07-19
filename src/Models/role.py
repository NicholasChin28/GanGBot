from tortoise.models import Model
from tortoise import fields

class Role(Model):
    id = fields.IntField(pk=True)
    role_id = fields.BigIntField()
    guild = fields.BigIntField()
    playsound_permission = fields.BooleanField(default=True)

    class Meta:
        table = 'role'