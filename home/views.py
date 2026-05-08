"""Public-facing views for the home site."""
import hashlib
import hmac
import logging
import subprocess
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from .forms import ContactForm, GuestSignUpForm

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def github_webhook(request):
    """Verify a GitHub push webhook then trigger redeploy.sh in the background.

    GitHub signs every payload with HMAC-SHA256 using the shared secret
    configured in Settings → Webhooks. We reject anything that doesn't match
    before touching the filesystem.
    """
    secret: str = getattr(settings, "GITHUB_WEBHOOK_SECRET", "") or ""
    if not secret:
        logger.error("github_webhook: GITHUB_WEBHOOK_SECRET is not set — rejecting.")
        return HttpResponseForbidden("Webhook not configured.")

    sig_header = request.META.get("HTTP_X_HUB_SIGNATURE_256", "")
    if not sig_header.startswith("sha256="):
        return HttpResponseForbidden("Missing signature.")

    expected = "sha256=" + hmac.new(
        secret.encode(), request.body, hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, sig_header):
        logger.warning("github_webhook: invalid signature — ignoring request.")
        return HttpResponseForbidden("Invalid signature.")

    script = Path(settings.BASE_DIR) / "redeploy.sh"
    logger.info("github_webhook: verified — spawning %s", script)

    # start_new_session=True detaches the child from gunicorn's process group
    # so it keeps running after systemctl restarts the service mid-script.
    subprocess.Popen(
        ["bash", str(script)],
        cwd=str(settings.BASE_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    return HttpResponse("Deploy triggered.", status=202)


class IndexView(TemplateView):
    template_name = "pages/home.html"


class ContactView(FormView):
    template_name = "pages/contact.html"
    form_class = ContactForm
    success_url = reverse_lazy("home:contact")

    def form_valid(self, form: ContactForm):
        form.save()
        messages.success(
            self.request,
            "Thanks for reaching out. I'll get back to you soon.",
        )
        return super().form_valid(form)


class GuestSignUpView(FormView):
    """Self-service registration that creates non-staff guest accounts.

    The URL is unlinked from the public site; it's intended to be shared
    privately. Already-authenticated users are sent to the dashboard.
    """

    template_name = "registration/guest_signup.html"
    form_class = GuestSignUpForm
    success_url = reverse_lazy("pm:dashboard")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("pm:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: GuestSignUpForm):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, f"Welcome, {user.username}.")
        return super().form_valid(form)
