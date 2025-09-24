from typing import Optional

# Create your models here.
from django.db import models, transaction

from user_models.models import User


class RoomModel(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.name


class PersonCounter(models.Model):
    """
    Transactional counter to track number of people in a room/building.

    Each row is an immutable event snapshot: new count and applied delta.
    """

    room = models.ForeignKey(RoomModel, on_delete=models.CASCADE, related_name="counters")
    created_at = models.DateTimeField(auto_now_add=True)
    count = models.IntegerField(default=0)
    delta = models.IntegerField(default=0)

    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=False)

    @classmethod
    def get_last(cls, room_name: str) -> Optional["PersonCounter"]:
        return cls.objects.filter(room__name=room_name).order_by("-created_at", "-id").first()

    @classmethod
    def add_delta(cls, room: RoomModel, delta: int, updated_by: Optional[User] = None) -> "PersonCounter":
        """
        Safely apply a delta for a given room by creating a new snapshot row.
        Lock the RoomModel row to serialize concurrent updates, including the first insert.
        """
        with transaction.atomic():
            # Lock the room row to serialize all updates for this room
            locked_room: RoomModel = RoomModel.objects.select_for_update().get(pk=room.pk)
            last: Optional[PersonCounter] = (
                cls.objects.filter(room=locked_room).order_by("-created_at", "-id").first()
            )
            new_count: int = (last.count if last else 0) + delta
            return cls.objects.create(room=locked_room, count=new_count, delta=delta, updated_by=updated_by)

    @classmethod
    def reset_to_zero(cls, room: RoomModel, updated_by: Optional[User] = None) -> "PersonCounter":
        """
        Reset the counter to 0 using a single serialized transaction.
        Computes the necessary delta under the lock to avoid races.
        """
        with transaction.atomic():
            locked_room: RoomModel = RoomModel.objects.select_for_update().get(pk=room.pk)
            last: Optional[PersonCounter] = (
                cls.objects.filter(room=locked_room).order_by("-created_at", "-id").first()
            )
            current_count: int = last.count if last else 0
            if current_count == 0:
                # Still record a no-op reset for traceability
                return cls.objects.create(room=locked_room, count=0, delta=0, updated_by=updated_by)
            return cls.objects.create(room=locked_room, count=0, delta=-current_count, updated_by=updated_by)
