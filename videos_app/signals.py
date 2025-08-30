from .models import Video
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
import os
from .tasks import convert_to_hls, extract_thumbnail
import django_rq
from pathlib import Path
from django.conf import settings


@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    thumb_rel = f"thumbnails/{instance.pk}.jpg"
    # thumb_tmp = Path(settings.MEDIA_ROOT) / "thumbnails" / f"{instance.pk}_frame.jpg"
    if created:
        queue = django_rq.get_queue("default", autocommit=True)
        queue.enqueue(convert_to_hls, instance.video_file.path)
        queue.enqueue(
            extract_thumbnail,
            instance.pk,
            str(instance.video_file.path),
            thumb_rel,
            second=2.0,
            max_width=480,
        )


@receiver(post_delete, sender=Video)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.video_file:
        if os.path.isfile(instance.video_file.path):
            os.remove(instance.video_file.path)
