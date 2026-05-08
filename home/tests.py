"""Tests for the public home app."""
from __future__ import annotations

import hashlib
import hmac
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
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


_SECRET = "test-webhook-secret"
_WEBHOOK_URL = "/deploy/github-webhook/"


def _make_sig(body: bytes, secret: str = _SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


@override_settings(GITHUB_WEBHOOK_SECRET=_SECRET)
class GithubWebhookTests(TestCase):
    def _post(self, body: bytes = b"{}", sig: str | None = None) -> object:
        if sig is None:
            sig = _make_sig(body)
        return self.client.post(
            _WEBHOOK_URL,
            data=body,
            content_type="application/json",
            HTTP_X_HUB_SIGNATURE_256=sig,
        )

    def test_get_not_allowed(self):
        response = self.client.get(_WEBHOOK_URL)
        self.assertEqual(response.status_code, 405)

    def test_missing_signature_returns_403(self):
        response = self.client.post(_WEBHOOK_URL, data=b"{}", content_type="application/json")
        self.assertEqual(response.status_code, 403)

    def test_wrong_signature_returns_403(self):
        response = self._post(sig=_make_sig(b"{}", secret="wrong-secret"))
        self.assertEqual(response.status_code, 403)

    @patch("home.views.subprocess.Popen")
    def test_valid_request_triggers_popen_and_returns_202(self, mock_popen):
        response = self._post()
        self.assertEqual(response.status_code, 202)
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        self.assertIn("redeploy.sh", args[0][1])
        self.assertTrue(kwargs.get("start_new_session"))

    @override_settings(GITHUB_WEBHOOK_SECRET="")
    @patch("home.views.subprocess.Popen")
    def test_unconfigured_secret_returns_403_and_does_not_spawn(self, mock_popen):
        response = self._post()
        self.assertEqual(response.status_code, 403)
        mock_popen.assert_not_called()


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
