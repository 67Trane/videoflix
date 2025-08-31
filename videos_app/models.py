from django.db import models
from django.utils.translation import gettext_lazy as _


class Video(models.Model):
    """Database model representing a video entry.

    Stores metadata (title, description, category), the uploaded video file,
    and an optional thumbnail image.
    """

    created_at = models.DateTimeField(
        _("Created at"),
        auto_now_add=True,
        help_text="Timestamp when the video entry was created."
    )
    title = models.CharField(
        _("Title"),
        max_length=200,
        help_text="Title of the video."
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        help_text="Optional detailed description of the video."
    )
    video_file = models.FileField(
        _("Video File"),
        upload_to="videos/",
        blank=True,
        null=True,
        help_text="Uploaded video file stored in the 'videos/' directory."
    )
    category = models.CharField(
        _("Category"),
        max_length=50,
        help_text="Category or genre of the video."
    )
    thumbnail_url = models.ImageField(
        _("Thumbnail"),
        upload_to="thumbnails/",
        blank=True,
        null=True,
        help_text="Optional thumbnail image stored in the 'thumbnails/' directory."
    )
