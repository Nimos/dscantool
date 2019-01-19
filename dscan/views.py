from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from esi.models import InvType, InvGroup
from django.conf import settings
from secrets import token_urlsafe
import re, json
from dscan.models import Scan, Corporation, Alliance
from esi.api import esiRequest
from django.utils.html import escape


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


def _parse_dscan(request, scan_data):

    # Parse input and count ships
    shipCount = {}
    solarSystem = None

    solarSystemIdentifierTypes = InvType.objects.filter(group_id__in=settings.SOLAR_SYSTEM_IDENTIFIERS).values_list("typeID", flat=True)

    # Parse Raw Data
    for line in scan_data:
        line = line.split("\t")
        try:
            line[0] = int(line[0])
        except: 
            continue

        if not shipCount.get(line[0], False):
            shipCount[line[0]] = 1
        else:
            shipCount[line[0]] += 1
        
        # Detect solar system
        if not solarSystem and line[0] in solarSystemIdentifierTypes:
            # Format for citadels and other structures
            matches = re.match(r'([A-z0-9\- ]+) -', line[1])
            if matches:
                solarSystem = matches.group(1)
            
            # Format for planets, moons and belts
            matches = re.match(r'([A-z0-9\- ]+) [XVI]+', line[1])
            if matches:
                solarSystem = matches.group(1)

            # Format for Customs Offices
            matches = re.match(r'Customs Office \(([A-z0-9\- ]+) [XVI]+\)', line[1])
            if matches:
                solarSystem = matches.group(1)

    # Get item type information from cache
    typeIDs = list(shipCount.keys())
    cachedTypes = InvType.objects.filter(typeID__in=typeIDs)

    # Figure out what's missing
    cachedIDs = set(cachedTypes.values_list("typeID", flat=True))
    missingIDs = list(set(typeIDs)-cachedIDs)

    if missingIDs:
        # Get missing IDs from ESI
        newTypes = []
        newGroups = []
        for typeID in missingIDs:
            try:
                result = esiRequest('/universe/types/'+str(typeID)+'/')

                # Create DB object for type
                invType = InvType(typeID=typeID)
                invType.typeName = result["name"]
                invType.group_id = result["group_id"]

                newTypes.append(invType)

                # Check if we need to fetch group information too
                if not InvGroup.objects.filter(groupID=invType.group_id).exists():
                    result = esiRequest('/universe/groups/'+str(invType.group_id)+'/')

                    invGroup = InvGroup(groupID=result["group_id"])
                    invGroup.groupName = result["name"]
                    invGroup.categoryID = result["category_id"]

                    invGroup.save()

            except Exception as e:
                # To avoid malicious users making us spam ESI calls with invalid typeIDs we'll abort after the first error
                print("Parse Error:", e)
                return render(request, "landing.html", {"error": "Something's wrong with your dscan data: Error retrieving type info for typeID "+str(typeID)})

        # Save new objects
        InvType.objects.bulk_create(newTypes)

        # Get a fresh queryset with the new types
        cachedTypes = InvType.objects.filter(typeID__in=typeIDs)


    ships = []
    groupCount = {}
    for ship in cachedTypes:
        ships.append({"name": ship.typeName, "count": shipCount[ship.typeID], "group": ship.group_id, "category": ship.group.categoryID})

        if not groupCount.get(ship.group_id, False):
            groupCount[ship.group_id] = shipCount[ship.typeID]
        else:
            groupCount[ship.group_id] += shipCount[ship.typeID]

    # Sum up groups and add group information
    groupIDs = list(groupCount.keys())
    invGroups = InvGroup.objects.filter(groupID__in=groupIDs)
    groups = []
    for invGroup in invGroups:
        groups.append({"id": invGroup.groupID, "name": invGroup.groupName, "count": groupCount[invGroup.groupID], "category": invGroup.categoryID})


    # Sort by how many of each they are
    groups = sorted(groups, key=lambda g: g["count"], reverse=True)
    ships = sorted(ships, key=lambda g: g["count"], reverse=True)

    # Sort everything into preset categories
    categories = {"ships": {}, "groups": {}}
    summary = []

    for ship in ships:
        default = True
        for category in settings.DSCAN_CATEGORIES:           
            if ship["group"] in settings.DSCAN_CATEGORIES[category]["groups"] or ship["category"] in settings.DSCAN_CATEGORIES[category]["categories"]:
                if not categories["ships"].get(category, False):
                    categories["ships"][category] = [[], 0]
                categories["ships"][category][0].append(ship) 
                categories["ships"][category][1] += ship["count"]
                default = False
        if default:
            if not categories["ships"].get("Ships", False):
               categories["ships"]["Ships"] = [[], 0]
            categories["ships"]["Ships"][0].append(ship)
            categories["ships"]["Ships"][1] += ship["count"]

        if ship["category"] == 6:
            summary.append(ship)

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


    # Prepare summary for meta tags
    othersCount = 0
    for ship in summary[3:]:
        othersCount += ship["count"]

    summaryText = ""
    for ship in summary[0:3]:
        summaryText += str(ship["count"]) + " " + ship["name"] + "\n"
    
    if othersCount > 0:
        summaryText += "("+str(othersCount)+" more)"

    # Prepare data for template
    result = []
    for category in settings.CATEGORY_ORDER:
        if categories["ships"].get(category, False):
            result.append((category, categories["ships"][category], categories["groups"][category]))

    token = token_urlsafe(6)[:6]
    while Scan.objects.filter(token=token).exists():
        token = token_urlsafe(6)[:6]

    savedScan = Scan(token=token, data=json.dumps(result), solarSystem=solarSystem, type=Scan.DSCAN, summaryText=summaryText, raw="\n".join(scan_data))
    savedScan.save()


    return redirect("dscan:show", token=token)

# Parse a local list
def _parse_local(request, scan_data):
    # Convert to set to remove duplicates
    data = list(set(scan_data))

    # Remove empty lines
    data = [x for x in data if x != '']

    n = 0
    affiliations = []
    while 500*n <= len(data):

        ids = esiRequest('/universe/ids/', data[500*n:500*(n+1)])

        if not ids.get("characters", False):
            return render(request, "landing.html", {"error": "Error: Didn't detect any valid characters in this local."})

        ids = [c["id"] for c in ids["characters"]]
        affiliations += esiRequest('/characters/affiliation/', ids)

        n += 1


    # Count
    corps = {}
    alliances = {}
    for character in affiliations:
        character["alliance_id"] = character.get("alliance_id", -1)
        
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
    
    # Get cached names from DB
    corpIDs = list(corps.keys())
    cachedCorps = Corporation.objects.filter(corporationID__in=corpIDs)

    for corp in cachedCorps:
        corps[corp.corporationID]["name"] = corp.name
        corps[corp.corporationID]["ticker"] = corp.ticker
        corps[corp.corporationID]["id"] = corp.corporationID

        result["corps"].append(corps[corp.corporationID])


    # Check which corps we need to get from ESI
    cachedIDs = set(cachedCorps.values_list("corporationID", flat=True))
    missingIDs = list(set(corpIDs)-cachedIDs)


    # Get missing corps and save
    newCorpCache = []
    for corpID in missingIDs:
        corporation = Corporation(corporationID=corpID)

        corpInfo = esiRequest('/corporations/'+str(corpID)+'/')

        corporation.ticker = corpInfo["ticker"]
        corporation.name = corpInfo["name"]
        newCorpCache.append(corporation)

        corps[corpID]["name"] = corporation.name
        corps[corpID]["ticker"] = corporation.ticker
        corps[corpID]["id"] = corpID

        result["corps"].append(corps[corpID])

    Corporation.objects.bulk_create(newCorpCache)


    # Same thing for alliances
    
    # Get cached alliances from DB
    allianceIDs = list(alliances.keys())
    cachedAlliances = Alliance.objects.filter(allianceID__in=allianceIDs)

    for alliance in cachedAlliances:
        alliances[alliance.allianceID]["name"] = alliance.name
        alliances[alliance.allianceID]["ticker"] = alliance.ticker
        alliances[alliance.allianceID]["id"] = alliance.allianceID

        result["alliances"].append(alliances[alliance.allianceID])

    # Check which ones are missing
    cachedIDs = set(cachedAlliances.values_list("allianceID", flat=True))
    missingIDs = list(set(allianceIDs)-cachedIDs)

    # Get missing alliances from ESI
    newAllianceCache = []
    for allianceID in missingIDs:
        if allianceID == -1:
            alliances[allianceID]["name"] = ""
            alliances[allianceID]["ticker"] = ""
            continue

        alliance = Alliance(allianceID=allianceID)

        allianceInfo = esiRequest('/alliances/'+str(allianceID)+'/')

        alliance.ticker = allianceInfo["ticker"]
        alliance.name = allianceInfo["name"]
        newAllianceCache.append(alliance)

        alliances[allianceID]["name"] = alliance.name
        alliances[allianceID]["ticker"] = alliance.ticker
        alliances[allianceID]["id"] = allianceID

        result["alliances"].append(alliances[allianceID])

    Alliance.objects.bulk_create(newAllianceCache)


    # Sort result
    result["alliances"] = sorted(result["alliances"], key=lambda x: x["count"], reverse=True)
    result["corps"] = sorted(result["corps"], key=lambda x: x["count"], reverse=True)


    # Prepare summary for meta tags
    othersCount = 0
    for alliance in result["alliances"][3:]:
        othersCount += alliance["count"]

    summaryText = ""
    for alliance in result["alliances"][0:3]:
        summaryText += str(alliance["count"]) + " " + alliance["name"] + "\n"
    
    if othersCount > 0:
        summaryText += "("+str(othersCount)+" more)"

    # Generate url token
    token = token_urlsafe(6)[:6]
    while Scan.objects.filter(token=token).exists():
        token = token_urlsafe(6)[:6]

    # Save
    savedScan = Scan(token=token, data=json.dumps(result), type=Scan.LOCALSCAN, summaryText=summaryText, raw="\n".join(scan_data))
    savedScan.save()


    return redirect("dscan:show", token=token)



# About page with CCP Legal notice and License
def about(request):
    return render(request, "about.html")


# Show a saved scan
def show(request, token):
    scan = get_object_or_404(Scan, token=token)

    if scan.type == Scan.DSCAN:
        return render(request, "dscan.html", {"created": scan.created, "token": token, "solarSystem": scan.solarSystem, "data": json.loads(scan.data), "summaryText": scan.summaryText})
    elif scan.type == Scan.LOCALSCAN:
        return render(request, "localscan.html", {"created": scan.created, "token": token, "data": json.loads(scan.data), "summaryText": scan.summaryText})

# Prettier error handling
def error404(request, exception, template_name=""):
    token = escape(request.path[1:])
    return render(request, "landing.html", {"error": "<h5>Error 404 - Not Found</h5><br>Could not find a saved scan with the token \""+token+"\"."}, status=404)

def error500(request, exception=None, template_name=""):
    print("ERROR 500 on ", request.method, request.path)
    print("Exception: ", exception)
    return render(request, "landing.html", {"error": "<h5>Error 500 - Internal Server Error</h5>If this problem persists please contact me on Discord, send me a mail ingame or create an issue on Github.<br>Check the footer for contact information."}, status=500)

def error400(request, exception=None, template_name=""):
    print("ERROR 400 on ", request.method, request.path)
    print("Exception: ", exception)
    return render(request, "landing.html", {"error": "<h5>Error 400 - Bad Request</h5>If this problem persists please contact me on Discord, send me a mail ingame or create an issue on Github.<br>Check the footer for contact information."}, status=400)
