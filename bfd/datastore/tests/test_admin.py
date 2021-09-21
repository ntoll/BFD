"""
Tests exercising the admin aspects of the datastore module.

Copyright (C) 2020 Nicholas H.Tollervey.

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

MIT License:

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from unittest import mock
from django.test import TestCase
from django.core.exceptions import ValidationError
from datastore import admin
from datastore import models


class UserCreationFormTestCase(TestCase):
    """
    Exercizes the custom methods and validation of the UserCreationForm used in
    the site admin.
    """

    def test_init(self):
        """
        Ensure autofocus is set for the username field.
        """
        f = admin.UserCreationForm()
        self.assertTrue(
            f.fields[f._meta.model.USERNAME_FIELD].widget.attrs["autofocus"]
        )

    def test_clean_password2(self):
        """
        The form ensures the two password fields match.
        """
        f1 = admin.UserCreationForm(
            data={
                "username": "test_user",
                "email": "test@user.com",
                "password1": "xyzzy2001",
                "password2": "xyzzy2001",
            }
        )
        self.assertTrue(f1.is_valid())
        f2 = admin.UserCreationForm(
            data={
                "username": "test_user",
                "email": "test@user.com",
                "password1": "xyzzy2001",
                "password2": "2001xyzzy",
            }
        )
        self.assertFalse(f2.is_valid())
        self.assertEqual(
            f2.errors["password2"], ["The two password fields didn't match."]
        )

    def test_post_clean(self):
        """
        Further password validation (using Django's built-in password
        validator) happens immediately after the form is cleaned.
        """
        f = admin.UserCreationForm(
            data={
                "username": "test_user",
                "email": "test@user.com",
                "password1": "xyzzy2001",
                "password2": "xyzzy2001",
            }
        )
        pwv = mock.MagicMock()
        error = ValidationError("Boom")
        pwv.validate_password = mock.MagicMock(side_effect=error)
        f.add_error = mock.MagicMock()
        with mock.patch("datastore.admin.password_validation", pwv):
            f.is_valid()
        f.add_error.assert_called_once_with("password2", error)

    def test_save(self):
        """
        Ensure the password is set against the user during the saving process.
        """
        mock_user = mock.MagicMock()
        mock_save = mock.MagicMock()
        mock_save.return_value = mock_user
        with mock.patch("datastore.admin.forms.ModelForm.save", mock_save):
            f = admin.UserCreationForm(
                data={
                    "username": "test_user",
                    "email": "test@user.com",
                    "password1": "xyzzy2001",
                    "password2": "xyzzy2001",
                }
            )
            f.is_valid()
            result = f.save()
            self.assertEqual(result, mock_user)
            mock_user.set_password.assert_called_once_with(
                f.cleaned_data["password1"]
            )
            mock_user.save.assert_called_once_with()


class UserChangeFormTestCase(TestCase):
    """
    Exercizes the custom methods and validation of the UserChangeForm used in
    the site admin.
    """

    def test_init(self):
        """
        Password help text is updated.
        """
        u = models.User.objects.create_user(
            username="test_user", email="test@user.com", password="password"
        )
        f = admin.UserChangeForm(u)
        self.assertIsNotNone(f.fields.get("password").help_text)

    def test_clean_password(self):
        """
        Ensure the initial value of the password (not the one from the form
        field) is always used when cleaning.
        """
        u = models.User.objects.create_user(
            username="test_user", email="test@user.com", password="password"
        )
        f = admin.UserChangeForm(u)
        f.initial = mock.MagicMock()
        f.clean_password()
        f.initial.get.assert_called_once_with("password")
