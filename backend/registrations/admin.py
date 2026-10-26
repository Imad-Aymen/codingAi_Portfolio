"""Admin configuration for the registrations app."""

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Registration


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "department", "school_year", "created_at", "pdf_link")
    list_filter = ("school_year", "created_at")
    search_fields = ("full_name", "email", "department")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "pdf_link")

    def pdf_link(self, obj):
        """Show a clickable download link for the certificate PDF stored in the database."""
        if obj.certificate_blob:
            url = reverse("certificate-download", args=[obj.pk])
            return format_html(
                '<a href="{}" target="_blank">📄 تحميل PDF</a>',
                url,
            )
        return "—"

    pdf_link.short_description = "شهادة PDF"
