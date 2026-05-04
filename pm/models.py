"""Domain models for the project management system.

Business rules and derived state belong on the model where reasonable;
cross-aggregate queries live in :mod:`pm.services`.
"""
from __future__ import annotations

from django.db import models
from django.urls import reverse

from core.fields import MarkdownField


class ProjectQuerySet(models.QuerySet):
    """Project queryset honoring per-user visibility."""

    def visible_to(self, user) -> "ProjectQuerySet":
        if getattr(user, "is_staff", False):
            return self
        return self.filter(is_hidden=False)


class ObjectiveQuerySet(models.QuerySet):
    def visible_to(self, user) -> "ObjectiveQuerySet":
        if getattr(user, "is_staff", False):
            return self
        return self.filter(project__is_hidden=False)


class CommentQuerySet(models.QuerySet):
    def visible_to(self, user) -> "CommentQuerySet":
        if getattr(user, "is_staff", False):
            return self
        return self.filter(objective__project__is_hidden=False)


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Client(TimestampedModel):
    name = models.CharField(max_length=200, unique=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    notes = MarkdownField(blank=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("pm:client_detail", args=[self.pk])


class Project(TimestampedModel):
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    name = models.CharField(max_length=200)
    init_prompt = MarkdownField(
        blank=True,
        hint="Initial brief / prompt for the project.",
    )
    repo_link = models.URLField(blank=True)
    launch_domain = models.CharField(max_length=255, blank=True)
    launch_specs = MarkdownField(
        blank=True,
        hint="Launch specifications.",
    )
    is_completed = models.BooleanField(default=False)
    is_hidden = models.BooleanField(
        default=False,
        help_text="Hide this project (and everything inside it) from guest users.",
    )

    objects = ProjectQuerySet.as_manager()

    class Meta:
        ordering = ("client__name", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("client", "name"),
                name="unique_project_per_client",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.client.name} – {self.name}"

    def get_absolute_url(self) -> str:
        return reverse("pm:project_detail", args=[self.pk])

    def mark_completed(self) -> None:
        self.is_completed = True
        self.save(update_fields=["is_completed", "updated_at"])

    def reopen(self) -> None:
        self.is_completed = False
        self.save(update_fields=["is_completed", "updated_at"])


class Objective(TimestampedModel):
    class Status(models.TextChoices):
        TODO = "todo", "Future"
        IN_PROGRESS = "in_progress", "Open"
        BLOCKED = "blocked", "Backlog"
        DONE = "done", "Closed"

    class Priority(models.IntegerChoices):
        HIGH = 1, "High"
        MEDIUM = 2, "Medium"
        LOW = 3, "Low"

    SHORT_DESCRIPTION_LENGTH = 50

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="objectives",
    )
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TODO,
    )
    priority = models.PositiveSmallIntegerField(
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    due_date = models.DateField(null=True, blank=True)

    objects = ObjectiveQuerySet.as_manager()

    class Meta:
        ordering = ("priority", "due_date", "-created_at")

    def __str__(self) -> str:
        return self.short_description or f"Objective #{self.pk}"

    def get_absolute_url(self) -> str:
        return reverse("pm:objective_detail", args=[self.pk])

    @property
    def short_description(self) -> str:
        text = (self.description or "").strip().replace("\n", " ")
        limit = self.SHORT_DESCRIPTION_LENGTH
        if len(text) <= limit:
            return text
        return text[: limit - 1].rstrip() + "…"

    @property
    def is_done(self) -> bool:
        return self.status == self.Status.DONE


class Comment(TimestampedModel):
    objective = models.ForeignKey(
        Objective,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    body = MarkdownField()

    objects = CommentQuerySet.as_manager()

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Comment on {self.objective_id} @ {self.created_at:%Y-%m-%d %H:%M}"

    def get_absolute_url(self) -> str:
        return self.objective.get_absolute_url()
