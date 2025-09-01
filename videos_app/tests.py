import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from .tasks import convert_to_hls, extract_thumbnail, get_hls_dir
from types import SimpleNamespace
from pathlib import Path
import videos_app.tasks as tasks


@pytest.mark.django_db
def test_get_all_videos():
    client = APIClient()
    email = "test@test.com"
    password = "testpassword"
    User.objects.create_user(
        username=email, email=email, password=password, is_active=True
    )
    login_url = reverse("login")
    resp = client.post(
        login_url, {"email": email, "password": password}, format="json")

    access = resp.cookies["access_token"].value
    video_url = reverse("video-list")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    ok = client.get(video_url)
    assert ok.status_code == 200
    assert isinstance(ok.data, list)


def test_get_hls_dir(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    video = SimpleNamespace(video_file=SimpleNamespace(
        path=str(tmp_path / "videos" / "clip.mp4")))
    p = get_hls_dir(video, "720p")
    assert p == Path(tmp_path) / "videos" / "clip_hls_720p"


def test_convert_to_hls(monkeypatch, tmp_path):
    src = tmp_path / "movie.mp4"
    src.write_bytes(b"x")

    calls = []

    def fake_run(cmd, check=True):
        calls.append(cmd)

    monkeypatch.setattr(tasks.subprocess, "run", fake_run)

    out = tasks.convert_to_hls(str(src))

    assert Path(out).name == "index.m3u8"
    assert len(calls) == 3
