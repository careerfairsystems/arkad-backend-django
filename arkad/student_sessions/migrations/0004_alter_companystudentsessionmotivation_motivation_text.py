# Generated by Django 5.1.6 on 2025-04-05 11:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student_sessions', '0003_remove_studentsession_applicants_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='companystudentsessionmotivation',
            name='motivation_text',
            field=models.TextField(blank=True, null=True),
        ),
    ]
