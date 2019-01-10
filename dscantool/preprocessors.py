from django.conf import settings


# Provides settings from the configuration file in templates
def template_settings(request):
    return {
        'debug': settings.DEBUG
    }