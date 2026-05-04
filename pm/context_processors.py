"""Template context processors for the pm app.

Surfaces small pieces of cross-cutting state (e.g. unread message count)
on every dashboard render so they don't have to be added to each view.
"""
from __future__ import annotations

from home.models import ContactMessage


def unread_messages(request):
    """Expose the number of unread contact messages to staff users."""
    user = getattr(request, "user", None)
    if not (user and user.is_authenticated and user.is_staff):
        return {}
    count = ContactMessage.objects.filter(is_read=False).count()
    return {"unread_messages_count": count}
