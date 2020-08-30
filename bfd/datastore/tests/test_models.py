"""
Tests for the datastore models.

Copyright (C) 2020 Nicholas H.Tollervey (ntoll@ntoll.org).

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>
"""
from unittest import mock
from datetime import datetime
from django.test import TestCase
from datastore import models
from django.core.exceptions import ValidationError
from datastore.utils import get_uuid


class UserTestCase(TestCase):
    """
    Exercises the bespoke BFD User model.

    The User model is exactly like the regular django.contrib.auth.models.User
    model except that the "username" field *MUST* be a SLUG. This is to ensure
    the user gets a validly named unique namespace for their personal use.
    """

    def test_create_user(self):
        """
        A user with a valid (SLUG) username is created as expected.
        """
        # Create the user.
        user = models.User.objects.create_user(
            username="test_user", email="test@user.com", password="password"
        )
        # Ensure it's in the database.
        u = models.User.objects.get(username="test_user")
        self.assertEqual(u.email, user.email)

    def test_create_user_no_username(self):
        """
        If no username is given, a ValueError is raised.
        """
        with self.assertRaises(ValueError):
            models.User.objects.create_user(
                username="", email="test@user.com", password="password"
            )

    def test_create_user_invalid_username(self):
        """
        A user without a SLUG username results in a validation error.
        """
        # Try to create the user.
        with self.assertRaises(ValidationError):
            models.User.objects.create_user(
                username=".test@user",
                email="test@user.com",
                password="password",
            )

    def test_create_user_invalid_email(self):
        """
        A user without a valid email address results in a validation error.
        """
        # Try to create the user.
        with self.assertRaises(ValidationError):
            models.User.objects.create_user(
                username="test_user",
                email="testuser.com",
                password="password",
            )


class NamespaceTestCase(TestCase):
    """
    Exercises the NamespaceManager and Namespace model.
    """

    def setUp(self):
        self.user = models.User.objects.create_user(
            username="test_user", email="test@user.com", password="password"
        )

    def test_create_namespace(self):
        """
        Ensure the user who creates the namespace is assigned the expected
        roles.
        """
        name = "my_namespace"
        description = "This is a test namespace."
        ns = models.Namespace.objects.create_namespace(
            name, description, self.user
        )
        self.assertEqual(ns.name, name)
        self.assertEqual(ns.description, description)
        self.assertIn(self.user, ns.admins.all())
        self.assertEqual(ns.created_by, self.user)
        self.assertIsInstance(ns.created_on, datetime)
        self.assertEqual(ns.updated_by, self.user)
        self.assertIsInstance(ns.updated_on, datetime)


class TagTestCase(TestCase):
    """
    Exercises the TagManager and Tag model.
    """

    def setUp(self):
        self.user = models.User.objects.create_user(
            username="test_user", email="test@user.com", password="password"
        )
        self.namespace = models.Namespace.objects.create_namespace(
            "my_namespace", "This is a test namespace.", self.user
        )

    def test_create_tag(self):
        """
        Ensure the user who creates the tag is allowed to and therefore
        assigned the expected roles.
        """
        name = "my_tag"
        description = "This is a test tag."
        type_of = models.VALID_DATA_TYPES[0][0]
        uuid = get_uuid(self.namespace.name, name)
        private = False
        tag = models.Tag.objects.create_tag(
            name, description, type_of, self.namespace, private, self.user
        )
        self.assertEqual(tag.name, name)
        self.assertEqual(tag.description, description)
        self.assertEqual(tag.type_of, type_of)
        self.assertEqual(tag.namespace, self.namespace)
        self.assertFalse(tag.private)
        self.assertEqual(tag.created_by, self.user)
        self.assertIsInstance(tag.created_on, datetime)
        self.assertEqual(tag.updated_by, self.user)
        self.assertIsInstance(tag.updated_on, datetime)
        self.assertEqual(tag.uuid, uuid)
        self.assertNotIn(self.user, tag.users.all())
        self.assertNotIn(self.user, tag.readers.all())

    def test_create_private_tag(self):
        """
        If the new tag is created as a private tag, then ensure the user who
        created it is in both the readers and users list.
        """
        name = "my_tag"
        description = "This is a test tag."
        type_of = models.VALID_DATA_TYPES[0][0]
        uuid = get_uuid(self.namespace.name, name)
        private = True
        tag = models.Tag.objects.create_tag(
            name, description, type_of, self.namespace, private, self.user
        )
        self.assertEqual(tag.name, name)
        self.assertEqual(tag.description, description)
        self.assertEqual(tag.type_of, type_of)
        self.assertEqual(tag.namespace, self.namespace)
        self.assertTrue(tag.private)
        self.assertEqual(tag.created_by, self.user)
        self.assertIsInstance(tag.created_on, datetime)
        self.assertEqual(tag.updated_by, self.user)
        self.assertIsInstance(tag.updated_on, datetime)
        self.assertEqual(tag.uuid, uuid)
        self.assertIn(self.user, tag.users.all())

    def test_create_tag_wrong_user(self):
        """
        If the user creating the tag is not an admin associated with the parent
        namespace, then a PermissionError is raised.
        """
        wrong_user = models.User.objects.create_user(
            username="wrong_user", email="wrong@user.com", password="password"
        )
        name = "my_tag"
        description = "This is a test tag."
        type_of = models.VALID_DATA_TYPES[0][0]
        private = True
        with self.assertRaises(PermissionError):
            models.Tag.objects.create_tag(
                name, description, type_of, self.namespace, private, wrong_user
            )

    def test_tag_path(self):
        """
        Ensure the generated path is correct given the namespace and tag name.
        """
        name = "my_tag"
        description = "This is a test tag."
        type_of = models.VALID_DATA_TYPES[0][0]
        private = True
        tag = models.Tag.objects.create_tag(
            name, description, type_of, self.namespace, private, self.user
        )
        expected = f"{self.namespace.name}/{name}"
        self.assertEqual(tag.path, expected)

    def test_is_user(self):
        """
        Ensure the is_user method returns a true reflection of the user state
        for referenced users. If a user is a user of a tag, it means they can
        annotate an object via the tag.
        """
        not_a_user = models.User.objects.create_user(
            username="test_user2", email="test2@user.com", password="password"
        )
        name = "my_tag"
        description = "This is a test tag."
        type_of = models.VALID_DATA_TYPES[0][0]
        private = False
        tag = models.Tag.objects.create_tag(
            name, description, type_of, self.namespace, private, self.user
        )
        tag.users.add(self.user)
        self.assertTrue(tag.is_user(self.user))
        self.assertFalse(tag.is_user(not_a_user))

    def test_is_reader_public(self):
        """
        If a tag is public, all users, no matter their other state with regard
        to the tag, are readers. Readers can see values on objects annotated
        via this tag.
        """
        not_a_reader = models.User.objects.create_user(
            username="test_user2", email="test2@user.com", password="password"
        )
        name = "my_tag"
        description = "This is a test tag."
        type_of = models.VALID_DATA_TYPES[0][0]
        private = False
        tag = models.Tag.objects.create_tag(
            name, description, type_of, self.namespace, private, self.user
        )
        tag.users.add(self.user)
        self.assertTrue(tag.is_reader(self.user))
        self.assertTrue(tag.is_reader(not_a_reader))

    def test_is_reader_private(self):
        """
        If the tag is private, only users explicitly marked as "readers" or who
        are able to annotate with the tag (they're users of the tag) are able
        to see values on objects annotated via this tag.
        """
        is_a_reader = models.User.objects.create_user(
            username="test_user2", email="test2@user.com", password="password"
        )
        not_a_reader = models.User.objects.create_user(
            username="test_user3", email="test3@user.com", password="password"
        )
        name = "my_tag"
        description = "This is a test tag."
        type_of = models.VALID_DATA_TYPES[0][0]
        private = True
        tag = models.Tag.objects.create_tag(
            name, description, type_of, self.namespace, private, self.user
        )
        tag.users.add(self.user)
        tag.readers.add(is_a_reader)
        self.assertTrue(tag.is_reader(self.user))
        self.assertTrue(tag.is_reader(is_a_reader))
        self.assertFalse(tag.is_reader(not_a_reader))


class AbstractBaseValueTestCase(TestCase):
    """
    Exercises the AbstractBaseValue (ABV) model.
    """

    def setUp(self):
        self.user = models.User.objects.create_user(
            username="test_user", email="test@user.com", password="password"
        )
        self.namespace = models.Namespace.objects.create_namespace(
            "my_namespace", "This is a test namespace.", self.user
        )
        self.tag = models.Tag.objects.create_tag(
            "my_tag",
            "This is a test tag.",
            models.VALID_DATA_TYPES[0][0],
            self.namespace,
            False,
            self.user,
        )

    def test_created_value_has_path(self):
        """
        Ensure a child of ABV can create objects as expected.
        """
        object_id = "a_test_object"
        uuid = get_uuid(self.namespace.name, self.tag.name)
        val = models.StringValue(
            object_id=object_id,
            uuid=uuid,
            namespace=self.namespace,
            tag=self.tag,
            last_updated_by=self.user,
            value="this is an arbitrary string value.",
        )
        val.save()
        expected = f"{object_id}/{self.namespace.name}/{self.tag.name}"
        self.assertEqual(val.path, expected)


class UploadToTestCase(TestCase):
    """
    Exercises the upload_to function associated with the BinaryValue class.

    It ensures versions of the binary value are stored in easy to find and
    archive.
    """

    def setUp(self):
        self.user = models.User.objects.create_user(
            username="test_user", email="test@user.com", password="password"
        )
        self.namespace = models.Namespace.objects.create_namespace(
            "my_namespace", "This is a test namespace.", self.user
        )
        self.tag = models.Tag.objects.create_tag(
            "my_tag",
            "This is a test tag.",
            models.VALID_DATA_TYPES[0][0],
            self.namespace,
            False,
            self.user,
        )

    def test_path_is_correct(self):
        """
        Ensure a child of ABV can create objects as expected.
        """
        object_id = "a_test_object"
        uuid = get_uuid(self.namespace.name, self.tag.name)
        val = models.BinaryValue(
            object_id=object_id,
            uuid=uuid,
            namespace=self.namespace,
            tag=self.tag,
            last_updated_by=self.user,
            value="mock binary data",
            mime="app/json",
        )
        val.save()
        filename = "a_filename.json"
        path = "{object_id}/{namespace}/{tag}/{timestamp}_{filename}".format(
            object_id=object_id,
            namespace=val.namespace.name,
            tag=val.tag.name,
            timestamp=12345.6789,
            filename=filename,
        )
        mock_time = mock.MagicMock()
        mock_time.time.return_value = 12345.6789
        with mock.patch("datastore.models.time", mock_time):
            result = models.upload_to(val, filename)
            self.assertEqual(path, result)
