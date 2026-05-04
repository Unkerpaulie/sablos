"""Views for the project management app.

Views are deliberately thin: data retrieval and aggregation live in
:mod:`pm.services`; per-instance business behavior lives on the models.
"""
from __future__ import annotations

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)
from django.views.generic.edit import FormMixin

from home.models import ContactMessage

from . import services
from .forms import ClientForm, CommentForm, ObjectiveForm, ProjectForm
from .mixins import StaffLoginRequiredMixin
from .models import Client, Comment, Objective, Project


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
class DashboardView(StaffLoginRequiredMixin, TemplateView):
    template_name = "pm/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["groups"] = services.get_dashboard_groups()
        return context


# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------
class ClientListView(StaffLoginRequiredMixin, ListView):
    model = Client
    template_name = "pm/clients/list.html"
    context_object_name = "clients"


class ClientDetailView(StaffLoginRequiredMixin, DetailView):
    model = Client
    template_name = "pm/clients/detail.html"
    context_object_name = "client"

    def get_queryset(self):
        return super().get_queryset().prefetch_related("projects")


class ClientCreateView(StaffLoginRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = "pm/clients/form.html"
    success_url = reverse_lazy("pm:client_list")


class ClientUpdateView(StaffLoginRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = "pm/clients/form.html"


class ClientDeleteView(StaffLoginRequiredMixin, DeleteView):
    model = Client
    template_name = "pm/clients/confirm_delete.html"
    success_url = reverse_lazy("pm:client_list")


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------
class ProjectListView(StaffLoginRequiredMixin, TemplateView):
    template_name = "pm/projects/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["client_projects"] = list(services.list_projects_grouped_by_client())
        return context


class ProjectDetailView(StaffLoginRequiredMixin, DetailView):
    model = Project
    template_name = "pm/projects/detail.html"
    context_object_name = "project"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("client")
            .prefetch_related("objectives")
        )


class ProjectCreateView(StaffLoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "pm/projects/form.html"


class ProjectUpdateView(StaffLoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "pm/projects/form.html"


class ProjectDeleteView(StaffLoginRequiredMixin, DeleteView):
    model = Project
    template_name = "pm/projects/confirm_delete.html"
    success_url = reverse_lazy("pm:project_list")


# ---------------------------------------------------------------------------
# Objectives
# ---------------------------------------------------------------------------
class ObjectiveDetailView(StaffLoginRequiredMixin, FormMixin, DetailView):
    model = Objective
    template_name = "pm/objectives/detail.html"
    context_object_name = "objective"
    form_class = CommentForm

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("project", "project__client")
            .prefetch_related("comments")
        )

    def get_success_url(self) -> str:
        return reverse("pm:objective_detail", args=[self.object.pk])

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            comment: Comment = form.save(commit=False)
            comment.objective = self.object
            comment.save()
            messages.success(request, "Comment added.")
            return redirect(self.get_success_url())
        return self.form_invalid(form)


class ObjectiveCreateView(StaffLoginRequiredMixin, CreateView):
    model = Objective
    form_class = ObjectiveForm
    template_name = "pm/objectives/form.html"

    def get_initial(self):
        initial = super().get_initial()
        project_id = self.request.GET.get("project")
        if project_id:
            initial["project"] = project_id
        return initial


class ObjectiveUpdateView(StaffLoginRequiredMixin, UpdateView):
    model = Objective
    form_class = ObjectiveForm
    template_name = "pm/objectives/form.html"


class ObjectiveDeleteView(StaffLoginRequiredMixin, DeleteView):
    model = Objective
    template_name = "pm/objectives/confirm_delete.html"

    def get_success_url(self) -> str:
        return self.object.project.get_absolute_url()


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------
class CommentListView(StaffLoginRequiredMixin, ListView):
    template_name = "pm/comments/list.html"
    context_object_name = "comments"
    paginate_by = 25

    def get_queryset(self):
        return services.search_comments(self.request.GET.get("q"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        return context


class CommentDeleteView(StaffLoginRequiredMixin, DeleteView):
    model = Comment
    template_name = "pm/comments/confirm_delete.html"

    def get_success_url(self) -> str:
        return self.object.objective.get_absolute_url()


# ---------------------------------------------------------------------------
# Inbox (contact messages)
# ---------------------------------------------------------------------------
class MessageListView(StaffLoginRequiredMixin, ListView):
    model = ContactMessage
    template_name = "pm/messages/list.html"
    context_object_name = "contact_messages"
    paginate_by = 25


class MessageToggleReadView(StaffLoginRequiredMixin, View):
    """Flip the ``is_read`` flag and return to the list."""

    def post(self, request, pk: int):
        message = get_object_or_404(ContactMessage, pk=pk)
        if message.is_read:
            message.mark_unread()
        else:
            message.mark_read()
        return redirect("pm:message_list")
