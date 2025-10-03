from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from ..models import Video
from ..tasks import get_hls_dir
from .serializers import VideoSerializer


class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that prefers the 'Authorization' header
    but falls back to reading the JWT from the 'access_token' cookie.

    Authentication order:
      1) If an Authorization header exists → use standard SimpleJWT authentication.
      2) Otherwise, try reading 'access_token' from cookies.
      3) If both are missing → no authentication (None), DRF will handle 401.
    """

    def authenticate(self, request):
        # Case 1: Authorization header present
        header = self.get_header(request)
        if header is not None:
            return super().authenticate(request)

        # Case 2: Fallback to cookie
        raw = request.COOKIES.get("access_token")
        if not raw:
            return None

        token = self.get_validated_token(raw)
        return self.get_user(token), token


class VideoListView(ListAPIView):
    """
    API endpoint that returns a list of all available videos.

    Requires authentication (JWT via header or 'access_token' cookie).
    """
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]


class VideoMasterView(APIView):
    """
    API endpoint that serves the HLS master playlist (index.m3u8)
    for a specific video at a given resolution.

    URL parameters:
      - movie_id (int): Primary key of the video.
      - resolution (str): Target resolution, e.g. "480p", "720p", "1080p".

    Raises:
      - Http404 if the resolution is invalid.
      - Http404 if the playlist file does not exist.
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

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
            playlist_path.open("rb"),
            content_type="application/vnd.apple.mpegurl",
        )


class VideoSegmentView(APIView):
    """
    API endpoint that serves a single HLS video segment (.ts file).

    URL parameters:
      - movie_id (int): Primary key of the video.
      - resolution (str): Target resolution, e.g. "720p".
      - segment (str): Segment filename, e.g. "seg_001.ts".

    Security:
      - Performs a basic path traversal check to prevent malicious input.

    Raises:
      - Http404 if the resolution is invalid.
      - Http404 if the segment does not exist or the name is invalid.
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id: int, resolution: str, segment: str):
        # Prevent directory traversal attempts
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

        return FileResponse(
            segment_path.open("rb"),
            content_type="video/MP2T",
        )
