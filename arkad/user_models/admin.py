from django.contrib import admin

from .models import User, Favourites

# Register your models here.
admin.site.register(User)

admin.site.register(Favourites)