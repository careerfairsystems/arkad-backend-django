# Generated by Django 5.1.6 on 2025-03-08 17:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_models', '0011_remove_company_days_at_arkad'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='url_facebook',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='url_instagram',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='url_linkedin',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='url_twitter',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='url_youtube',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
