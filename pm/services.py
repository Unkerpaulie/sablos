"""Service layer for the project management app.

Cross-aggregate queries and read-models for views live here so views
remain thin and models remain focused on per-instance behavior.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from django.db.models import Count, Prefetch, Q, QuerySet

from .models import Comment, Objective, Project


@dataclass(frozen=True)
class DashboardGroup:
    """A project together with its active objectives, ready for rendering."""

    project: Project
    objectives: list[Objective]


def objectives_with_comment_count() -> QuerySet[Objective]:
    """Base objective queryset annotated with ``comment_count``."""
    return Objective.objects.annotate(comment_count=Count("comments"))


def get_dashboard_groups() -> list[DashboardGroup]:
    """Return active projects with their open objectives.

    Only objectives whose status is ``Open`` (``IN_PROGRESS``) are
    surfaced on the dashboard; completed projects are excluded.
    """
    open_objectives = objectives_with_comment_count().filter(
        status=Objective.Status.IN_PROGRESS,
    )
    projects = (
        Project.objects.filter(is_completed=False)
        .select_related("client")
        .prefetch_related(
            Prefetch(
                "objectives",
                queryset=open_objectives,
                to_attr="active_objectives",
            )
        )
        .order_by("client__name", "name")
    )
    return [
        DashboardGroup(project=project, objectives=list(project.active_objectives))
        for project in projects
    ]


def list_projects_grouped_by_client() -> Iterable[tuple]:
    """Yield ``(client, [projects])`` tuples in display order."""
    from .models import Client  # local import to avoid cycles

    clients = Client.objects.prefetch_related(
        Prefetch(
            "projects",
            queryset=Project.objects.order_by("is_completed", "name"),
        )
    ).order_by("name")
    for client in clients:
        yield client, list(client.projects.all())


def search_comments(query: str | None) -> QuerySet[Comment]:
    qs = Comment.objects.select_related(
        "objective",
        "objective__project",
        "objective__project__client",
    )
    if query:
        qs = qs.filter(
            Q(body__icontains=query)
            | Q(objective__description__icontains=query)
            | Q(objective__project__name__icontains=query)
        )
    return qs.order_by("-created_at")
