from django.contrib import admin

from event_booking.models import Event, Ticket

admin.site.register(Event)
admin.site.register(Ticket)
