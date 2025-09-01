import pytest
from django.contrib.auth.models import User
from django.core import mail
from django.test import RequestFactory
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from core import settings
from .api.services import send_activation_email
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_login():
    client = APIClient()

    email = "test@test.com"
    password = "testpassword"
    User.objects.create_user(
        username=email, email=email, password=password, is_active=True
    )

    login_url = reverse("login")
    resp = client.post(
        login_url, {"email": email, "password": password}, format="json")

    assert resp.status_code == 200, resp.data
    assert "access_token" in resp.cookies, "Login didnt set access_token cookie"


@pytest.mark.django_db
def test_send_activation_email_builds_absolute_link_and_sends_mail(settings):

    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.DEFAULT_FROM_EMAIL = "noreply@videoflix.test"

    email = "test@test.com"
    password = "testpassword"
    user = User.objects.create_user(
        username=email, email=email, password=password, is_active=True)

    rf = RequestFactory()
    request = rf.get("/", secure=True)

    token = send_activation_email(user, request)
    assert token and isinstance(token, str)

    assert len(mail.outbox) == 1
    msg = mail.outbox[0]
    assert email in msg.to

    body = msg.body
    if msg.alternatives:
        body += "\n" + msg.alternatives[0][0]

    # The activation URL should include the correct uidb64 and token
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    assert f"/activate/{uidb64}/" in body
    assert token in body


@pytest.mark.django_db
def test_registration():
    client = APIClient()
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

    email = "test@test.com"
    password = "testpassword"

    register_url = reverse("registration")
    resp = client.post(register_url, {"email": email, "password": password, "confirmed_password": password}, format="json")
    
    assert resp.status_code == 201, resp.data
    assert "user" in resp.data and "token" in resp.data
    assert resp.data["user"]["email"] == email
    assert User.objects.filter(email=email).exists()

@pytest.mark.django_db
def test_logout():
    client = APIClient()
    
    email = "test@test.com"
    password = "testpassword"
    User.objects.create_user(username=email, email=email, password=password, is_active=True)
    login_url = reverse("login")
    login_resp = client.post(login_url, {"email": email, "password": password, "confirmed_password": password}, format="json")
    assert login_resp.status_code == 200, login_resp.data
    assert "refresh_token" in login_resp.cookies
    assert "access_token" in login_resp.cookies
    
    
    logout_url = reverse("logout")
    out= client.post(logout_url)
    assert out.status_code == 200, getattr(out, "data", out)
    
    
@pytest.mark.django_db
def test_logout_missing_cookie_returns_400():
    client = APIClient()
    resp = client.post(reverse("logout"))
    assert resp.status_code == 400
    assert "detail" in resp.data
    assert "Refresh-Token" in resp.data["detail"]


@pytest.mark.django_db
def test_logout_with_invalid_refresh_returns_400():
    client = APIClient()
    client.cookies["refresh_token"] = "bogus.invalid.refresh"
    resp = client.post(reverse("logout"))
    assert resp.status_code == 400
    assert "detail" in resp.data