"""URL configuration for the guests app."""
from django.urls import path

from . import views

app_name = "guests"

urlpatterns = [
    path("", views.GuestListView.as_view(), name="list"),
    path("<int:pk>/edit/", views.GuestUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.GuestDeleteView.as_view(), name="delete"),
    path(
        "<int:pk>/toggle-active/",
        views.GuestToggleActiveView.as_view(),
        name="toggle_active",
    ),
]
