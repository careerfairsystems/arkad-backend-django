# Generated by Django 5.2 on 2025-05-19 16:58

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0002_alter_company_desired_competences_and_more'),
        ('student_sessions', '0004_alter_companystudentsessionmotivation_motivation_text'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(
            old_name='CompanyStudentSessionMotivation',
            new_name='CompanyStudentSessionApplicationInformation',
        ),
    ]
