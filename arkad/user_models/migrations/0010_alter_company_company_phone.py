# Generated by Django 5.1.6 on 2025-03-08 17:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_models', '0009_alter_company_company_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='company_phone',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
