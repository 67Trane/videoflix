from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from ..models import Video
from .serializers import VideoSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.http import FileResponse, Http404
from ..tasks import get_hls_dir
from rest_framework.response import Response

import logging

logger = logging.getLogger(__name__)

from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        if header is not None:
            return super().authenticate(request)

        raw = request.COOKIES.get("access_token")
        if not raw:
            return None
        token = self.get_validated_token(raw)
        return self.get_user(token), token


class VideoListView(ListAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    authentication_classes = [CookieJWTAuthentication]
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
    authentication_classes = [CookieJWTAuthentication]

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
            open(playlist_path, "rb"), content_type="application/vnd.apple.mpegurl"
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

    authentication_classes = [CookieJWTAuthentication]
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
