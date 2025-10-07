from django import forms

class CreateLunchEventForm(forms.Form):
    username = forms.CharField(label="Username", max_length=100)
    time_start = forms.DateTimeField(
        label="Start Time",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )
    duration = forms.IntegerField(label="Duration in minutes")
    amount = forms.IntegerField(label="Number of tickets")

