from arkad.customized_django_ninja import Schema


class NotificationTokenSchema(Schema):
    fcm_token: str
