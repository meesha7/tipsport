# Generated by Django 2.0.2 on 2018-02-16 22:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ts', '0005_auto_20180216_2301'),
    ]

    operations = [
        migrations.AddField(
            model_name='bet',
            name='live',
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
    ]
