""" Context processors for the forms lab app. """

from .forms import DEMOS


def demo_navigation(request):
    return {"demo_navigation": DEMOS}
