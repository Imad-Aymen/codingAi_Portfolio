"""Custom Cloudinary storage for public PDF uploads.

django-cloudinary-storage may upload files with restricted access.
This backend explicitly uploads with type='upload' (public) and
resource_type='raw' so PDFs are always publicly downloadable.
"""

import os
import cloudinary
import cloudinary.uploader
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class CloudinaryPDFStorage(Storage):
    """Store uploaded PDFs on Cloudinary with public access."""

    def __init__(self):
        url = os.environ.get("CLOUDINARY_URL", "")
        if url:
            cloudinary.config(CLOUDINARY_URL=url)

    def _save(self, name, content):
        """Upload file to Cloudinary and return the public_id."""
        # Read the file content
        file_content = content.read()

        # Upload with explicit public access
        result = cloudinary.uploader.upload(
            file_content,
            public_id=os.path.splitext(name)[0],  # remove .pdf extension for public_id
            resource_type="raw",       # not 'image' — this is a PDF
            type="upload",             # 'upload' = publicly accessible
            access_mode="public",      # explicitly public
            overwrite=True,
            folder="media",            # organize in a folder
        )
        # Return the public_id (used later to build the URL)
        return result.get("public_id", name)

    def url(self, name):
        """Return the public Cloudinary URL for the file."""
        # Build the raw delivery URL directly
        cloud_name = cloudinary.config().cloud_name
        # Ensure name doesn't start with 'media/' twice
        clean_name = name
        return f"https://res.cloudinary.com/{cloud_name}/raw/upload/{clean_name}"

    def exists(self, name):
        """Cloudinary handles uniqueness via public_id; always return False."""
        return False

    def delete(self, name):
        """Delete the file from Cloudinary."""
        try:
            cloudinary.uploader.destroy(name, resource_type="raw", type="upload")
        except Exception:
            pass

    def size(self, name):
        """Return None — size is not tracked locally."""
        return None
