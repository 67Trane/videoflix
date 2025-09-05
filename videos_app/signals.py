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
    """Signal handler that runs after a Video instance is saved.

    - On creation of a new Video:
      * Enqueues a background job to convert the uploaded file into HLS format.
      * Enqueues a background job to generate a thumbnail image.

    Args:
        sender (Model): The model class (Video).
        instance (Video): The actual saved Video instance.
        created (bool): True if a new object was created, False if updated.
        **kwargs: Additional arguments passed by the signal.
    """
    thumb_rel = f"thumbnails/{instance.pk}.jpg"

    if created:
        # Use RQ (Redis Queue) to process tasks asynchronously in the background.
        queue = django_rq.get_queue("default", autocommit=True)

        # Enqueue HLS video conversion
        queue.enqueue(convert_to_hls, instance.video_file.path)

        # Only extract a thumbnail if the user did not upload one
        if not instance.thumbnail_url:
            # Enqueue thumbnail extraction
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
    """Signal handler that deletes associated media files
    when a Video instance is removed.

    - Deletes the original video file.
    - Deletes the thumbnail image (if it exists).

    Args:
        sender (Model): The model class (Video).
        instance (Video): The deleted Video instance.
        **kwargs: Additional arguments passed by the signal.
    """
    # Delete video file if it exists
    if instance.video_file and os.path.isfile(instance.video_file.path):
        os.remove(instance.video_file.path)

    # Delete thumbnail file if it exists
    if instance.thumbnail_url and os.path.isfile(instance.thumbnail_url.path):
        os.remove(instance.thumbnail_url.path)
