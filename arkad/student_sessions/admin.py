from django.contrib import admin

from student_sessions.models import (
    StudentSession,
    StudentSessionApplication,
    StudentSessionTimeslot,
)

admin.site.register(StudentSession)
admin.site.register(StudentSessionApplication)
admin.site.register(StudentSessionTimeslot)
