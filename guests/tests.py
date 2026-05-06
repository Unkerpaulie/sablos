"""Tests for the guests app."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class _Fixtures(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user(
            username="staffer", password="pw", is_staff=True
        )
        cls.guest = User.objects.create_user(
            username="someone", password="pw", email="someone@example.com"
        )
        cls.other_guest = User.objects.create_user(
            username="another", password="pw", is_active=False
        )


class GuestListViewTests(_Fixtures):
    def test_anonymous_redirected_to_login(self):
        response = self.client.get(reverse("guests:list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response["Location"])

    def test_guest_forbidden(self):
        self.client.force_login(self.guest)
        response = self.client.get(reverse("guests:list"))
        self.assertEqual(response.status_code, 403)

    def test_staff_sees_only_non_staff_users(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("guests:list"))
        self.assertEqual(response.status_code, 200)
        # Each visible row exposes the per-guest edit URL; staff rows don't.
        self.assertContains(response, reverse("guests:update", args=[self.guest.pk]))
        self.assertContains(response, reverse("guests:update", args=[self.other_guest.pk]))
        self.assertNotContains(
            response, reverse("guests:update", args=[self.staff.pk])
        )


class GuestUpdateViewTests(_Fixtures):
    def test_staff_can_edit_guest(self):
        self.client.force_login(self.staff)
        url = reverse("guests:update", args=[self.guest.pk])
        response = self.client.post(
            url,
            {
                "username": "someone",
                "first_name": "Some",
                "last_name": "One",
                "email": "renamed@example.com",
                "is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.guest.refresh_from_db()
        self.assertEqual(self.guest.first_name, "Some")
        self.assertEqual(self.guest.email, "renamed@example.com")

    def test_cannot_edit_staff_via_guest_update(self):
        self.client.force_login(self.staff)
        url = reverse("guests:update", args=[self.staff.pk])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_guest_cannot_open_update(self):
        self.client.force_login(self.guest)
        url = reverse("guests:update", args=[self.other_guest.pk])
        self.assertEqual(self.client.get(url).status_code, 403)


class GuestToggleActiveTests(_Fixtures):
    def test_toggle_flips_is_active(self):
        self.client.force_login(self.staff)
        url = reverse("guests:toggle_active", args=[self.guest.pk])
        self.assertTrue(self.guest.is_active)
        self.client.post(url)
        self.guest.refresh_from_db()
        self.assertFalse(self.guest.is_active)
        self.client.post(url)
        self.guest.refresh_from_db()
        self.assertTrue(self.guest.is_active)

    def test_toggle_rejects_staff_target(self):
        self.client.force_login(self.staff)
        url = reverse("guests:toggle_active", args=[self.staff.pk])
        self.assertEqual(self.client.post(url).status_code, 404)


class GuestDeleteViewTests(_Fixtures):
    def test_staff_can_delete_guest(self):
        self.client.force_login(self.staff)
        url = reverse("guests:delete", args=[self.guest.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(pk=self.guest.pk).exists())

    def test_cannot_delete_staff_via_guests_app(self):
        self.client.force_login(self.staff)
        url = reverse("guests:delete", args=[self.staff.pk])
        self.assertEqual(self.client.post(url).status_code, 404)
        self.assertTrue(User.objects.filter(pk=self.staff.pk).exists())


class SidebarLinksTests(_Fixtures):
    """The Guests and Admin sidebar links should appear only for staff."""

    def test_guest_does_not_see_staff_only_links(self):
        self.client.force_login(self.guest)
        response = self.client.get(reverse("pm:dashboard"))
        self.assertNotContains(response, 'href="/admin/"')
        self.assertNotContains(response, reverse("guests:list"))

    def test_staff_sees_both_links(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("pm:dashboard"))
        self.assertContains(response, 'href="/admin/"')
        self.assertContains(response, reverse("guests:list"))
