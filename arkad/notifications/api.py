from arkad.customized_django_ninja import Router
from user_models.models import AuthenticatedRequest
from notifications.schema import UpdateFCMTokenSchema, NotifyByTokenSchema
from notifications.fcm_helper import fcm


router = Router(tags=["Notifications"])


@router.post("fcm-token", response={200: str})
def update_fcm_token(request: AuthenticatedRequest, data: UpdateFCMTokenSchema):
    request.user.fcm_token = data.fcm_token  # user
    request.user.save()
    return 200, "Updated fcm token"


@router.post("notify", response={200: str})
def send_notification_to_token(
    request: AuthenticatedRequest, data: NotifyByTokenSchema
):
    "Sends the specified message (title and body) to specified token."
    if not request.user.is_superuser:
        return 403, "Insufficient permissions"

    fcm.send_to_user(token=data.token, title=data.title, body=data.body)
    return 200, "Notification sent"
