""" URLs for the forms lab app. """

from django.urls import path

from . import views

app_name = "forms_lab"

urlpatterns = [
    path("", views.index, name="index"),
    path("forms/<slug:slug>/", views.form_detail, name="form_detail"),
    path("forms/<slug:slug>/field/<slug:name>/", views.field_validate, name="field"),
    path(
        "forms/signup/check-username/",
        views.signup_check_username,
        name="check_username",
    ),
    path("forms/signup/check-email/", views.signup_check_email, name="check_email"),
    path(
        "forms/address/country-change/",
        views.address_country_change,
        name="country_change",
    ),
    path(
        "forms/payment/brand-detect/", views.payment_brand_detect, name="brand_detect"
    ),
    path("forms/wizard/step/<int:n>/", views.wizard_step, name="wizard_step"),
    path("forms/file-upload/scan/", views.file_upload_scan, name="file_scan"),
    path("forms/formset/add-row/", views.formset_add_row, name="formset_add_row"),
    path(
        "forms/survey/toggle-passport/",
        views.survey_toggle_passport,
        name="toggle_passport",
    ),
    path("stats/", views.stats, name="stats"),
    path("reference/", views.reference, name="reference"),
]
