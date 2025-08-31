from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from ..models import Video
from .serializers import VideoSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse, Http404
from ..tasks import get_hls_dir


class VideoListView(ListAPIView):
    """API endpoint that returns a list of all available videos.

    - Accessible only to authenticated users.
    - Uses JWT for authentication.
    """
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


class VideoMasterView(APIView):
    """API endpoint that serves the HLS master playlist (index.m3u8).

    Args:
        movie_id (int): ID of the video in the database.
        resolution (str): Target resolution (e.g. "480p", "720p", "1080p").

    Raises:
        Http404: If the resolution is invalid or the playlist file does not exist.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, movie_id: int, resolution: str):
        video = get_object_or_404(Video, pk=movie_id)

        try:
            hls_dir = get_hls_dir(video, resolution)
        except ValueError:
            raise Http404("resolution not available")

        playlist_path = hls_dir / "index.m3u8"
        if not playlist_path.exists():
            raise Http404("master not found")

        return FileResponse(
            open(playlist_path, "rb"),
            content_type="application/vnd.apple.mpegurl"
        )


class VideoSegmentView(APIView):
    """API endpoint that serves a single HLS video segment (.ts file).

    Args:
        movie_id (int): ID of the video in the database.
        resolution (str): Target resolution (e.g. "720p").
        segment (str): Segment filename (e.g. "seg_001.ts").

    Raises:
        Http404: If the segment name is invalid or the file does not exist.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id: int, resolution: str, segment: str):
        # Security check: prevent path traversal attempts like "../../"
        if "/" in segment or "\\" in segment:
            raise Http404("invalid segment")

        video = get_object_or_404(Video, pk=movie_id)

        try:
            hls_dir = get_hls_dir(video, resolution)
        except ValueError:
            raise Http404("resolution not available")

        segment_path = hls_dir / segment
        if not segment_path.exists():
            raise Http404("segment not found")

        return FileResponse(open(segment_path, "rb"), content_type="video/MP2T")
