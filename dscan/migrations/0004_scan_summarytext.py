# Generated by Django 2.1.2 on 2019-01-11 04:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dscan', '0003_auto_20190110_0520'),
    ]

    operations = [
        migrations.AddField(
            model_name='scan',
            name='summaryText',
            field=models.TextField(null=True),
        ),
    ]
