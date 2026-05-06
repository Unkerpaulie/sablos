"""Tests for the project-management app."""
from __future__ import annotations

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.urls import reverse

from . import services
from .models import Client, Comment, Objective, Project
from .templatetags.pm_extras import due_row_class

User = get_user_model()


class _Fixtures(TestCase):
    """Shared test data — staff, guest, two clients (one with a hidden project)."""

    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user("staff", password="pw", is_staff=True)
        cls.guest = User.objects.create_user("guest", password="pw")
        cls.client_v = Client.objects.create(name="VisibleCo")
        cls.client_h = Client.objects.create(name="HiddenCo")
        cls.client_empty = Client.objects.create(name="EmptyCo")
        cls.proj_v = Project.objects.create(client=cls.client_v, name="VProj")
        cls.proj_h = Project.objects.create(
            client=cls.client_h, name="HProj", is_hidden=True,
        )
        cls.obj_v = Objective.objects.create(
            project=cls.proj_v, description="visible objective body",
            status=Objective.Status.IN_PROGRESS,
        )
        cls.obj_h = Objective.objects.create(
            project=cls.proj_h, description="hidden objective body",
            status=Objective.Status.IN_PROGRESS,
        )
        cls.cmt_v = Comment.objects.create(objective=cls.obj_v, body="visible comment")
        cls.cmt_h = Comment.objects.create(objective=cls.obj_h, body="hidden comment")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class ProjectModelTests(TestCase):
    def test_mark_completed_and_reopen(self):
        c = Client.objects.create(name="Acme")
        p = Project.objects.create(client=c, name="P1")
        self.assertFalse(p.is_completed)
        p.mark_completed()
        self.assertTrue(Project.objects.get(pk=p.pk).is_completed)
        p.reopen()
        self.assertFalse(Project.objects.get(pk=p.pk).is_completed)

    def test_unique_project_per_client(self):
        from django.db import IntegrityError, transaction
        c = Client.objects.create(name="Acme")
        Project.objects.create(client=c, name="P")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Project.objects.create(client=c, name="P")


class ObjectiveModelTests(TestCase):
    def test_short_description_truncates(self):
        c = Client.objects.create(name="X")
        p = Project.objects.create(client=c, name="P")
        long = "x" * 120
        o = Objective.objects.create(project=p, description=long)
        self.assertLessEqual(len(o.short_description), Objective.SHORT_DESCRIPTION_LENGTH)
        self.assertTrue(o.short_description.endswith("…"))

    def test_short_description_passes_through_short_text(self):
        c = Client.objects.create(name="X")
        p = Project.objects.create(client=c, name="P")
        o = Objective.objects.create(project=p, description="short")
        self.assertEqual(o.short_description, "short")


class VisibilityQuerySetTests(_Fixtures):
    def test_staff_sees_hidden(self):
        self.assertIn(self.proj_h, Project.objects.visible_to(self.staff))
        self.assertIn(self.obj_h, Objective.objects.visible_to(self.staff))
        self.assertIn(self.cmt_h, Comment.objects.visible_to(self.staff))

    def test_guest_does_not_see_hidden(self):
        self.assertNotIn(self.proj_h, Project.objects.visible_to(self.guest))
        self.assertNotIn(self.obj_h, Objective.objects.visible_to(self.guest))
        self.assertNotIn(self.cmt_h, Comment.objects.visible_to(self.guest))
        # Visible items still surface.
        self.assertIn(self.proj_v, Project.objects.visible_to(self.guest))

    def test_anonymous_treated_as_non_staff(self):
        self.assertNotIn(self.proj_h, Project.objects.visible_to(AnonymousUser()))


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------
class ServicesTests(_Fixtures):
    def test_dashboard_groups_filter_by_visibility(self):
        staff_pks = {g.project.pk for g in services.get_dashboard_groups(self.staff)}
        guest_pks = {g.project.pk for g in services.get_dashboard_groups(self.guest)}
        self.assertIn(self.proj_h.pk, staff_pks)
        self.assertNotIn(self.proj_h.pk, guest_pks)
        self.assertIn(self.proj_v.pk, guest_pks)

    def test_dashboard_only_open_objectives(self):
        Objective.objects.create(
            project=self.proj_v, description="future",
            status=Objective.Status.TODO,
        )
        groups = {g.project.pk: g for g in services.get_dashboard_groups(self.staff)}
        statuses = {o.status for o in groups[self.proj_v.pk].objectives}
        self.assertEqual(statuses, {Objective.Status.IN_PROGRESS})

    def test_list_projects_omits_clients_with_no_visible_projects(self):
        staff_grouped = list(services.list_projects_grouped_by_client(self.staff))
        guest_grouped = list(services.list_projects_grouped_by_client(self.guest))
        staff_clients = {c.pk for c, _ in staff_grouped}
        guest_clients = {c.pk for c, _ in guest_grouped}
        # EmptyCo never appears (no projects at all).
        self.assertNotIn(self.client_empty.pk, staff_clients)
        self.assertNotIn(self.client_empty.pk, guest_clients)
        # HiddenCo appears for staff but not guest.
        self.assertIn(self.client_h.pk, staff_clients)
        self.assertNotIn(self.client_h.pk, guest_clients)
        # VisibleCo always appears.
        self.assertIn(self.client_v.pk, staff_clients)
        self.assertIn(self.client_v.pk, guest_clients)

    def test_search_comments_respects_visibility_and_query(self):
        staff_qs = services.search_comments(None, self.staff)
        guest_qs = services.search_comments(None, self.guest)
        self.assertIn(self.cmt_h, staff_qs)
        self.assertNotIn(self.cmt_h, guest_qs)
        # Query filter still works.
        self.assertIn(self.cmt_v, services.search_comments("visible", self.guest))
        self.assertEqual(
            list(services.search_comments("nope-no-match", self.staff)), []
        )



# ---------------------------------------------------------------------------
# View access control
# ---------------------------------------------------------------------------
class AccessControlTests(_Fixtures):
    def test_anonymous_redirected_to_login(self):
        for url in [
            reverse("pm:dashboard"),
            reverse("pm:client_list"),
            reverse("pm:project_list"),
            reverse("pm:project_detail", args=[self.proj_v.pk]),
            reverse("pm:objective_detail", args=[self.obj_v.pk]),
            reverse("pm:comment_list"),
        ]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, url)
            self.assertIn("/login/", response["Location"])

    def test_guest_read_access_to_visible_pages(self):
        self.client.force_login(self.guest)
        for url in [
            reverse("pm:dashboard"),
            reverse("pm:client_list"),
            reverse("pm:client_detail", args=[self.client_v.pk]),
            reverse("pm:project_list"),
            reverse("pm:project_detail", args=[self.proj_v.pk]),
            reverse("pm:objective_detail", args=[self.obj_v.pk]),
            reverse("pm:comment_list"),
        ]:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_guest_gets_404_for_hidden_project_and_objective(self):
        self.client.force_login(self.guest)
        self.assertEqual(
            self.client.get(reverse("pm:project_detail", args=[self.proj_h.pk])).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(reverse("pm:objective_detail", args=[self.obj_h.pk])).status_code,
            404,
        )

    def test_staff_can_open_hidden_pages(self):
        self.client.force_login(self.staff)
        self.assertEqual(
            self.client.get(reverse("pm:project_detail", args=[self.proj_h.pk])).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(reverse("pm:objective_detail", args=[self.obj_h.pk])).status_code,
            200,
        )

    def test_guest_blocked_from_write_routes(self):
        self.client.force_login(self.guest)
        for url in [
            reverse("pm:client_create"),
            reverse("pm:client_update", args=[self.client_v.pk]),
            reverse("pm:project_create"),
            reverse("pm:project_update", args=[self.proj_v.pk]),
            reverse("pm:objective_create"),
            reverse("pm:objective_update", args=[self.obj_v.pk]),
            reverse("pm:message_list"),
        ]:
            self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_only_staff_can_post_comments(self):
        self.client.force_login(self.guest)
        url = reverse("pm:objective_detail", args=[self.obj_v.pk])
        response = self.client.post(url, {"body": "guest tried"})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Comment.objects.filter(body="guest tried").exists())

        self.client.force_login(self.staff)
        response = self.client.post(url, {"body": "staff added"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Comment.objects.filter(body="staff added").exists())

    def test_message_toggle_read_round_trip(self):
        from home.models import ContactMessage
        msg = ContactMessage.objects.create(name="A", email="a@b.io", body="x")
        self.client.force_login(self.staff)
        url = reverse("pm:message_toggle_read", args=[msg.pk])
        self.client.post(url)
        self.assertTrue(ContactMessage.objects.get(pk=msg.pk).is_read)
        self.client.post(url)
        self.assertFalse(ContactMessage.objects.get(pk=msg.pk).is_read)



class CreateFormPrefillTests(_Fixtures):
    def test_project_create_preselects_client_from_query(self):
        self.client.force_login(self.staff)
        url = reverse("pm:project_create") + f"?client={self.client_v.pk}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].initial.get("client"), str(self.client_v.pk))

    def test_objective_create_preselects_project_from_query(self):
        self.client.force_login(self.staff)
        url = reverse("pm:objective_create") + f"?project={self.proj_v.pk}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].initial.get("project"), str(self.proj_v.pk))



class DueRowClassTests(_Fixtures):
    def _make_objective(self, **kwargs):
        defaults = {
            "project": self.proj_v,
            "description": "x",
            "status": Objective.Status.IN_PROGRESS,
        }
        defaults.update(kwargs)
        return Objective(**defaults)

    def test_no_due_date_returns_empty(self):
        self.assertEqual(due_row_class(self._make_objective(due_date=None)), "")

    def test_overdue_returns_danger(self):
        obj = self._make_objective(due_date=date.today() - timedelta(days=1))
        self.assertEqual(due_row_class(obj), "table-danger")

    def test_due_today_returns_warning(self):
        obj = self._make_objective(due_date=date.today())
        self.assertEqual(due_row_class(obj), "table-warning")

    def test_due_within_three_days_returns_warning(self):
        obj = self._make_objective(due_date=date.today() + timedelta(days=3))
        self.assertEqual(due_row_class(obj), "table-warning")

    def test_due_beyond_three_days_returns_empty(self):
        obj = self._make_objective(due_date=date.today() + timedelta(days=4))
        self.assertEqual(due_row_class(obj), "")

    def test_done_objective_never_highlighted(self):
        obj = self._make_objective(
            due_date=date.today() - timedelta(days=10),
            status=Objective.Status.DONE,
        )
        self.assertEqual(due_row_class(obj), "")
