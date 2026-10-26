"""Registration app URLs."""

from django.urls import path

from . import views

urlpatterns = [
    path("registrations/", views.create_registration, name="registration-create"),
    path("registrations/<int:pk>/download/", views.download_certificate, name="certificate-download"),
]
