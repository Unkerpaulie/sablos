"""Forms for the project management app.

A small mixin applies Bootstrap classes consistently. Validation logic
relies on Django's ModelForm machinery; no manual request parsing.
"""
from __future__ import annotations

from django import forms

from core.fields import MarkdownTextarea

from .models import Client, Comment, Objective, Project


class BootstrapFormMixin:
    """Add Bootstrap CSS classes to every bound widget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                css_class = "form-check-input"
            elif isinstance(widget, forms.Select):
                css_class = "form-select"
            else:
                css_class = "form-control"
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = (existing + " " + css_class).strip()


class ClientForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Client
        fields = ("name", "email", "phone", "notes")


class ProjectForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Project
        fields = (
            "client",
            "name",
            "init_prompt",
            "repo_link",
            "launch_domain",
            "launch_specs",
            "is_completed",
        )


class ObjectiveForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Objective
        fields = ("project", "description", "status", "priority", "due_date")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }


class CommentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("body",)
        widgets = {
            "body": MarkdownTextarea(attrs={"rows": 3, "placeholder": "Add a comment..."}),
        }
