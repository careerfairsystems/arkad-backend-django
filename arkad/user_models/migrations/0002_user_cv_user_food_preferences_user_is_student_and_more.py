# Generated by Django 5.1.6 on 2025-02-26 18:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_models', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='cv',
            field=models.FileField(blank=True, null=True, upload_to='user/cv', verbose_name='Users cv'),
        ),
        migrations.AddField(
            model_name='user',
            name='food_preferences',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='is_student',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='user',
            name='linkedin',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='master_title',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='profile_picture',
            field=models.FileField(blank=True, null=True, upload_to='user/profile-pictures', verbose_name='User profile picture'),
        ),
        migrations.AddField(
            model_name='user',
            name='programme',
            field=models.CharField(blank=True, choices=[('Brandingenjör', 'Brandingenjor'), ('Maskinteknik_Teknisk_Design', 'Maskinteknik Td'), ('Elektroteknik', 'Elektroteknik'), ('Ekosystemteknik', 'Ekosystemteknik'), ('Maskinteknik', 'Maskinteknik'), ('Nanoveteknik', 'Nanoveteknik'), ('Bioteknik', 'Bioteknik'), ('Industridesign', 'Industridesign'), ('Arkitekt', 'Arkitekt'), ('Informations och Kommunikationsteknik', 'Infokomm Teknik'), ('Kemiteknik', 'Kemiteknik'), ('Byggteknik med Järnvägsteknik', 'Bygg Jarnvag'), ('Väg och vatttenbyggnad', 'Vag Vatten'), ('Byggteknik med arkitektur', 'Bygg Arkitektur'), ('Industriell ekonomi', 'Industriell Ekonomi'), ('Teknisk Matematik', 'Teknisk Matematik'), ('Medicinteknik', 'Medicinteknik'), ('Lantmäteri', 'Lantmateri'), ('Datateknik', 'Datateknik'), ('Teknisk Fysik', 'Teknisk Fysik'), ('Byggteknik med väg och trafikteknik', 'Bygg Vag Trafik')], max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='study_year',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
