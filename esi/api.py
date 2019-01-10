from .models import EsiCall
import json
from dscantool.debug_logger import log
from urllib.request import urlopen, Request as urlrequest
import urllib
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import pytz

ESI_BASE = settings.ESI_BASE

# Runs a request to the specified ESI route with the arguments provided
# Automatically chooses the HTTP method unless you pass a custom one
# Automatically obeys cache times
def esiRequest(route, arguments={}, auth=None):
        
    # Look in the database if we have a cached result for this call
    cachedCall = EsiCall.objects.filter(route=route, arguments=json.dumps(arguments)).order_by('cachedUntil').last()

    # Compare cache time and return result
    if cachedCall and (not cachedCall.cachedUntil or cachedCall.cachedUntil > timezone.now()):
        try:
            log("Cache Return for ", route)
            return json.loads(cachedCall.cachedResult)
        except Exception as e:
            log(cachedCall.cachedResult, "HELP", e)
            return None
    elif not cachedCall:
        print("Route :"+route)
        cachedCall = EsiCall(route=route, arguments=json.dumps(arguments))
    
    
    # Prepare auth headers if needed
    headers = {}
    
    if auth:
        # if access token is expired, use refresh token
        if auth.tokenExpiry < timezone.now():
            auth = refreshAccessToken(auth)
            log("Using refresh token", )

        authorization = "Bearer "+auth.accessToken

        headers['Authorization'] = authorization


    # Acess ESI
    if not arguments:
        request = urlrequest(ESI_BASE + route, headers=headers)
    else:
        headers['content-type'] = 'application/json'
        data = json.dumps(arguments).encode('utf-8')
        request = urlrequest(ESI_BASE + route, data=data, headers=headers)

        log(request.data)

    log("ESI request to "+ request.get_method()+" "+route)

    try:
        response = urlopen(request)
        result = response.read().decode("utf-8")
        cachedCall.cachedResult = result
        
        result = json.loads(result)

        cachedUntil = response.info().get('expires')
        if cachedUntil:
            cachedCall.cachedUntil = datetime.strptime(cachedUntil, '%a, %d %b %Y %H:%M:%S GMT').replace(tzinfo=pytz.UTC)

        cachedCall.save()
        return result

    except urllib.error.HTTPError as e:
        r = e.read()
        log("ESI Exception:", r)
        return []