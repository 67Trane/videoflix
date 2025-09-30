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
    filtered_username = user.username.split("@")[0]

    subject = "Activate your Videoflix account"
    text = (
        f"Dear {filtered_username},\n\n"
        "Thank you for registering with Videoflix. To complete your registration and verify your email address, "
        "please click the link below:\n\n"
        f"{activation_url}\n\n"
        "If you did not create an account with us, please disregard this email.\n\n"
        "Best regards,\nYour Videoflix Team"
    )

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>{subject}</title>
    </head>
    <body style="margin:0; padding:0; background:#f5f6f8;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#f5f6f8;">
        <tr>
        <td align="center" style="padding:32px 16px;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width:640px; background:#ffffff; border-radius:12px; box-shadow:0 1px 2px rgba(16,24,40,.04);">
            <!-- Wordmark header (no image) -->
            <tr>
                <td align="center" style="padding:28px 24px 8px 24px;">
                <span style="display:inline-block; width:0; height:0; 
                            border-left:16px solid #6c4df5; 
                            border-top:10px solid transparent; 
                            border-bottom:10px solid transparent; 
                            margin-right:8px; vertical-align:-2px;"></span>
                <span style="font:700 24px/1 Arial,Helvetica,sans-serif; color:#6c4df5; letter-spacing:.6px;">
                    VIDEOFLIX
                </span>
                </td>
            </tr>

            <tr>
                <td style="padding:8px 24px 0 24px; font:14px/22px Arial,Helvetica,sans-serif; color:#111827;">
                <p style="margin:0 0 14px 0;">Dear {filtered_username},</p>
                <p style="margin:0 0 20px 0; color:#374151;">
                    Thank you for registering with <strong>Videoflix</strong>. To complete your registration and verify your email address, please click the button below:
                </p>
                </td>
            </tr>

            <tr>
                <td align="left" style="padding:0 24px 12px 24px;">
                <a href="{activation_url}"
                    style="display:inline-block; padding:12px 22px; background:#1a73e8; color:#ffffff; text-decoration:none; font:700 14px/14px Arial,Helvetica,sans-serif; border-radius:9999px;">
                    Activate account
                </a>
                </td>
            </tr>

            <tr>
                <td style="padding:4px 24px 8px 24px; font:13px/20px Arial,Helvetica,sans-serif; color:#6b7280;">
                <p style="margin:0 0 18px 0;">
                    If you did not create an account with us, please disregard this email.
                </p>
                <p style="margin:0 0 4px 0; color:#374151;">Best regards,</p>
                <p style="margin:0 0 22px 0; color:#374151;">Your Videoflix Team</p>
                </td>
            </tr>
            </table>

            <div style="max-width:640px; margin:12px auto 0; font:11px/16px Arial,Helvetica,sans-serif; color:#9ca3af;">
            © Videoflix — This is an automated message.
            </div>
        </td>
        </tr>
    </table>
    </body>
    </html>
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
    filtered_username = user.username.split("@")[0]

    subject = "Reset your Videoflix password"
    text = (
        "Hello,\n\n"
        "We recently received a request to reset your password. If you made this request, "
        "please click the link below to reset your password:\n\n"
        f"{reset_url}\n\n"
        f"Please note: for security reasons, this link is only valid for about 24 hours.\n\n"
        "If you did not request a password reset, please ignore this email.\n\n"
        "Best regards,\nYour Videoflix team"
    )

    html = f"""
      <!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width,initial-scale=1" />
        <title>{subject}</title>
        </head>
        <body style="margin:0; padding:0; background:#f5f6f8;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#f5f6f8;">
            <tr>
            <td align="center" style="padding:32px 16px;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width:640px; background:#ffffff; border-radius:12px; box-shadow:0 1px 2px rgba(16,24,40,.04);">
                <tr>
                    <td style="padding:24px; font:14px/22px Arial,Helvetica,sans-serif; color:#111827;">
                    <h1 style="margin:0 0 12px 0; font:600 20px/1.3 Arial,Helvetica,sans-serif; color:#111827;">Reset your Password</h1>

                    <p style="margin:0 0 16px 0; color:#374151;">
                        Hello, {filtered_username}
                    </p>
                    <p style="margin:0 0 20px 0; color:#374151;">
                        We recently received a request to reset your password. If you made this request,
                        please click the button below to reset your password:
                    </p>

                    <p style="margin:0 0 22px 0;">
                        <a href="{reset_url}"
                        style="display:inline-block; padding:12px 22px; background:#1a73e8; color:#ffffff; text-decoration:none; font:700 14px/14px Arial,Helvetica,sans-serif; border-radius:9999px;">
                        Reset password
                        </a>
                    </p>

                    <p style="margin:0 0 12px 0; color:#6b7280;">
                        Please note that for security reasons, this link is only valid for about 24 hours.
                    </p>
                    <p style="margin:0 0 20px 0; color:#6b7280;">
                        If you did not request a password reset, please ignore this email.
                    </p>

                    <p style="margin:0; color:#374151;">Best regards,<br/>Your Videoflix team!</p>
                    </td>
                </tr>

                <!-- Wortmarke ohne Bild, unten wie im Screenshot -->
                <tr>
                    <td align="left" style="padding:8px 24px 28px 24px;">
                    <span style="display:inline-block; width:0; height:0;
                                border-left:16px solid #6c4df5;
                                border-top:10px solid transparent;
                                border-bottom:10px solid transparent;
                                vertical-align:-2px; margin-right:8px;"></span>
                    <span style="font:700 24px/1 Arial,Helvetica,sans-serif; color:#6c4df5; letter-spacing:.6px;">
                        VIDEOFLIX
                    </span>
                    </td>
                </tr>
                </table>

                <div style="max-width:640px; margin:12px auto 0; font:11px/16px Arial,Helvetica,sans-serif; color:#9ca3af;">
                © Videoflix — This is an automated message.
                </div>
            </td>
            </tr>
        </table>
        </body>
        </html>
    """

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        to=[user.email],
    )
    msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=True)
