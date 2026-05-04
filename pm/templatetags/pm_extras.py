"""Template helpers scoped to the pm app."""
from __future__ import annotations

import markdown as _md
from django import template
from django.utils.safestring import mark_safe

from pm.models import Objective

register = template.Library()


_STATUS_BADGE_CLASSES = {
    Objective.Status.TODO: "bg-secondary",
    Objective.Status.IN_PROGRESS: "bg-primary",
    Objective.Status.BLOCKED: "bg-warning text-dark",
    Objective.Status.DONE: "bg-success",
}

_PRIORITY_BADGE_CLASSES = {
    Objective.Priority.HIGH: "bg-danger",
    Objective.Priority.MEDIUM: "bg-info text-dark",
    Objective.Priority.LOW: "bg-secondary",
}


@register.filter(name="markdown")
def render_markdown(value: str | None) -> str:
    if not value:
        return ""
    html = _md.markdown(
        value,
        extensions=["fenced_code", "tables", "sane_lists"],
        output_format="html",
    )
    return mark_safe(html)


@register.filter(name="status_badge")
def status_badge(status: str) -> str:
    return _STATUS_BADGE_CLASSES.get(status, "bg-secondary")


@register.filter(name="priority_badge")
def priority_badge(priority: int) -> str:
    return _PRIORITY_BADGE_CLASSES.get(priority, "bg-secondary")


@register.filter(name="truncate_chars")
def truncate_chars(value: str | None, length: int = 80) -> str:
    if not value:
        return ""
    text = str(value).strip().replace("\n", " ")
    if len(text) <= length:
        return text
    return text[: length - 1].rstrip() + "…"
