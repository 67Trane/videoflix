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

# Tests for auth and email flows:
# - login, registration, logout, refresh
# - activation and password reset email content
# Keep assertions tight and user-facing messages stable.


@pytest.mark.django_db
def test_login():
    """Successful login sets JWT cookies and returns 200."""
    client = APIClient()

    email = "test@test.com"
    password = "testpassword"
    User.objects.create_user(
        username=email, email=email, password=password, is_active=True
    )

    login_url = reverse("login")
    resp = client.post(login_url, {"email": email, "password": password}, format="json")

    assert resp.status_code == 200, resp.data
    assert "access_token" in resp.cookies, "Login didnt set access_token cookie"


@pytest.mark.django_db
def test_send_activation_email(settings):
    """Activation email is sent and contains uidb64 + token."""
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.DEFAULT_FROM_EMAIL = "noreply@videoflix.test"

    email = "test@test.com"
    password = "testpassword"
    user = User.objects.create_user(
        username=email, email=email, password=password, is_active=True
    )

    rf = RequestFactory()
    request = rf.get("/", secure=True)

    token = send_activation_email(user, request)
    assert token and isinstance(token, str)

    assert len(mail.outbox) == 1
    msg = mail.outbox[0]
    assert email in msg.to

    # Search both text and HTML bodies
    body = msg.body
    if msg.alternatives:
        body += "\n" + msg.alternatives[0][0]

    # The activation URL should include the correct uidb64 and token
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    assert f"/activate/{uidb64}/" in body
    assert token in body


@pytest.mark.django_db
def test_registration():
    """Registration returns 201, echoes user email, and persists the user."""
    client = APIClient()
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

    email = "test@test.com"
    password = "testpassword"

    register_url = reverse("registration")
    resp = client.post(
        register_url,
        {"email": email, "password": password, "confirmed_password": password},
        format="json",
    )

    assert resp.status_code == 201, resp.data
    assert "user" in resp.data and "token" in resp.data
    assert resp.data["user"]["email"] == email
    assert User.objects.filter(email=email).exists()


@pytest.mark.django_db
def test_logout():
    """Logout blacklists refresh token and returns 200."""
    client = APIClient()

    email = "test@test.com"
    password = "testpassword"
    User.objects.create_user(username=email, email=email, password=password, is_active=True)

    login_url = reverse("login")
    login_resp = client.post(
        login_url, {"email": email, "password": password, "confirmed_password": password}, format="json"
    )
    assert login_resp.status_code == 200, login_resp.data
    assert "refresh_token" in login_resp.cookies
    assert "access_token" in login_resp.cookies

    logout_url = reverse("logout")
    out = client.post(logout_url)
    assert out.status_code == 200, getattr(out, "data", out)


@pytest.mark.django_db
def test_logout_missing_cookie_returns_400():
    """Logout without refresh cookie returns 400 with detail message."""
    client = APIClient()
    resp = client.post(reverse("logout"))
    assert resp.status_code == 400
    assert "detail" in resp.data
    assert "Refresh-Token" in resp.data["detail"]


@pytest.mark.django_db
def test_logout_with_invalid_refresh_returns_400():
    """Logout with malformed/invalid refresh cookie returns 400."""
    client = APIClient()
    client.cookies["refresh_token"] = "bogus.invalid.refresh"
    resp = client.post(reverse("logout"))
    assert resp.status_code == 400
    assert "detail" in resp.data


@pytest.mark.django_db
def test_refresh_without_cookie_returns_400():
    """Token refresh without refresh cookie returns 400 with explicit message."""
    client = APIClient()
    url = reverse("token_refresh")
    resp = client.post(url)
    assert resp.status_code == 400
    assert resp.data["detail"] == "Refresh token not found!"


@pytest.mark.django_db
def test_refresh_with_valid_cookie():
    """Token refresh with a valid refresh cookie returns new access token and sets cookie."""
    client = APIClient()

    email = "test@test.com"
    password = "testpassword"
    User.objects.create_user(username=email, email=email, password=password, is_active=True)

    login_resp = client.post(
        reverse("login"), {"email": email, "password": password}, format="json"
    )
    assert login_resp.status_code == 200, login_resp.data
    assert "refresh_token" in login_resp.cookies, "Login didnt set fresh_token cookie"
    assert "access_token" in login_resp.cookies, "Login didnt set access_token cookie"

    old_access_cookie = login_resp.cookies["access_token"].value
    refresh_cookie = login_resp.cookies["refresh_token"].value

    # Simulate browser sending the refresh cookie
    client.cookies["refresh_token"] = refresh_cookie

    refresh_url = reverse("token_refresh")
    resp = client.post(refresh_url)
    assert resp.status_code == 200, getattr(resp, "data", resp)
    assert "detail" in resp.data and resp.data["detail"] == "Token refreshed"
    assert "access" in resp.data
    assert "access_token" in resp.cookies

    new_access_cookie = resp.cookies["access_token"].value
    # Sanity check: JWTs have 2 dots (3 parts), and should rotate
    assert new_access_cookie.count(".") == 2
    assert new_access_cookie != old_access_cookie
