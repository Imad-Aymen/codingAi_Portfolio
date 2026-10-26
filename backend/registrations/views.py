"""API endpoints for CODING AI registration portal.

POST /api/registrations/  - Student registration
"""

import logging
import os

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Registration, SchoolYear

logger = logging.getLogger(__name__)


MAX_PDF_BYTES = 15 * 1024 * 1024  # 15MB: one PDF certificate only
PDF_CONTENT_TYPES = {"application/pdf", "application/x-pdf", "application/octet-stream"}
REQUIRED_FIELDS = ("full_name", "department", "school_year", "email")


def error_response(message, status=400, errors=None):
    """Unified JSON error response: success/message/errors."""
    payload = {"success": False, "message": message}
    if errors:
        payload["errors"] = errors
    return JsonResponse(payload, status=status, json_dumps_params={"ensure_ascii": False})


@csrf_exempt
# CSRF decision: the UI is a standalone single HTML file served from a
# different origin and cannot render a Django template with {% csrf_token %};
# the spec also requires exactly one submission request. This endpoint is
# therefore exempt, compensated by:
#   - restricting origins via CORS_ALLOWED_ORIGINS in settings.py,
#   - full validation of fields and file type/size/signature,
#   - the UI automatically sends X-CSRFToken when the cookie exists.
# If the UI is served from the same Django origin: remove this decorator,
# add ensure_csrf_cookie to the page, and keep the X-CSRFToken header.
def create_registration(request):
    """Validate the request, save the row and file, and return the record id."""

    if request.method != "POST":
        return error_response("Method not allowed. Use POST.", status=405)

    if not (request.content_type or "").startswith("multipart/form-data"):
        return error_response("Invalid content type. multipart/form-data is required.")

    data = request.POST
    errors = {}

    full_name = data.get("full_name", "").strip()
    department = data.get("department", "").strip()
    school_year = data.get("school_year", "").strip()
    email = data.get("email", "").strip().lower()  # normalize case to guarantee uniqueness

    # --- Validate the four fields ---
    if not full_name or len(full_name) > 150:
        errors["full_name"] = "Full name is required (150 characters max)."
    if not department or len(department) > 150:
        errors["department"] = "Department or major is required (150 characters max)."
    if school_year not in SchoolYear.values:
        errors["school_year"] = "School year must be a number from 1 to 6."
    if not email or len(email) > 254:
        errors["email"] = "Email address is required (254 characters max)."
    else:
        try:
            validate_email(email)
        except ValidationError:
            errors["email"] = "Invalid email address format."

    # --- Validate the PDF: name, size, MIME type, signature ---
    uploaded = request.FILES.get("certificate_pdf")
    if uploaded is None:
        errors["certificate_pdf"] = "The certificate PDF is required."
    else:
        if not uploaded.name.lower().endswith(".pdf"):
            errors["certificate_pdf"] = "Only a .pdf file extension is allowed."
        if uploaded.size == 0:
            errors["certificate_pdf"] = "The PDF file is empty."
        elif uploaded.size > MAX_PDF_BYTES:
            errors["certificate_pdf"] = "The PDF exceeds 15 MB."
        if (uploaded.content_type or "").lower() not in PDF_CONTENT_TYPES:
            errors["certificate_pdf"] = "File type not allowed. PDF only."
        # Real file signature (magic bytes) — do not trust the client content_type
        if "certificate_pdf" not in errors:
            try:
                header = uploaded.read(5)
                uploaded.seek(0)
                if header != b"%PDF-":
                    errors["certificate_pdf"] = "The attachment is not a valid PDF (signature mismatch)."
            except (OSError, ValueError, AttributeError):
                logger.exception("Could not read the uploaded PDF")
                return error_response("Could not read the uploaded file.", status=400)

    if errors:
        return error_response("The request data is incomplete or invalid.", status=400, errors=errors)

    # --- Duplicate policy: one email = one registration ---
    if Registration.objects.filter(email__iexact=email).exists():
        return error_response(
            "This email address is already registered with CODING AI.",
            status=400,
            errors={"email": "duplicate"},
        )

    registration = Registration(
        full_name=full_name,
        department=department,
        school_year=school_year,
        email=email,
        certificate_pdf=uploaded,
    )

    try:
        with transaction.atomic():
            registration.save()
    except IntegrityError:
        # Guard against a race between two requests with the same email; clean the file
        _delete_orphan_file(registration)
        return error_response(
            "This email address is already registered with CODING AI.",
            status=400,
            errors={"email": "duplicate"},
        )
    except Exception:
        _delete_orphan_file(registration)
        logger.exception("Unexpected error while saving the registration")
        return error_response("A server error occurred while saving the registration. Try again later.", status=500)

    return JsonResponse(
        {
            "success": True,
            "message": "Your CODING AI registration was saved successfully.",
            "id": registration.id,
            "certificate_url": request.build_absolute_uri(registration.certificate_pdf.url),
            "created_at": registration.created_at.isoformat(),
        },
        status=201,
        json_dumps_params={"ensure_ascii": False},
    )



def download_certificate(request, pk):
    """Return the stored PDF binary as a downloadable file."""
    registration = get_object_or_404(Registration, pk=pk)
    if not registration.certificate_blob:
        raise Http404("Certificate not found.")
    filename = f"certificate_{registration.created_at:%Y%m%d%H%M%S}.pdf"
    response = HttpResponse(registration.certificate_blob, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

    """Delete the certificate from MEDIA_ROOT if the database save failed."""
    try:
        if registration.certificate_pdf:
            registration.certificate_pdf.delete(save=False)
    except Exception:
        logger.exception("Could not delete the orphan PDF after a failed save")


