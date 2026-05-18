""" URLs for the forms lab app. """

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.forms_lab.urls")),
]
