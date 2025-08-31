from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework import viewsets
from ..models import Video
from .serializers import VideoSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse, Http404
from ..tasks import get_hls_dir


class VideoListView(ListAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = ["get"]


class VideoMasterView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, movie_id: int, resolution: str):
        video = get_object_or_404(Video, pk=movie_id)

        try:
            hls_dir = get_hls_dir(video, resolution)
        except ValueError:
            raise Http404("resolution not aviable")
        playlist_path = hls_dir / "index.m3u8"

        if not playlist_path.exists():
            raise Http404("master not found")

        return FileResponse(
            open(playlist_path, "rb"), content_type="application/vnd.apple.mpegurl"
        )


class VideoSegmentView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id: int, resolution: str, segment: str):
        if "/" in segment or "\\" in segment:
            raise Http404("invalid segment")

        video = get_object_or_404(Video, pk=movie_id)

        try:
            hls_dir = get_hls_dir(video, resolution)
        except ValueError:
            raise Http404("resolution not aviable")

        segment_path = hls_dir / segment

        if not segment_path.exists():
            raise Http404("segment not found")

        return FileResponse(open(segment_path, "rb"), content_type="video/MP2T")
