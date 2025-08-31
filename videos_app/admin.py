from django.contrib import admin
from .models import Video


@admin.register(Video)
class Video(admin.ModelAdmin):
    """Admin configuration for the Video model.

    - Displays ID, title, category, and creation date in the list view.
    - Allows searching by title, description, and category.
    - Provides filters for category and creation date.
    """
    list_display = ("id", "title", "category", "created_at")
    search_fields = ("title", "description", "category")
    list_filter = ("category", "created_at")
