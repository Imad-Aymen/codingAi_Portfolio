"""Root URL configuration."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import render
from django.urls import include, path


def index(request):
    return render(request, "index.html")


urlpatterns = [
    path("", index, name="index"),           # الصفحة الرئيسية
    path("admin/", admin.site.urls),          # Django Dashboard
    path("api/", include("registrations.urls")),  # API
]

# Serve media files (PDFs) during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
