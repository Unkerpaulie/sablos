"""Reusable view mixins for the pm app."""
from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin


class StaffLoginRequiredMixin(LoginRequiredMixin):
    """Require an authenticated, staff user.

    The pm system is private to staff for now; non-staff read access is
    a planned future addition (see project brief).
    """

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_staff:
            from django.core.exceptions import PermissionDenied

            raise PermissionDenied("Staff access required.")
        return super().dispatch(request, *args, **kwargs)
