from django.db import models

# Create your models here.
class EsiCall(models.Model):
    route = models.TextField()
    arguments = models.TextField()

    cachedUntil = models.DateTimeField(null=True)
    cachedResult = models.TextField()


class Character(models.Model):
    characterID = models.BigIntegerField(unique=True)
    charName = models.CharField(max_length=200)

    corpID = models.BigIntegerField()
    corpName = models.CharField(max_length=200)

    allianceID = models.BigIntegerField(null=True)
    allianceName = models.CharField(max_length=100)


    def __str__(self):
        return self.charName


class InvType(models.Model):
    typeID = models.BigIntegerField(unique=True)
    typeName = models.CharField(max_length=200)
    group = models.ForeignKey('InvGroup', to_field='groupID', on_delete=models.DO_NOTHING, db_constraint=False)

class InvGroup(models.Model):
    groupID = models.BigIntegerField(unique=True)
    groupName = models.CharField(max_length=200)
    categoryID = models.BigIntegerField()

    capital = models.BooleanField(default=False)