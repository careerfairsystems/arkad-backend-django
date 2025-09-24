# Create your models here.
from django.db import models


class PersonCounter(models.Model):
    """
    This is a transactional counter to keep track of the number of people in a room/building.

    It contains the room/building, the timestamp of the last update, and the current count.
    It also contains the delta, which is the change in count since the last update.
    0 means no change, positive means people entered, negative means people left.
    """
    room = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    count = models.IntegerField(default=0)
    delta = models.IntegerField(default=0)