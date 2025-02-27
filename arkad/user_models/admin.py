from django.contrib import admin

from .models import User
from .company_models import Company

# Register your models here.
admin.site.register(User)
admin.site.register(Company)
