"""Models for the home (public) site."""
from __future__ import annotations

from django.db import models


class ContactMessage(models.Model):
    """A submission from the public contact form."""

    name = models.CharField(max_length=120)
    email = models.EmailField()
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Message from {self.name} ({self.created_at:%Y-%m-%d})"

    def mark_read(self) -> None:
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=["is_read"])

    def mark_unread(self) -> None:
        if self.is_read:
            self.is_read = False
            self.save(update_fields=["is_read"])
