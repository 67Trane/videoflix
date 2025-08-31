from rest_framework import serializers
from ..models import Video


class VideoSerializer(serializers.ModelSerializer):
    """Serializer for the Video model.

    Converts Video instances into JSON and validates incoming data
    when creating or updating videos.
    """

    class Meta:
        model = Video
        fields = [
            "id",
            "title",
            "description",
            "thumbnail_url",
            "category",
            "created_at",
        ]
