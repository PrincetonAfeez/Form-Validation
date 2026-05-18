""" Models for the forms lab app. """

from django.db import models


class ValidationLog(models.Model):
    form_name = models.CharField(max_length=64)
    field_name = models.CharField(max_length=64, blank=True, null=True)
    error_code = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["form_name", "field_name", "error_code"]),
            models.Index(fields=["created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        field = self.field_name or "__all__"
        return f"{self.form_name}.{field}: {self.error_code}"
