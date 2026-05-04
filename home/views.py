"""Public-facing views for the home site."""
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from .forms import ContactForm


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
