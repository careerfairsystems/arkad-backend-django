from arkad.customized_django_ninja import Schema


class UpdateFCMTokenSchema(Schema):
    fcm_token: str


class NotifyByTokenSchema(Schema):
    token: str
    title: str
    body: str
