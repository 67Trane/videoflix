from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin


class CustomUserAdmin(UserAdmin):
    """Custom admin configuration for the built-in User model.

    - Displays username, email, activation status, staff flag, and join date.
    - Provides filters for activation status and staff status.
    - Extends Django’s default UserAdmin.
    """
    list_display = ("username", "email", "is_active", "is_staff", "date_joined")
    list_filter = ("is_active", "is_staff")


# Replace the default User admin with the customized version
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
