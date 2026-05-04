"""Admin registrations for the pm app."""
from django.contrib import admin

from .models import Client, Comment, Objective, Project


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "client", "is_completed", "created_at")
    list_filter = ("is_completed", "client")
    search_fields = ("name", "client__name")
    autocomplete_fields = ("client",)


@admin.register(Objective)
class ObjectiveAdmin(admin.ModelAdmin):
    list_display = ("short_description", "project", "status", "priority", "due_date")
    list_filter = ("status", "priority", "project")
    search_fields = ("description", "project__name")
    autocomplete_fields = ("project",)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("objective", "created_at")
    search_fields = ("body", "objective__description")
    autocomplete_fields = ("objective",)
