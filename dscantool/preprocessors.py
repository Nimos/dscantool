from django.conf import settings


# Provides settings from the configuration file in templates
def template_settings(request):
    return {
        'debug': settings.DEBUG,
        'site_name': settings.DSCAN_SITE_NAME,
        'eve_image_url': settings.DSCAN_EVE_IMAGE_URL,
        'repository_url': settings.DSCAN_REPOSITORY_URL,
        'zkillboard_url': settings.DSCAN_ZKILLBOARD_URL,
        'dotlan_url': settings.DSCAN_DOTLAN_URL,
        'feedback': settings.DSCAN_FEEDBACK
    }
