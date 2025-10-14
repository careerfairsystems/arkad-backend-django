from arkad.customized_django_ninja import Router
from user_models.models import AuthenticatedRequest
from notifications.schema import UpdateFCMTokenSchema


router = Router(tags=["Notifications"])


@router.post("fcm-token", response={200: str})
def update_fcm_token(request: AuthenticatedRequest, data: UpdateFCMTokenSchema):
    request.user.fcm_token = data.fcm_token  # user
    request.user.save()
    return 200, "Updated fcm token"
