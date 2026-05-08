"""URL configuration for the home app."""
from django.urls import path

from . import views

app_name = "home"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("say-hi/", views.ContactView.as_view(), name="contact"),
    path("guest-signup/", views.GuestSignUpView.as_view(), name="guest_signup"),
    path("deploy/github-webhook/", views.github_webhook, name="github_webhook"),
]
