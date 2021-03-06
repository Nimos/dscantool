# Generated by Django 2.1.2 on 2019-01-10 04:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dscan', '0002_alliance_corporation'),
    ]

    operations = [
        migrations.CreateModel(
            name='Scan',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('token', models.CharField(max_length=6)),
                ('solarSystem', models.TextField(null=True)),
                ('data', models.TextField()),
                ('type', models.IntegerField(choices=[(0, 'DScan'), (1, 'Local Scan')])),
            ],
        ),
        migrations.DeleteModel(
            name='DScan',
        ),
    ]
