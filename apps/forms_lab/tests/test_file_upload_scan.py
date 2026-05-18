""" Test file upload scan. """

from __future__ import annotations

from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.forms_lab.services import validate_file_upload_field


def _tiny_png_upload(name: str = "avatar.png") -> SimpleUploadedFile:
    image_io = BytesIO()
    Image.new("RGB", (10, 10), "white").save(image_io, format="PNG")
    image_io.seek(0)
    return SimpleUploadedFile(name, image_io.read(), content_type="image/png")


@pytest.mark.django_db
def test_file_scan_avatar_only_without_resume(client):
    png = _tiny_png_upload()
    response = client.post(
        "/forms/file-upload/scan/",
        {"_field": "avatar", "avatar": png},
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == 200
    assert b"Validation passed" in response.content
    assert b"resume" not in response.content.lower() or b"required" not in response.content


@pytest.mark.django_db
def test_file_scan_resume_only(client):
    pdf = SimpleUploadedFile(
        "resume.pdf", b"%PDF-1.4\nbody", content_type="application/pdf"
    )
    response = client.post(
        "/forms/file-upload/scan/",
        {"_field": "resume", "resume": pdf},
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == 200
    assert b"Validation passed" in response.content


@pytest.mark.django_db
def test_file_scan_missing_field_param_is_404(client):
    response = client.post("/forms/file-upload/scan/", {}, HTTP_HX_REQUEST="true")
    assert response.status_code == 404


@pytest.mark.django_db
def test_file_scan_unknown_field_is_404(client):
    response = client.post(
        "/forms/file-upload/scan/",
        {"_field": "not_a_field"},
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == 404


def test_validate_file_upload_field_rejects_unknown_name():
    with pytest.raises(ValueError, match="Unknown file field"):
        validate_file_upload_field("bogus", {}, None)
