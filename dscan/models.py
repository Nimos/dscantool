from django.db import models

# Create your models here.
class Scan(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=6)

    solarSystem = models.TextField(null=True)
    data = models.TextField() 

    DSCAN = 0
    LOCALSCAN = 1
    SCAN_TYPE_CHOICES = (
        (DSCAN, 'DScan'),
        (LOCALSCAN, 'Local Scan'),
    )
    type = models.IntegerField(choices=SCAN_TYPE_CHOICES)

class Corporation(models.Model):
    corporationID = models.BigIntegerField()

    ticker = models.TextField()
    name = models.TextField()

class Alliance(models.Model):
    allianceID = models.BigIntegerField()

    ticker = models.TextField()
    name = models.TextField()