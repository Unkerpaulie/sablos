"""Tests for the public home app."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import ContactMessage

User = get_user_model()


class IndexViewTests(TestCase):
    def test_index_renders(self):
        response = self.client.get(reverse("home:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hi, I'm Paul")


class ContactViewTests(TestCase):
    def test_get_renders_form(self):
        response = self.client.get(reverse("home:contact"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "name=\"body\"")

    def test_post_creates_message(self):
        response = self.client.post(
            reverse("home:contact"),
            {"name": "Alice", "email": "alice@example.com", "body": "**hello**"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 1)
        msg = ContactMessage.objects.get()
        self.assertEqual(msg.name, "Alice")
        self.assertEqual(msg.body, "**hello**")
        self.assertFalse(msg.is_read)

    def test_post_invalid_keeps_form(self):
        response = self.client.post(
            reverse("home:contact"),
            {"name": "", "email": "not-an-email", "body": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)


class GuestSignUpViewTests(TestCase):
    url = "/guest-signup/"

    def test_get_renders(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post_creates_non_staff_active_user_and_logs_in(self):
        response = self.client.post(
            self.url,
            {
                "username": "newguest",
                "password1": "Hunter2-Hunter2",
                "password2": "Hunter2-Hunter2",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].endswith(reverse("pm:dashboard")))
        user = User.objects.get(username="newguest")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)
        # Session should be authenticated as the new user.
        session_user_id = self.client.session.get("_auth_user_id")
        self.assertEqual(int(session_user_id), user.pk)

    def test_authenticated_user_redirected_away(self):
        existing = User.objects.create_user(username="already", password="pw")
        self.client.force_login(existing)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].endswith(reverse("pm:dashboard")))


class ContactMessageModelTests(TestCase):
    def test_mark_read_and_unread(self):
        msg = ContactMessage.objects.create(name="A", email="a@b.io", body="x")
        self.assertFalse(msg.is_read)
        msg.mark_read()
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)
        msg.mark_unread()
        msg.refresh_from_db()
        self.assertFalse(msg.is_read)
