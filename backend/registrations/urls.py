"""Registration app URLs."""

from django.urls import path

from . import views

urlpatterns = [
    path("registrations/", views.create_registration, name="registration-create"),
]
