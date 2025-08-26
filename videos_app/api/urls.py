from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from .views import VideoListView

urlpatterns = [
    path("video/", VideoListView.as_view(), name="video-list"),
]
