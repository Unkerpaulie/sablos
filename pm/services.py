"""Service layer for the project management app.

Cross-aggregate queries and read-models for views live here so views
remain thin and models remain focused on per-instance behavior.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from django.db.models import Case, Count, IntegerField, Prefetch, Q, QuerySet, Value, When

from .models import Comment, Objective, Project


@dataclass(frozen=True)
class DashboardGroup:
    """A project together with its active objectives, ready for rendering."""

    project: Project
    objectives: list[Objective]


def objectives_with_comment_count(user=None) -> QuerySet[Objective]:
    """Base objective queryset annotated with ``comment_count``.

    When ``user`` is provided, the queryset is filtered to objectives
    belonging to projects visible to that user.
    """
    qs = Objective.objects.annotate(comment_count=Count("comments"))
    if user is not None:
        qs = qs.visible_to(user)
    return qs


def get_dashboard_groups(user) -> list[DashboardGroup]:
    """Return active projects with their non-done objectives.

    Open (IN_PROGRESS) objectives appear first, followed by Future (TODO)
    then Backlog (BLOCKED). Closed objectives and completed/hidden projects
    are excluded entirely.
    """
    _status_order = Case(
        When(status=Objective.Status.IN_PROGRESS, then=Value(0)),
        When(status=Objective.Status.TODO, then=Value(1)),
        When(status=Objective.Status.BLOCKED, then=Value(2)),
        default=Value(3),
        output_field=IntegerField(),
    )
    non_done_objectives = (
        objectives_with_comment_count(user)
        .exclude(status=Objective.Status.DONE)
        .annotate(_status_order=_status_order)
        .order_by("_status_order", "priority", "due_date")
    )
    projects = (
        Project.objects.visible_to(user)
        .filter(is_completed=False)
        .select_related("client")
        .prefetch_related(
            Prefetch(
                "objectives",
                queryset=non_done_objectives,
                to_attr="active_objectives",
            )
        )
        .order_by("client__name", "name")
    )
    return [
        DashboardGroup(project=project, objectives=list(project.active_objectives))
        for project in projects
        if project.active_objectives
    ]


def list_projects_grouped_by_client(user) -> Iterable[tuple]:
    """Yield ``(client, [projects])`` tuples in display order.

    Clients with no projects visible to ``user`` are omitted.
    """
    from .models import Client  # local import to avoid cycles

    visible_projects = Project.objects.visible_to(user)
    clients = (
        Client.objects.filter(projects__in=visible_projects)
        .distinct()
        .prefetch_related(
            Prefetch(
                "projects",
                queryset=visible_projects.order_by("is_completed", "name"),
            )
        )
        .order_by("name")
    )
    for client in clients:
        yield client, list(client.projects.all())


def search_comments(query: str | None, user) -> QuerySet[Comment]:
    qs = Comment.objects.visible_to(user).select_related(
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
