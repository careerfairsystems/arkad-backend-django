import os
from datetime import datetime, timedelta

import pytz
import qrcode
from django.core.management.base import BaseCommand, CommandParser
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from event_booking.models import Event, Ticket
from user_models.models import User


class Command(BaseCommand):
    help = "Creates a lunch event and books tickets for it."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "username", type=str, help="The username of the user to book the event for."
        )
        parser.add_argument(
            "time_start",
            type=str,
            help="The start time of the event in YYYY-MM-DDTHH:MM format.",
        )
        parser.add_argument(
            "duration", type=int, help="The duration of the event in minutes."
        )
        parser.add_argument(
            "amount",
            type=int,
            help="The capacity of the event and the number of tickets to create.",
        )

    def handle(self, *args, **options) -> None:  # type: ignore[no-untyped-def]
        username = options["username"]
        time_start_str = options["time_start"]
        duration_minutes = options["duration"]
        amount = options["amount"]

        stockholm_tz = pytz.timezone("Europe/Stockholm")

        try:
            start_time_naive = datetime.fromisoformat(time_start_str)
            start_time = stockholm_tz.localize(start_time_naive)
        except ValueError:
            self.stdout.write(
                self.style.ERROR(
                    "Invalid time_start format. Please use YYYY-MM-DDTHH:MM."
                )
            )
            return

        end_time = start_time + timedelta(minutes=duration_minutes)
        # Visible time should be year 2100
        visible_time = stockholm_tz.localize(
            start_time.replace(
                year=2100, hour=21, minute=0, second=0, microsecond=0
            ).replace(tzinfo=None)
        )

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

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created event: '{event.name}' with capacity {amount}."
            )
        )

        # Create a directory for the ticket PDFs
        dir_name = (
            f"{event.name.replace(' ', '_')}_{start_time.strftime('%Y%m%d_%H%M')}"
        )
        os.makedirs(dir_name, exist_ok=True)

        try:
            user, created = User.objects.get_or_create(
                username=username, defaults={"email": f"{username}@fake-user.com"}
            )
            if created:
                user.set_unusable_password()
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"User '{username}' did not exist, so a new user was created."
                    )
                )

            tickets = []
            for _ in range(amount):
                ticket = Ticket.objects.create(user=user, event=event)
                tickets.append(ticket)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created {amount} tickets for {user.username} for event {event.name}."
                )
            )

            # Group tickets into chunks of 4
            ticket_chunks = [tickets[i : i + 4] for i in range(0, len(tickets), 4)]
            pdf_count = 0

            for chunk in ticket_chunks:
                pdf_count += 1
                pdf_path = os.path.join(dir_name, f"tickets_page_{pdf_count}.pdf")
                c = canvas.Canvas(pdf_path, pagesize=A4)
                width, height = A4

                positions = [
                    (0, height / 2),  # Top-left
                    (width / 2, height / 2),  # Top-right
                    (0, 0),  # Bottom-left
                    (width / 2, 0),  # Bottom-right
                ]

                for i, ticket in enumerate(chunk):
                    x_offset, y_offset = positions[i]

                    c.setFont("Helvetica-Bold", 16)
                    c.drawString(
                        x_offset + 50,
                        y_offset + height / 2 - 50,
                        "Lunch Ticket",
                    )

                    c.setFont("Helvetica", 12)
                    c.drawString(
                        x_offset + 50,
                        y_offset + height / 2 - 70,
                        f"Start: {event.start_time.strftime('%Y-%m-%d %H:%M')}",
                    )
                    c.drawString(
                        x_offset + 50,
                        y_offset + height / 2 - 90,
                        f"End: {event.end_time.strftime('%Y-%m-%d %H:%M')}",
                    )

                    qr_img = qrcode.make(str(ticket.uuid))
                    qr_path = os.path.join(dir_name, f"qr_{ticket.uuid}.png")
                    with open(qr_path, "wb") as f:
                        qr_img.save(f)

                    c.drawImage(
                        qr_path,
                        x_offset + 50,
                        y_offset + height / 2 - 250,
                        width=150,
                        height=150,
                    )
                    os.remove(qr_path)

                c.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created {len(tickets)} tickets in {pdf_count} PDF files in '{dir_name}'."
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
            # Rollback event creation on other errors
            event.delete()
            self.stdout.write(
                self.style.WARNING(f"Event '{event.name}' has been rolled back.")
            )
