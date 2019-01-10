from django.shortcuts import render, redirect, get_object_or_404
from esi.models import InvType, InvGroup
from django.conf import settings
from secrets import token_urlsafe
import re, json
from dscan.models import Scan, Corporation, Alliance
from esi.api import esiRequest


# Create your views here.
def landing(request):
    return render(request, "landing.html")

def parse(request):
    if request.method != "POST":
        return landing(request)

    data = request.POST.get("data", None)

    if not data or data == "":
        return render(request, "landing.html", {"error": "Error: No Data submitted"})

    # Remove \r
    data = data.replace("\r", "")
    data = data.split("\n")
    if "\t" in data[0]:
        return _parse_dscan(request, data)
    else:
        return _parse_local(request, data)


def _parse_dscan(request, data):

    # Parse input and count ships
    shipCount = {}
    solarSystem = None

    for line in data:
        line = line.split("\t")

        if not shipCount.get(line[0], False):
            shipCount[line[0]] = 1
        else:
            shipCount[line[0]] += 1

        # Detect solar system
        if not solarSystem and line[1] and line[0] in ["11","12","13","14","15","2015","2063","2233","3799","35825","35832","35833","35835","45036","47513"]:
            if re.match(r'[A-z0-9\-]+ -', line[1]):
                solarSystem = line[1].split(" -")[0]
            elif re.match(r'[A-z0-9\-]+ [XVI]+', line[1]):
                solarSystem = line[1].split(" ")[0]

    # Get more information about ship types
    ships = []
    groupCount = {}
    for ship in shipCount:
        try:
            invType = InvType.objects.get(typeID=ship)
        except:
            continue
            return render(request, "landing.html", {"error": "Something's wrong with your dscan data."})
        ships.append({"name": invType.typeName, "count": shipCount[ship], "group": invType.group_id, "category": invType.group.categoryID})

        if not groupCount.get(invType.group_id, False):
            groupCount[invType.group_id] = shipCount[ship]
        else:
            groupCount[invType.group_id] += shipCount[ship]

    # Sum up groups
    groups = []
    for group in groupCount:
        invGroup = InvGroup.objects.get(groupID=group)
        groups.append({"id": invGroup.groupID, "name": invGroup.groupName, "count": groupCount[group], "category": invGroup.categoryID})


    # Sort by how many of each they are
    groups = sorted(groups, key=lambda g: g["count"], reverse=True)
    ships = sorted(ships, key=lambda g: g["count"], reverse=True)

    # Sort everything into preset categories
    categories = {"ships": {}, "groups": {}}

    for ship in ships:
        default = True
        for category in settings.DSCAN_CATEGORIES:           
            if ship["group"] in settings.DSCAN_CATEGORIES[category]["groups"] or ship["category"] in settings.DSCAN_CATEGORIES[category]["categories"]:
                if not categories["ships"].get(category, False):
                    categories["ships"][category] = []
                categories["ships"][category].append(ship) 
                default = False
        if default:
            if not categories["ships"].get("Ships", False):
               categories["ships"]["Ships"] = []
            categories["ships"]["Ships"].append(ship)

    for group in groups:
        default = True
        for category in settings.DSCAN_CATEGORIES:           
            if group["id"] in settings.DSCAN_CATEGORIES[category]["groups"] or group["category"] in settings.DSCAN_CATEGORIES[category]["categories"]:
                if not categories["groups"].get(category, False):
                    categories["groups"][category] = []
                categories["groups"][category].append(group) 
                default = False
        if default:
            if not categories["groups"].get("Ships", False):
                categories["groups"]["Ships"] = []
            categories["groups"]["Ships"].append(group)


    # Prepare data for template
    result = []
    for category in settings.CATEGORY_ORDER:
        if categories["ships"].get(category, False):
            result.append((category, categories["ships"][category], categories["groups"][category]))

    token = token_urlsafe(6)[:6]
    while Scan.objects.filter(token=token).exists():
        token = token_urlsafe(6)[:6]

    savedScan = Scan(token=token, data=json.dumps(result), solarSystem=solarSystem, type=Scan.DSCAN)
    savedScan.save()


    return redirect("dscan:show", token=token)

# Parse a local list
def _parse_local(request, data):
    # Convert to set to remove duplicates
    data = list(set(data))

    # Remove empty lines
    data = [x for x in data if x != '']

    ids = esiRequest('/universe/ids/', data)

    if not ids.get("characters", False):
        return render(request, "landing.html", {"error": "Error: Didn't detect any valid characters in this local."})

    ids = [c["id"] for c in ids["characters"]]
    affiliations = esiRequest('/characters/affiliation/', ids)

    # Count
    corps = {}
    alliances = {}
    for character in affiliations:

        character["alliance_id"] = character.get("alliance_id", "-1")
        
        try:
            corps[character["corporation_id"]]["count"] += 1
        except:
            corps[character["corporation_id"]] = {"alliance": character["alliance_id"]}
            corps[character["corporation_id"]]["count"] = 1

        try:
            alliances[character["alliance_id"]]["count"] += 1
        except:
            alliances[character["alliance_id"]] = {"count": 1}


    # Get names and tickers

    result = {"corps": [], "alliances": []}
    for corpID in corps:
        corporation, created = Corporation.objects.get_or_create(corporationID=corpID)

        if created:
            corpInfo = esiRequest('/corporations/'+str(corpID)+'/')

            corporation.ticker = corpInfo["ticker"]
            corporation.name = corpInfo["name"]
            corporation.save()

        corps[corpID]["name"] = corporation.name
        corps[corpID]["ticker"] = corporation.ticker
        corps[corpID]["id"] = corpID

        result["corps"].append(corps[corpID])

    for allianceID in alliances:
        if allianceID == "-1":
            alliances[allianceID]["name"] = ""
            alliances[allianceID]["ticker"] = ""
            continue

        alliance, created = Alliance.objects.get_or_create(allianceID=allianceID)

        if created:
            allianceInfo = esiRequest('/alliances/'+str(allianceID)+'/')

            alliance.ticker = allianceInfo["ticker"]
            alliance.name = allianceInfo["name"]
            alliance.save()

        alliances[allianceID]["name"] = alliance.name
        alliances[allianceID]["ticker"] = alliance.ticker
        alliances[allianceID]["id"] = allianceID

        result["alliances"].append(alliances[allianceID])

    result["alliances"] = sorted(result["alliances"], key=lambda x: x["count"], reverse=True)
    result["corps"] = sorted(result["corps"], key=lambda x: x["count"], reverse=True)

    token = token_urlsafe(6)[:6]
    while Scan.objects.filter(token=token).exists():
        token = token_urlsafe(6)[:6]

    savedScan = Scan(token=token, data=json.dumps(result), type=Scan.LOCALSCAN)
    savedScan.save()


    return redirect("dscan:show", token=token)



# About page with CCP Legal notice and License
def about(request):
    return render(request, "about.html")


# Show a saved scan
def show(request, token):
    scan = get_object_or_404(Scan, token=token)

    if scan.type == Scan.DSCAN:
        return render(request, "dscan.html", {"created": scan.created, "token": token, "solarSystem": scan.solarSystem, "data": json.loads(scan.data)})
    elif scan.type == Scan.LOCALSCAN:
        return render(request, "localscan.html", {"created": scan.created, "token": token, "data": json.loads(scan.data)})