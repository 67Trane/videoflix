from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator


def absolute_url(request, path: str) -> str:
    """Build an absolute URL from a relative path.

    Args:
        request (Request): DRF/Django request object (used to build domain + scheme).
        path (str): Relative URL path.

    Returns:
        str: Absolute URL including domain and scheme.
    """
    return request.build_absolute_uri(path)


def send_activation_email(user, request):
    """Send an account activation email to a user.

    - Generates a unique activation token tied to the user.
    - Builds an activation URL containing the token and user ID.
    - Sends a multi-part email (plain text + HTML) with the link.

    Args:
        user (User): The user instance to send the activation link to.
        request (Request): DRF/Django request object used for absolute URL generation.

    Returns:
        str: The generated activation token (useful for testing/debugging).
    """
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    # path = reverse("activate", kwargs={"uidb64": uidb64, "token": token})
    # activation_url = absolute_url(request, path)
    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:4200")
    activation_url = f"{frontend_url}/pages/auth/activate.html?uid={uidb64}&token={token}"
    filtered_username= user.username.split("@")[0]

    subject = "Activate your Videoflix account"
    text = (
        "Hi,\n\n"
        "Please confirm your registration by clicking the link below:\n"
        f"{activation_url}\n\n"
        "If you didn’t sign up for Videoflix, you can safely ignore this email."
    )
    html = f"""
    <div style="font-family: Arial, sans-serif; color: #fff; background-color:#0d0d0d; padding:20px; text-align:center;">
        <h2 style="color:#9147ff; margin-bottom:20px;">Welcome to Videoflix</h2>
        <p style="color:#ccc;">Dear {filtered_username}, <br> Please confirm your registration by clicking the button below:</p>
        <p>
        <a href="{activation_url}" 
            style="display:inline-block; padding:14px 28px;
                    background: linear-gradient(90deg, #9147ff, #4e9fff);
                    color:#fff; text-decoration:none; border-radius:8px;
                    font-weight:bold; font-family:Arial, sans-serif;">
            Activate Account
        </a>
        </p>
        <p style="color:#777; font-size:12px; margin-top:20px;">
        If you didn’t sign up for Videoflix, you can safely ignore this email.
        </p>
    </div>
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
    """Send a password reset email to a user.

    - Generates a password reset token tied to the user.
    - Builds a reset URL containing the token and user ID.
    - Sends a multi-part email (plain text + HTML) with the link.
    - The link is valid only for a limited time (token expiration).

    Args:
        user (User): The user instance requesting the reset.
        request (Request): DRF/Django request object used for absolute URL generation.

    Returns:
        None
    """
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    # path = reverse("password_confirm", kwargs={
    #                "uidb64": uidb64, "token": token})
    
    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:4200")
    reset_url = f"{frontend_url}/pages/auth/confirm_password.html?uid={uidb64}&token={token}"
    # reset_url = absolute_url(request, path)
    filtered_username= user.username.split("@")[0]
    print("asassssssssss")

    subject = "Reset your Videoflix password"
    text = (
        "Hi,\n\n"
        "We received a request to reset your password.\n"
        f"Click the link below (valid for a limited time):\n{reset_url}\n\n"
        "If you didn’t request this, you can safely ignore this email."
    )
    html = f"""
      <div style="font-family: Arial, sans-serif; color: #fff; background-color:#0d0d0d; padding:20px; text-align:center;">
    <h2 style="color:#9147ff; margin-bottom:20px;">Reset your Videoflix password</h2>
    <p style="color:#ccc;">Dear {filtered_username},<br>
       We received a request to reset your password.</p>
    <p>
        <a href="{reset_url}" 
           style="display:inline-block; padding:14px 28px;
                  background: linear-gradient(90deg, #9147ff, #4e9fff);
                  color:#fff; text-decoration:none; border-radius:8px;
                  font-weight:bold; font-family:Arial, sans-serif;">
           Reset Password
        </a>
    </p>
    <p style="color:#777; font-size:12px; margin-top:20px;">
       If you didn’t request this, you can safely ignore this email.
    </p>
</div>
    """

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        to=[user.email],
    )
    msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=True)
