# Generated by Django 2.0.2 on 2018-02-16 22:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ts', '0007_bet_closed'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bet',
            name='live',
        ),
    ]