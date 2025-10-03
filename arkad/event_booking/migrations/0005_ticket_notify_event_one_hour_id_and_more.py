from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event_booking', '0004_event_release_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='notify_event_one_hour_id',
            field=models.CharField(null=True),
        ),
        migrations.AddField(
            model_name="ticket",
            name="notify_event_tmrw_id",
            field=models.CharField(null=True),
        ),
    ]
