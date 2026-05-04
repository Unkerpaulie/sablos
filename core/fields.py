"""Shared model and form field types.

`MarkdownField` is a domain-meaningful alias for a text field whose
content is authored in Markdown. It stores raw Markdown and surfaces a
form widget tagged for downstream styling / progressive enhancement
(e.g. attaching a Markdown preview later).

Rendering of the stored Markdown to HTML lives in template filters so
output concerns stay in the presentation layer.
"""
from __future__ import annotations

from django import forms
from django.db import models


class MarkdownTextarea(forms.Textarea):
    """Textarea with Bootstrap classes and a marker for markdown editors."""

    def __init__(self, attrs=None):
        defaults = {
            "rows": 6,
            "class": "form-control",
            "data-markdown": "true",
            "spellcheck": "true",
        }
        if attrs:
            merged = {**defaults, **attrs}
            existing = attrs.get("class", "")
            merged["class"] = (defaults["class"] + " " + existing).strip()
        else:
            merged = defaults
        super().__init__(merged)


class MarkdownFormField(forms.CharField):
    widget = MarkdownTextarea


class MarkdownField(models.TextField):
    """Stores Markdown text. Behaves like TextField at the database level.

    Accepts a ``hint`` kwarg that becomes the form ``help_text`` with the
    suffix ``(Markdown)`` automatically appended. Pass an empty hint (the
    default) to surface just ``(Markdown)``.
    """

    description = "Markdown text"
    MARKDOWN_SUFFIX = "(Markdown)"

    def __init__(self, *args, hint: str = "", **kwargs):
        prefix = (hint or "").strip()
        kwargs["help_text"] = (
            f"{prefix} {self.MARKDOWN_SUFFIX}" if prefix else self.MARKDOWN_SUFFIX
        )
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        defaults = {"form_class": MarkdownFormField, "widget": MarkdownTextarea}
        defaults.update(kwargs)
        return super().formfield(**defaults)
