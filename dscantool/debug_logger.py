from django.conf import settings
import inspect
from datetime import datetime
from termcolor import colored
import colorama
colorama.init()


# Logs lines to console with pretty-ish formatting and extra information
def log(*msg):
    if settings.DEBUG:
        colors = ["grey", "red", "green", "cyan", "magenta", "blue", "yellow"]

        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        c = 0
        for l in calframe[1][3]:
            c+=ord(l)
            c %= len(colors)

        print(datetime.now(), colored(calframe[1][3], colors[c]), msg)