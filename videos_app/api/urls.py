from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from .views import VideoListView, VideoMasterView, VideoSegmentView

urlpatterns = [
    path("video/", VideoListView.as_view(), name="video-list"),
    path(
        "video/<int:movie_id>/<str:resolution>/index.m3u8",
        VideoMasterView.as_view(),
        name="video-master",
    ),
    path(
        "video/<int:movie_id>/<str:resolution>/<str:segment>/",
        VideoSegmentView.as_view(),
        name="video-segment",
    ),
]
