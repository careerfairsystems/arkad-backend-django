# Create your models here.
from django.db import models, transaction


class RoomModel(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class PersonCounter(models.Model):
    """
    This is a transactional counter to keep track of the number of people in a room/building.

    It contains the room/building, the timestamp of the last update, and the current count.
    It also contains the delta, which is the change in count since the last update.
    0 means no change, positive means people entered, negative means people left.
    """
    room = models.ForeignKey(RoomModel, on_delete=models.CASCADE, related_name='counters')
    created_at = models.DateTimeField(auto_now_add=True)
    count = models.IntegerField(default=0)
    delta = models.IntegerField(default=0)

    @classmethod
    def get_last(cls, room_name: str) -> "PersonCounter":
        return cls.objects.filter(room__name=room_name).order_by('-created_at').first()

    @classmethod
    def add_delta(cls, room: RoomModel, delta: int) -> "PersonCounter":
        """
        Safely apply a delta for a given room.
        Creates a new PersonCounter row with updated count.
        """
        with transaction.atomic():
            last = cls.objects.select_for_update().filter(room=room).order_by('-created_at').first()
            new_count = (last.count if last else 0) + delta
            return cls.objects.create(room=room, count=new_count, delta=delta)

