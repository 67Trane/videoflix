from django.db import models
from django.utils.translation import gettext_lazy as _

class Video(models.Model):
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    title = models.CharField(_("Title"), max_length=200)
    description = models.TextField(_("Desciption"), blank=True)
    thumbnail_url = models.CharField(_("Thumbnail URL"), max_length=500, blank=True)
    category = models.CharField(_("Category"), max_length=50)
    
