# Generated by Django 2.1.7 on 2019-03-23 04:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('RPSer', '0002_auto_20190322_1849'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='brain',
            index=models.Index(fields=['username', 'rpser_last', 'user_last'], name='RPSer_brain_usernam_b44606_idx'),
        ),
    ]