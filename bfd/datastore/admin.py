"""
Define admin related forms and managers for the bespoke BFD User model.

The User model is exactly like the regular django.contrib.auth.models.User
model except that the "username" field *MUST* be a SLUG. This is to ensure the
user gets a validly named unique namespace for their personal use.

Copyright (C) 2020 CamerataIO Limited.

"Commons Clause" License Condition v1.0:

The Software is provided to you by the Licensor under the License, as defined
below, subject to the following condition.

Without limiting other conditions in the License, the grant of rights under the
License will not include, and the License does not grant to you, the right to
Sell the Software.

For purposes of the foregoing, "Sell" means practicing any or all of the rights
granted to you under the License to provide to third parties, for a fee or
other consideration (including without limitation fees for hosting or
consulting/support services related to the Software), a product or service
whose value derives, entirely or substantially, from the functionality of the
Software. Any license notice or attribution required by the License must also
include this Commons Clause License Condition notice.

Apache License v2.0 Notice:

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from django import forms  # type: ignore
from django.contrib import admin  # type: ignore
from django.core.exceptions import ValidationError  # type: ignore
from django.contrib.auth import password_validation  # type: ignore
from django.contrib.auth.models import Group  # type: ignore
from django.contrib.auth.forms import ReadOnlyPasswordHashField  # type: ignore
from django.contrib.auth import admin as auth_admin  # type: ignore
from django.utils.translation import gettext_lazy as _  # type: ignore
from .models import User, Namespace, Tag


class UserCreationForm(forms.ModelForm):
    """
    A form for creating new BFD users who have a username that is also a valid
    SLUG field.
    """

    error_messages = {
        "password_mismatch": _("The two password fields didn't match."),
    }
    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
        help_text=_("Enter the same password as before, for verification."),
    )

    class Meta:
        model = User
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._meta.model.USERNAME_FIELD in self.fields:
            self.fields[self._meta.model.USERNAME_FIELD].widget.attrs[
                "autofocus"
            ] = True

    def clean_password2(self) -> str:
        """
        Passwords must be the same.
        """
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                self.error_messages["password_mismatch"],
                code="password_mismatch",
            )
        return password2

    def _post_clean(self):
        """
        Validate the password after self.instance is updated with form data
        by super().
        """
        super()._post_clean()
        password = self.cleaned_data.get("password2")
        if password:
            try:
                password_validation.validate_password(password, self.instance)
            except ValidationError as error:
                self.add_error("password2", error)

    def save(self, commit=True) -> User:
        """
        Ensures the password is set against the user.
        """
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """
    A form for changing BFD users who have a username that is also a valid
    SLUG field.
    """

    password = ReadOnlyPasswordHashField(
        label=_("Password"),
        help_text=_(
            "Raw passwords are not stored, so there is no way to see this "
            "user's password, but you can change the password using "
            '<a href="{}">this form</a>.'
        ),
    )

    class Meta:
        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        password = self.fields.get("password")
        if password:
            password.help_text = password.help_text.format("../password/")

    def clean_password(self) -> str:
        """
        Regardless of what the user provides, return the initial value.
        This is done here, rather than on the field, because the
        field does not have access to the initial value.
        """
        return self.initial.get("password")


class UserAdmin(auth_admin.UserAdmin):
    """
    Admin class for BFD User model.
    """

    form = UserChangeForm
    add_form = UserCreationForm


# Register your models here.
admin.site.register(User, UserAdmin)
admin.site.register(Namespace)
admin.site.register(Tag)
# We're not using Django's built-in permissions, so unregister the Group model
# from admin.
admin.site.unregister(Group)
