from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from .views import VideoListView, VideoMasterView, VideoSegmentView

# URL routing for video-related API endpoints (HLS streaming).
urlpatterns = [
    # Returns a list of all available videos (JSON response).
    path("video/", VideoListView.as_view(), name="video-list"),
    # Returns the HLS master playlist (index.m3u8) for a given video and resolution.
    path(
        "video/<int:movie_id>/<str:resolution>/index.m3u8",
        VideoMasterView.as_view(),
        name="video-master",
    ),
    # Returns a single HLS segment (.ts file) for a given video and resolution.
    path(
        "video/<int:movie_id>/<str:resolution>/<str:segment>/",
        VideoSegmentView.as_view(),
        name="video-segment",
    ),
]
