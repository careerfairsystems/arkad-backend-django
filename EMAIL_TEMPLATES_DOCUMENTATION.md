# Email Templates Documentation

This document describes the email notification system for ARKAD events.

## Overview

The email system includes the following email types:

### Email Functions (in `email_app/emails.py`)

1. **`send_event_closing_reminder_email()`**
   - **Purpose**: Remind users that event registration closes tomorrow
   - **When to use**: 1 day before registration closes
   - **Includes**: Event details, location, description, disclaimer support (for SAAB/FMV)

2. **`send_event_reminder_email()`**
   - **Purpose**: Remind users about upcoming events (tomorrow or in 1 hour)
   - **When to use**: 24 hours or 1 hour before event starts
   - **Parameters**: `hours_before` (24 for tomorrow, 1 for one hour)
   - **Includes**: Event details, location, description, disclaimer support

3. **`send_event_selection_email()`**
   - **Purpose**: Notify users they've been selected for Student Sessions or Company Visits
   - **When to use**: After selection process is complete
   - **Includes**: Event details, location, description, disclaimer support (for SAAB/FMV)

4. **`send_generic_information_email()`**
   - **Purpose**: Send general information emails
   - **Includes**: Customizable greeting, heading, message, button, and note

5. **`send_signup_code_email()`**
   - **Purpose**: Send 6-digit signup codes

## Email Templates

All templates are located in `email_app/templates/email_app/`:

1. **`event_closing_reminder.html`** - Registration closing soon
2. **`event_reminder.html`** - Event starting soon
3. **`event_selection.html`** - Selection notification
4. **`generic_information_email.html`** - Generic emails
5. **`base.html`** - Base template with ARKAD branding

## Test Views

Preview email templates in your browser at these URLs:

- `/email/test/event_closing_reminder` - Registration closing reminder
- `/email/test/event_reminder_tomorrow` - SAAB company visit (tomorrow) with security disclaimer
- `/email/test/event_reminder_one_hour` - Klarna student session (in one hour)
- `/email/test/event_selection_student_session` - Spotify student session selection
- `/email/test/event_selection_company_visit` - FMV company visit selection with citizenship disclaimer

## Usage Examples

### Send a closing reminder (registration closes tomorrow)
```python
from django.http import HttpRequest
from email_app.emails import send_event_closing_reminder_email
from datetime import datetime, timedelta
from django.utils import timezone

send_event_closing_reminder_email(
    request=request,
    email="student@student.lu.se",
    event_name="AI and Machine Learning Workshop",
    company_name="Google",
    event_type="Lunch Lecture",
    closes_at=timezone.now() + timedelta(days=1),
    event_description="Learn about the latest in AI technology",
    location="Kårhuset, Main Hall",
    button_link="https://arkadtlth.se/events/123",
    disclaimer="",  # Add disclaimers for SAAB/FMV
)
```

### Send an event reminder (tomorrow)
```python
send_event_reminder_email(
    request=request,
    email="student@student.lu.se",
    event_name="Company Visit to SAAB",
    company_name="SAAB",
    event_type="Company Visit",
    event_start=timezone.now() + timedelta(days=1),
    event_description="Tour of SAAB facilities",
    location="SAAB, Linköping",
    button_link="https://arkadtlth.se/events/456",
    disclaimer="NOTE: Bring valid ID. Security check required upon arrival.",
    hours_before=24,  # 24 for tomorrow, 1 for one hour
)
```

### Send an event reminder (one hour before)
```python
send_event_reminder_email(
    request=request,
    email="student@student.lu.se",
    event_name="Student Session with Klarna",
    company_name="Klarna",
    event_type="Student Session",
    event_start=timezone.now() + timedelta(hours=1),
    event_description="Career opportunities in Fintech",
    location="Kårhuset, Room 204",
    button_link="https://arkadtlth.se/events/456",
    disclaimer="",
    hours_before=1,  # 1 for one hour before
)
```

### Send a selection notification
```python
send_event_selection_email(
    request=request,
    email="student@student.lu.se",
    event_name="Student Session - Spotify Engineering",
    company_name="Spotify",
    event_type="Student Session",
    event_start=timezone.now() + timedelta(days=7),
    event_description="Meet Spotify engineers",
    location="Kårhuset, Room 305",
    button_link="https://arkadtlth.se/events/789",
    disclaimer="",
)
```

## Special Disclaimers

### SAAB Company Visits
**Disclaimer**: "NOTE: Bring valid ID. Security check required upon arrival."

### FMV Company Visits
**Disclaimer**: "NOTE: Swedish citizenship required. Bring valid ID. Security check required upon arrival."

## Features

- ✅ HTML and plain text versions
- ✅ Responsive email design
- ✅ Event details (location, date, time, description)
- ✅ Call-to-action buttons
- ✅ Special disclaimers for security-sensitive events
- ✅ ARKAD branding and social media links
- ✅ Browser preview views for testing

## Template Variables

All event email templates accept these variables:
- `greeting` - Main greeting text
- `heading` - Subheading
- `event_name` - Name of the event
- `company_name` - Company name
- `event_date` - Date in YYYY-MM-DD format
- `event_time` - Time in HH:MM format (for reminders/selections)
- `location` - Event location (optional)
- `description` - Event description HTML (optional)
- `message` - Additional message text
- `button_text` - CTA button text
- `button_link` - CTA button URL
- `disclaimer` - Warning/disclaimer text (optional)
- `base_url` - Base URL for assets

## Notes for Notifications

Based on your requirements, here are which events require **emails** vs just **notifications**:

### Email Notifications
- ✅ Registration closing reminder (closes tomorrow)
- ✅ Event tomorrow reminder
- ✅ Event one hour reminder
- ✅ Selection notification (student sessions/company visits)

### Notification Only (no email functions needed)
- Registration opened for lunch lectures
- Registration opened for company visits
- Registration opened for student sessions

These notification-only events can be handled by your notification system without sending emails.
