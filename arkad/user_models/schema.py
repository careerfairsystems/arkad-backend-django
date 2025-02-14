from ninja import Schema, ModelSchema
from user_models.models import User


class SigninSchema(Schema):
    username: str
    password: str

class ProfileSchema(ModelSchema):
    class Meta:
        model = User
        fields = ('id',
                  'username',
                  'email',
                  'first_name',
                  'last_name',
                  'is_active',
                  'is_staff',
                  'is_superuser',)
