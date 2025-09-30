import datetime

import pytz

# DEFAULT DATES
timezone_name: str = "Europe/Stockholm"
SWEDEN_TIMEZONE = pytz.timezone(timezone_name)

# All Student Sessions Booking Opens (13 oktober 00.00)
NAIVE_STUDENT_SESSIONS_OPEN = datetime.datetime(2025, 10, 13, 0, 0, 0)
student_sessions_open_sweden_time = SWEDEN_TIMEZONE.localize(
    NAIVE_STUDENT_SESSIONS_OPEN
)
STUDENT_SESSIONS_OPEN_UTC = student_sessions_open_sweden_time.astimezone(pytz.utc)

# Student Sessions Booking Closes (26 oktober 23.59.59)
NAIVE_STUDENT_SESSIONS_CLOSE = datetime.datetime(2025, 10, 26, 23, 59, 59)
student_sessions_close_sweden_time = SWEDEN_TIMEZONE.localize(
    NAIVE_STUDENT_SESSIONS_CLOSE
)
STUDENT_SESSIONS_CLOSE_UTC = student_sessions_close_sweden_time.astimezone(pytz.utc)

# Student Time Slot Booking Opens (2 november 17:00)
NAIVE_STUDENT_SLOT_BOOKING_OPEN = datetime.datetime(2025, 11, 2, 17, 0, 0)
student_slot_booking_open_sweden_time = SWEDEN_TIMEZONE.localize(
    NAIVE_STUDENT_SLOT_BOOKING_OPEN
)
STUDENT_SLOT_BOOKING_OPEN_UTC = student_slot_booking_open_sweden_time.astimezone(
    pytz.utc
)

# Student Time Slot Booking Closes (5 november 23:59)
NAIVE_STUDENT_SLOT_BOOKING_CLOSE = datetime.datetime(2025, 11, 5, 23, 59, 0)
student_slot_booking_close_sweden_time = SWEDEN_TIMEZONE.localize(
    NAIVE_STUDENT_SLOT_BOOKING_CLOSE
)
STUDENT_SLOT_BOOKING_CLOSE_UTC = student_slot_booking_close_sweden_time.astimezone(
    pytz.utc
)

# Companies Receive Confirmed Student Session Schedule (6 november 00:00)
NAIVE_COMPANY_SCHEDULE_RECEIVE = datetime.datetime(2025, 11, 6, 0, 0, 0)
company_schedule_receive_sweden_time = SWEDEN_TIMEZONE.localize(
    NAIVE_COMPANY_SCHEDULE_RECEIVE
)
COMPANY_SCHEDULE_RECEIVE_UTC = company_schedule_receive_sweden_time.astimezone(pytz.utc)

# All Company Visits Booking Closes (12 november 23:59)
NAIVE_COMPANY_VISITS_CLOSE = datetime.datetime(2025, 11, 12, 23, 59, 0)
company_visits_close_sweden_time = SWEDEN_TIMEZONE.localize(NAIVE_COMPANY_VISITS_CLOSE)
COMPANY_VISITS_CLOSE_UTC = company_visits_close_sweden_time.astimezone(pytz.utc)
