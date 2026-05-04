"""URL configuration for the pm app."""
from django.urls import path

from . import views

app_name = "pm"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),

    # Clients
    path("clients/", views.ClientListView.as_view(), name="client_list"),
    path("clients/new/", views.ClientCreateView.as_view(), name="client_create"),
    path("clients/<int:pk>/", views.ClientDetailView.as_view(), name="client_detail"),
    path("clients/<int:pk>/edit/", views.ClientUpdateView.as_view(), name="client_update"),
    path("clients/<int:pk>/delete/", views.ClientDeleteView.as_view(), name="client_delete"),

    # Projects
    path("projects/", views.ProjectListView.as_view(), name="project_list"),
    path("projects/new/", views.ProjectCreateView.as_view(), name="project_create"),
    path("projects/<int:pk>/", views.ProjectDetailView.as_view(), name="project_detail"),
    path("projects/<int:pk>/edit/", views.ProjectUpdateView.as_view(), name="project_update"),
    path("projects/<int:pk>/delete/", views.ProjectDeleteView.as_view(), name="project_delete"),

    # Objectives
    path("objectives/new/", views.ObjectiveCreateView.as_view(), name="objective_create"),
    path("objectives/<int:pk>/", views.ObjectiveDetailView.as_view(), name="objective_detail"),
    path("objectives/<int:pk>/edit/", views.ObjectiveUpdateView.as_view(), name="objective_update"),
    path("objectives/<int:pk>/delete/", views.ObjectiveDeleteView.as_view(), name="objective_delete"),

    # Comments
    path("comments/", views.CommentListView.as_view(), name="comment_list"),
    path("comments/<int:pk>/delete/", views.CommentDeleteView.as_view(), name="comment_delete"),

    # Messages (contact form inbox)
    path("messages/", views.MessageListView.as_view(), name="message_list"),
    path(
        "messages/<int:pk>/toggle-read/",
        views.MessageToggleReadView.as_view(),
        name="message_toggle_read",
    ),
]
