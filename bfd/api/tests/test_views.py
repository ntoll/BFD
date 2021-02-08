"""
Tests exercising the API views

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
from django.urls import path, include, reverse
from rest_framework import status
from rest_framework.test import APITestCase, URLPatternsTestCase
from rest_framework.authtoken.models import Token
from datastore import models


class UserDetailViewTestCase(APITestCase, URLPatternsTestCase):
    """
    Exercises the UserDetail view.
    """

    urlpatterns = [
        path("api/", include("api.urls")),
    ]

    def setUp(self):
        self.target_user = models.User.objects.create_user(
            username="target_user",
            email="target@user.com",
            password="password",
            is_superuser=False,
        )
        Token.objects.create(user=self.target_user)
        self.super_user = models.User.objects.create_user(
            username="super_user",
            email="super@user.com",
            password="password",
            is_superuser=True,
        )
        Token.objects.create(user=self.super_user)
        self.test_user = models.User.objects.create_user(
            username="test_user",
            email="test@user.com",
            password="password",
            is_superuser=False,
        )
        Token.objects.create(user=self.test_user)

    def test_get_cannot_be_anonymous(self):
        """
        An HTTP get to the endpoint results in an HTTP 403 Forbidden response.
        """
        url = reverse(
            "user-detail",
            kwargs={
                "username": "test_user",
            },
        )
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_not_found(self):
        """
        If the caller is logged in but the referenced user does not exist, the
        API returns a 404 Not Found response.
        """
        url = reverse(
            "user-detail",
            kwargs={
                "username": "missing_user",
            },
        )
        self.client.login(username="test_user", password="password")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get(self):
        """
        An HTTP get as a logged in user to the endpoint, returns the expected
        information about the referenced user.
        """
        url = reverse(
            "user-detail",
            kwargs={
                "username": "target_user",
            },
        )
        token = Token.objects.get(user__username="test_user")
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual("target_user", data["username"])
        self.assertEqual("target@user.com", data["email"])
        self.assertFalse(data["is_admin"])
        self.assertIsNone(data["last_login"])

    def test_get_superuser(self):
        """
        An HTTP get as a logged in user to the endpoint, returns the expected
        information about the referenced user. In this case, since the target
        user is a superuser, the is_admin flag is set in the response.
        """
        url = reverse(
            "user-detail",
            kwargs={
                "username": "super_user",
            },
        )
        token = Token.objects.get(user__username="test_user")
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual("super_user", data["username"])
        self.assertEqual("super@user.com", data["email"])
        self.assertTrue(data["is_admin"])
        self.assertIsNone(data["last_login"])


class NamespaceCreateViewTestCase(APITestCase, URLPatternsTestCase):
    """
    Exercises the NamespaceCreate view.
    """

    urlpatterns = [
        path("api/", include("api.urls")),
    ]

    def setUp(self):
        self.admin_user = models.User.objects.create_user(
            username="super_user",
            email="admin@user.com",
            password="password",
            is_staff=True,
        )
        Token.objects.create(user=self.admin_user)
        self.test_user = models.User.objects.create_user(
            username="test_user",
            email="test@user.com",
            password="password",
            is_superuser=False,
        )
        Token.objects.create(user=self.test_user)

    def test_post_cannot_be_anonymous(self):
        """
        An HTTP get to the endpoint results in an HTTP 403 Forbidden response.
        """
        url = reverse("namespace-create")
        data = {
            "name": "test_namespace",
            "description": "A test namespace's description.",
            "admins": [],
        }
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_not_admin(self):
        """
        If the caller is logged in but not an admin user, then the API returns
        a 403 Forbidden response.
        """
        url = reverse("namespace-create")
        data = {
            "name": "test_namespace",
            "description": "A test namespace's description.",
            "admins": [],
        }
        token = Token.objects.get(user__username="test_user")
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_ok(self):
        """
        If the caller is logged in and an admin user, then the API returns
        a 201 Created response. The namespace has been added to the database.
        """
        url = reverse("namespace-create")
        data = {
            "name": "test_namespace",
            "description": "A test namespace's description.",
            "admins": [],
        }
        token = Token.objects.get(user__username="super_user")
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_data = response.json()
        self.assertEqual(data["name"], new_data["name"])
        self.assertEqual(data["description"], new_data["description"])
        self.assertEqual(
            [
                {
                    "username": "super_user",
                    "avatar": self.admin_user.avatar,
                },
            ],
            new_data["admins"],
        )

    def test_post_bad_data(self):
        """
        Assuming the caller is an admin, if there's something wrong with the
        passed in data, then they get a 400 BAD REQUEST response with error
        information about the problem field.
        """
        url = reverse("namespace-create")
        data = {
            "name": "test namespace",  # Namespace name must be a SLUG!
            "description": "A test namespace's description.",
            "admins": [],
        }
        token = Token.objects.get(user__username="super_user")
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.json())
