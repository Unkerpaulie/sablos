"""Views for managing guest (non-staff) user accounts."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DeleteView, ListView, UpdateView

from pm.mixins import StaffLoginRequiredMixin

from .forms import GuestForm

User = get_user_model()


def guest_queryset():
    """All non-staff, non-superuser accounts, newest first."""
    return (
        User.objects.filter(is_staff=False, is_superuser=False)
        .order_by("-date_joined")
    )


class GuestListView(StaffLoginRequiredMixin, ListView):
    template_name = "guests/list.html"
    context_object_name = "guests"

    def get_queryset(self):
        return guest_queryset()


class GuestUpdateView(StaffLoginRequiredMixin, UpdateView):
    template_name = "guests/form.html"
    form_class = GuestForm
    success_url = reverse_lazy("guests:list")

    def get_queryset(self):
        return guest_queryset()

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Updated {self.object.username}.")
        return response


class GuestDeleteView(StaffLoginRequiredMixin, DeleteView):
    template_name = "guests/confirm_delete.html"
    success_url = reverse_lazy("guests:list")
    context_object_name = "guest"

    def get_queryset(self):
        return guest_queryset()

    def form_valid(self, form):
        username = self.get_object().username
        response = super().form_valid(form)
        messages.success(self.request, f"Deleted {username}.")
        return response


class GuestToggleActiveView(StaffLoginRequiredMixin, View):
    """POST-only toggle for is_active."""

    def post(self, request, pk):
        guest = get_object_or_404(guest_queryset(), pk=pk)
        guest.is_active = not guest.is_active
        guest.save(update_fields=["is_active"])
        messages.success(
            request,
            f"{guest.username} {'activated' if guest.is_active else 'deactivated'}.",
        )
        return redirect("guests:list")
