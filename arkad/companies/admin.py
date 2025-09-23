from django.contrib import admin
from companies.models import Job, Company

# Register your models here.
class CompanyAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['name', 'website', 'company_email']
    list_filter = ['desired_degrees', ]

admin.site.register(Job)
admin.site.register(Company, CompanyAdmin)
