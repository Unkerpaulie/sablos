"""Forms for the guests app."""
from django import forms
from django.contrib.auth import get_user_model


class GuestForm(forms.ModelForm):
    """Edit a guest user's profile fields and active flag."""

    class Meta:
        model = get_user_model()
        fields = ("username", "first_name", "last_name", "email", "is_active")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-check-input")
            else:
                existing = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = (existing + " form-control").strip()
