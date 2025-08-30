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
    permission_classes = [AllowAny]
    http_method_names = ["get"]


class VideoMasterView(APIView):
    # authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, movie_id: int, resolution: str):
        video = get_object_or_404(Video, pk=movie_id)

        try:
            hls_dir = get_hls_dir(video, resolution)
        except ValueError:
            raise Http404("resolution not aviable")
        print("hls pfad ist", hls_dir)
        playlist_path = hls_dir / "index.m3u8"
        print("master pfad ist", playlist_path)

        if not playlist_path.exists():
            raise Http404("master not found")

        return FileResponse(open(playlist_path, "rb"), content_type="application/vnd.apple.mpegurl")


class VideoSegmentView(APIView):
    permission_classes = [AllowAny]
    