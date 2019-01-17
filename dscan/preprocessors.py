from .models import Scan
from datetime import timedelta
from django.utils import timezone

# Provides settings from the configuration file in templates
def template_stats(request):
    dscans = Scan.objects.filter(type=Scan.DSCAN).count()
    localscans = Scan.objects.filter(type=Scan.LOCALSCAN).count()
    total = Scan.objects.count()
    day = Scan.objects.filter(created__gte=timezone.now()-timedelta(hours=24)).count()
    return {
        'stats': {
            "day": day,
            "total": total,
            "d": dscans,
            "l": localscans
        }
    }
