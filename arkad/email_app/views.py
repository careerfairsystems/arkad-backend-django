# Create your views here.


from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

from email_app.utils import get_base_url


def test_reset(request):
    return render(
        request,
        "email_app/reset.html",
        {
            "reset_link": "https://example.com/reset",
            "name": "asdas",
            "base_url": get_base_url(request),
        },
    )


def test_sign_up(request):
    return render(
        request,
        "email_app/sign_up.html",
        {"digits": [1, 2, 3, 4, 5, 6], "base_url": get_base_url(request)},
    )


def test_generic_information(request):
    return render(
        request,
        "email_app/generic_information_email.html",
        {
            "name": "John Doe",
            "greeting": "Welcome to ARKAD!",
            "heading": "Your registration has been confirmed",
            "message": "Thank you for registering for the ARKAD Career Fair 2025. We are excited to have you join us!<br><br>The event will take place on <strong>November 11-12, 2025</strong> at Kårhuset in Lund.",
            "button_text": "View Event Details",
            "button_link": "https://www.arkadtlth.se",
            "note": "If you have any questions, please don't hesitate to contact us.",
            "base_url": get_base_url(request),
        },
    )


def test_event_closing_reminder(request):
    """Test view for event closing reminder email template"""
    return render(
        request,
        "email_app/event_closing_reminder.html",
        {
            "greeting": "Reminder!",
            "heading": "Registration closes tomorrow",
            "event_name": "Lunch Lecture on AI and Machine Learning",
            "company_name": "Google",
            "event_date": "2025-11-10",
            "location": "Kårhuset, Main Hall",
            "description": "A fascinating presentation on how AI is changing the future of software development.",
            "message": "Remember to cancel your spot if you can't attend! Registration closes on 2025-11-10 at 23:59.",
            "button_text": "Manage my booking",
            "button_link": "https://www.arkadtlth.se/events/1",
            "disclaimer": "",
            "base_url": get_base_url(request),
        },
    )


def test_event_reminder_tomorrow(request):
    """Test view for event tomorrow reminder email template"""
    return render(
        request,
        "email_app/event_reminder.html",
        {
            "greeting": "Reminder!",
            "heading": "You're registered for Company Visit which is tomorrow",
            "event_name": "Company Visit to SAAB's Facility",
            "company_name": "SAAB",
            "event_date": (timezone.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "event_time": "13:00",
            "location": "SAAB, Linköping",
            "description": "An exclusive tour of SAAB's research and development facility.",
            "message": "We look forward to seeing you!",
            "button_text": "View event details",
            "button_link": "https://www.arkadtlth.se/events/2",
            "disclaimer": "NOTE: Bring valid ID. Security check required upon arrival.",
            "base_url": get_base_url(request),
        },
    )


def test_event_reminder_one_hour(request):
    """Test view for event one hour reminder email template"""
    return render(
        request,
        "email_app/event_reminder.html",
        {
            "greeting": "Reminder!",
            "heading": "You're registered for Student Session which is in one hour",
            "event_name": "Student Session - Career Opportunities in Fintech",
            "company_name": "Klarna",
            "event_date": timezone.now().strftime("%Y-%m-%d"),
            "event_time": (timezone.now() + timedelta(hours=1)).strftime("%H:%M"),
            "location": "Kårhuset, Room 204",
            "description": "An interactive session about career opportunities and internships at Klarna.",
            "message": "We look forward to seeing you!",
            "button_text": "View event details",
            "button_link": "https://www.arkadtlth.se/events/3",
            "disclaimer": "",
            "base_url": get_base_url(request),
        },
    )


def test_event_selection_student_session(request):
    """Test view for student session selection email template"""
    return render(
        request,
        "email_app/event_selection.html",
        {
            "greeting": "Congratulations!",
            "heading": "You've been selected for Student Session",
            "event_name": "Student Session - Working Life at Spotify",
            "company_name": "Spotify",
            "event_date": (timezone.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "event_time": "15:00",
            "location": "Kårhuset, Room 305",
            "description": "Meet Spotify engineers and learn about what it's like to work at one of the world's leading music streaming companies.",
            "message": "We're happy to inform you that you've been selected for this event. Please confirm your attendance as soon as possible.",
            "button_text": "View event details",
            "button_link": "https://www.arkadtlth.se/events/4",
            "disclaimer": "",
            "base_url": get_base_url(request),
        },
    )


def test_event_selection_company_visit(request):
    """Test view for company visit selection email template"""
    return render(
        request,
        "email_app/event_selection.html",
        {
            "greeting": "Congratulations!",
            "heading": "You've been selected for Company Visit",
            "event_name": "Company Visit to FMV Headquarters",
            "company_name": "FMV",
            "event_date": (timezone.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
            "event_time": "10:00",
            "location": "FMV, Stockholm",
            "description": "An exclusive opportunity to visit the Swedish Defence Materiel Administration and learn about their operations.",
            "message": "We're happy to inform you that you've been selected for this event. Please confirm your attendance as soon as possible.",
            "button_text": "View event details",
            "button_link": "https://www.arkadtlth.se/events/5",
            "disclaimer": "NOTE: Swedish citizenship required. Bring valid ID. Security check required upon arrival.",
            "base_url": get_base_url(request),
        },
    )
