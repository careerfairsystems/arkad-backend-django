# Generated by Django 5.1.6 on 2025-03-08 17:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_models', '0013_job_company_jobs'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='description',
            field=models.TextField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='link',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='title',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
