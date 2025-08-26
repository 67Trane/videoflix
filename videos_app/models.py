from django.db import models
from django.utils.translation import gettext_lazy as _

class Video(models.Model):
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    title = models.CharField(_("Title"), max_length=200)
    description = models.TextField(_("Desciption"), blank=True)
    video_file = models.FileField(_("Video File"),upload_to="videos/", blank=True, null=True)
    category = models.CharField(_("Category"), max_length=50)
    
