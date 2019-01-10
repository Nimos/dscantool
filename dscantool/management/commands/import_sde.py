from django.core.management.base import BaseCommand
from esi.models import InvGroup, InvType

from os import path
import yaml

class Command(BaseCommand):
    help = 'Imports Groups and Types from .yaml files located in eve_data'

    def handle(self, *args, **options):

        if not path.exists("eve_data/groupIDs.yaml"):
            print("Couldn't open 'eve_data/groupIDs.yaml', see README for more information")
            return

        if not path.exists("eve_data/typeIDs.yaml"):
            print("Couldn't open 'eve_data/typeIDs.yaml', see README for more information")
            return


        print("Loading Groups...")

        newGroups = []
        try:
            file = open("eve_data/groupIDs.yaml", encoding="utf-8")
            groups = yaml.load(file)

            for g in groups:
                print(g, end="\r")
                if (groups[g]["name"].get("en", False)):
                    newGroups.append(InvGroup(groupID=g, groupName=groups[g]["name"].get("en").encode("utf8"), categoryID=groups[g]["categoryID"]))

            InvGroup.objects.all().delete()
            InvGroup.objects.bulk_create(newGroups)

        except Exception as e:
            print("Error reading groupIDs.yaml", e)

        print("Loading Types...")

        newTypes = []
        try:
            file = open("eve_data/typeIDs.yaml", encoding="utf-8")
            types = yaml.load(file)

            for g in types:
                print(g, end="\r")
                if (types[g]["name"].get("en", False)):
                    newTypes.append(InvType(typeID=g, typeName=types[g]["name"].get("en").encode("utf-8"), group_id=types[g]["groupID"]))

            InvType.objects.all().delete()
            InvType.objects.bulk_create(newTypes)

        except Exception as e:
            print("Error reading groupIDs.yaml", e)
