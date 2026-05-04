"""Public-facing views for the home site."""
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from .forms import ContactForm, GuestSignUpForm


class IndexView(TemplateView):
    template_name = "pages/home.html"


class ContactView(FormView):
    template_name = "pages/contact.html"
    form_class = ContactForm
    success_url = reverse_lazy("home:contact")

    def form_valid(self, form: ContactForm):
        form.save()
        messages.success(
            self.request,
            "Thanks for reaching out. I'll get back to you soon.",
        )
        return super().form_valid(form)


class GuestSignUpView(FormView):
    """Self-service registration that creates non-staff guest accounts.

    The URL is unlinked from the public site; it's intended to be shared
    privately. Already-authenticated users are sent to the dashboard.
    """

    template_name = "registration/guest_signup.html"
    form_class = GuestSignUpForm
    success_url = reverse_lazy("pm:dashboard")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("pm:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: GuestSignUpForm):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, f"Welcome, {user.username}.")
        return super().form_valid(form)
