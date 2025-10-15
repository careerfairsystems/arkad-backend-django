from arkad.customized_django_ninja import Router
from user_models.models import AuthenticatedRequest, User
from notifications.schema import UpdateFCMTokenSchema


router = Router(tags=["Notifications"])


@router.post("fcm-token", response={200: str})
def update_fcm_token(request: AuthenticatedRequest, data: UpdateFCMTokenSchema):
    """
    Update the FCM token for the authenticated user.

    Also checks that no other user has the same token, and clears it if so. This is to avoid
    sending notifications to the wrong user if the token is reused for the same device.
    """
    User.objects.filter(fcm_token=data.fcm_token).exclude(id=request.user.id).update(
        fcm_token=None
    )
    request.user.fcm_token = data.fcm_token  # user
    request.user.save()
    return 200, "Updated fcm token"
