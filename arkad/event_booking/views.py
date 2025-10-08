import os
import shutil
import zipfile
from datetime import timedelta
from io import BytesIO

import pytz
import qrcode
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .forms import CreateLunchEventForm
from .models import Event, Ticket
from user_models.models import User


@staff_member_required
def create_lunch_event_view(request: HttpRequest) -> HttpResponse:
    # Make sure user is superuser
    if not request.user.is_superuser:
        return HttpResponse("Unauthorized", status=401)
    if request.method == "POST":
        form = CreateLunchEventForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            time_start = form.cleaned_data["time_start"]
            duration = form.cleaned_data["duration"]
            amount = form.cleaned_data["amount"]

            start_time = time_start
            end_time = start_time + timedelta(minutes=duration)

            stockholm_tz = pytz.timezone("Europe/Stockholm")
            visible_time = stockholm_tz.localize(
                start_time.replace(year=2500, hour=21, minute=0, second=0, microsecond=0).replace(
                    tzinfo=None
                )
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

            user, created = User.objects.get_or_create(
                username=username, defaults={"email": f"{username}@fake-user.com"}
            )
            if created:
                user.set_unusable_password()
                user.save()

            tickets = []
            for _ in range(amount):
                ticket = Ticket.objects.create(user=user, event=event)
                tickets.append(ticket)

            dir_name = (
                f"{event.name.replace(' ', '_')}_{start_time.strftime('%Y%m%d_%H%M')}"
            )
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)

            ticket_chunks = [tickets[i : i + 12] for i in range(0, len(tickets), 12)]
            pdf_count = 0

            for chunk in ticket_chunks:
                pdf_count += 1
                pdf_path = os.path.join(dir_name, f"tickets_page_{pdf_count}.pdf")
                c = canvas.Canvas(pdf_path, pagesize=A4)
                width, height = A4

                positions = []
                for row in range(4):
                    for col in range(3):
                        positions.append((col * (width / 3), (3 - row) * (height / 4)))

                for i, ticket in enumerate(chunk):
                    x_offset, y_offset = positions[i]
                    cell_width = width / 3
                    cell_height = height / 4
                    c.setFont("Helvetica-Bold", 12)
                    c.drawString(
                        x_offset + 20, y_offset + cell_height - 30, "Lunch Ticket"
                    )
                    c.setFont("Helvetica", 10)
                    c.drawString(
                        x_offset + 20,
                        y_offset + cell_height - 50,
                        f"Start: {event.start_time.strftime('%Y-%m-%d %H:%M')}",
                    )
                    c.drawString(
                        x_offset + 20,
                        y_offset + cell_height - 70,
                        f"End: {event.end_time.strftime('%Y-%m-%d %H:%M')}",
                    )

                    qr_img = qrcode.make(str(ticket.uuid))
                    qr_path = os.path.join(dir_name, f"qr_{ticket.uuid}.png")
                    with open(qr_path, "wb") as f:
                        qr_img.save(f)

                    c.drawImage(
                        qr_path,
                        x_offset + 20,
                        y_offset + 20,
                        width=100,
                        height=100,
                    )
                    os.remove(qr_path)

                c.save()

            zip_buffer = BytesIO()
            with zipfile.ZipFile(
                zip_buffer, "a", zipfile.ZIP_DEFLATED, False
            ) as zip_file:
                for root, _, files in os.walk(dir_name):
                    for file in files:
                        zip_file.write(os.path.join(root, file), file)

            shutil.rmtree(dir_name)

            response = HttpResponse(
                zip_buffer.getvalue(), content_type="application/zip"
            )
            response["Content-Disposition"] = f'attachment; filename="{dir_name}.zip"'
            return response

    else:
        form = CreateLunchEventForm()

    return render(
        request,
        "admin/create_lunch_event.html",
        {"form": form, "title": "Create Lunch Event"},
    )
