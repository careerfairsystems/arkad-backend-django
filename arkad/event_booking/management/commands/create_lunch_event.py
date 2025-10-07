from datetime import datetime, time, timedelta

import pytz
from django.core.management.base import BaseCommand, CommandParser
from event_booking.models import Event, Ticket
from user_models.models import User


class Command(BaseCommand):
    help = "Creates a lunch event and books tickets for it."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("username", type=str, help="The username of the user to book the event for.")
        parser.add_argument(
            "time_start",
            type=str,
            help="The start time of the event in YYYY-MM-DDTHH:MM format.",
        )
        parser.add_argument("duration", type=int, help="The duration of the event in minutes.")
        parser.add_argument("amount", type=int, help="The capacity of the event and the number of tickets to create.")

    def handle(self, *args, **options) -> None:
        username = options["username"]
        time_start_str = options["time_start"]
        duration_minutes = options["duration"]
        amount = options["amount"]

        stockholm_tz = pytz.timezone("Europe/Stockholm")

        try:
            start_time_naive = datetime.fromisoformat(time_start_str)
            start_time = stockholm_tz.localize(start_time_naive)
        except ValueError:
            self.stdout.write(self.style.ERROR("Invalid time_start format. Please use YYYY-MM-DDTHH:MM."))
            return

        end_time = start_time + timedelta(minutes=duration_minutes)
        visible_time = stockholm_tz.localize(datetime.combine(start_time.date(), time(21, 0)))

        event = Event.objects.create(
            name="Automatic LunchEvent",
            type="lu",
            start_time=start_time,
            end_time=end_time,
            visible_time=visible_time,
            capacity=amount,
            location="Restaurant",
        )
        event.name = f"Automatic LunchEvent {event.id}"
        event.save()

        self.stdout.write(self.style.SUCCESS(f"Successfully created event: '{event.name}' with capacity {amount}."))

        try:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': f'{username}@fake-user.com'}
            )
            if created:
                user.set_unusable_password()
                user.save()
                self.stdout.write(self.style.SUCCESS(f"User '{username}' did not exist, so a new user was created."))

            for _ in range(amount):
                Ticket.objects.create(user=user, event=event)

            self.stdout.write(self.style.SUCCESS(f"Successfully created {amount} tickets for {user.username} for event {event.name}."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
            # Rollback event creation on other errors
            event.delete()
            self.stdout.write(self.style.WARNING(f"Event '{event.name}' has been rolled back."))
