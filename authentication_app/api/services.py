from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator


def absolute_url(request, path: str) -> str:
    return request.build_absolute_uri(path)


def send_activation_email(user, request):
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    path = reverse("activate", kwargs={"uidb64": uidb64, "token": token})
    activation_url = absolute_url(request, path)

    subject = "Activate your Videoflix account"
    text = (
        "Hi,\n\n"
        "Please confirm your registration by clicking the link below:\n"
        f"{activation_url}\n\n"
        "If you didn’t sign up for Videoflix, you can safely ignore this email."
    )
    html = f"""
      <p>Hi,</p>
      <p>Please confirm your registration by clicking the link below:</p>
      <p><a href="{activation_url}">{activation_url}</a></p>
      <p>If you didn’t sign up for Videoflix, you can safely ignore this email.</p>
    """

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        to=[user.email],
    )
    msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=False)
    return token


def send_password_reset_email(user, request):
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    path = reverse("password_confirm", kwargs={
                   "uidb64": uidb64, "token": token})
    reset_url = absolute_url(request, path)

    subject = "Reset your VideoFlix password"
    text = (
        "Hi,\n\n"
        "We received a request to reset your password.\n"
        f"Click the link below (valid for a limited time):\n{reset_url}\n\n"
        "If you didn’t request this, you can safely ignore this email."
    )
    html = f"""
      <p>Hi,</p>
      <p>We received a request to reset your password.</p>
      <p>Click the link below (valid for a limited time):<br>
         <a href="{reset_url}">{reset_url}</a></p>
      <p>If you didn’t request this, you can safely ignore this email.</p>
    """
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        to=[user.email],
    )
    msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=True)
