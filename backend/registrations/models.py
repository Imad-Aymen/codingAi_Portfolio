"""Academic registration model for the CODING AI club."""

import uuid
from pathlib import Path

from django.db import models
from django.utils import timezone
from django.utils.text import get_valid_filename


def certificate_upload_path(instance, filename):
    """Organized, safe path: media/certificates/YYYY/MM/<uuid>/<name>.pdf

    A uuid prevents name collisions before the row is saved (no pk yet),
    and get_valid_filename strips any path from the browser-supplied name.
    """
    now = timezone.now()
    safe_name = get_valid_filename(Path(filename).name) or "certificate.pdf"
    if not safe_name.lower().endswith(".pdf"):
        safe_name = Path(safe_name).stem + ".pdf"
    return f"certificates/{now:%Y}/{now:%m}/{uuid.uuid4().hex}/{safe_name}"


class SchoolYear(models.TextChoices):
    """Accepted school years — matches the <select> values in the UI."""

    YEAR_1 = "1", "Year 1"
    YEAR_2 = "2", "Year 2"
    YEAR_3 = "3", "Year 3"
    YEAR_4 = "4", "Year 4"
    YEAR_5 = "5", "Year 5"
    YEAR_6 = "6", "Year 6"


class Registration(models.Model):
    """One registration per student: academic data + a certificate PDF.

    Duplicate policy: the email is unique (unique=True) and stored in
    lowercase, so only one registration per email is allowed. A second
    attempt returns a clear 400 instead of a duplicate row or a 500 error.
    """

    full_name = models.CharField("Full name", max_length=150)
    department = models.CharField("Department / Major", max_length=150)
    school_year = models.CharField("School year", max_length=1, choices=SchoolYear.choices)
    email = models.EmailField("Email address", unique=True)
    certificate_pdf = models.FileField("Certificate PDF", upload_to=certificate_upload_path)
    created_at = models.DateTimeField("Created at", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Registration"
        verbose_name_plural = "Registrations"

    def __str__(self):
        return f"{self.full_name} <{self.email}>"
