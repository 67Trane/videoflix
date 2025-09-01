import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient

@pytest.mark.django_db
def test_get_all_videos():
    client = APIClient()
    email = "test@test.com"
    password = "testpassword"
    User.objects.create_user(
        username=email, email=email, password=password, is_active=True
    )
    login_url = reverse("login")
    resp = client.post(login_url, {"email": email, "password": password}, format="json")

    access = resp.cookies["access_token"].value
    video_url = reverse("video-list")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    ok = client.get(video_url)
    assert ok.status_code == 200
    assert isinstance(ok.data, list)
