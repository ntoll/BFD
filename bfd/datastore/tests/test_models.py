"""
Tests for the datastore models.
"""
from unittest import mock
from datetime import datetime
from django.test import TestCase
from django.contrib.auth.models import User
from datastore import models
from datastore.utils import get_uuid


class NamespaceTestCase(TestCase):
    """
    Exercises the NamespaceManager and Namespace model.
    """

    def setUp(self):
        self.user = User.objects.create_user(
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
        self.user = User.objects.create_user(
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
        self.assertIn(self.user, tag.readers.all())

    def test_create_tag_wrong_user(self):
        """
        If the user creating the tag is not an admin associated with the parent
        namespace, then a PermissionError is raised.
        """
        wrong_user = User.objects.create_user(
            username="wrong_user", email="wrong@user.com", password="password"
        )
        name = "my_tag"
        description = "This is a test tag."
        type_of = models.VALID_DATA_TYPES[0][0]
        uuid = get_uuid(self.namespace.name, name)
        private = True
        with self.assertRaises(PermissionError):
            tag = models.Tag.objects.create_tag(
                name, description, type_of, self.namespace, private, wrong_user
            )

    def test_tag_path(self):
        """
        Ensure the generated path is correct given the namespace and tag name.
        """
        name = "my_tag"
        description = "This is a test tag."
        type_of = models.VALID_DATA_TYPES[0][0]
        uuid = get_uuid(self.namespace.name, name)
        private = True
        tag = models.Tag.objects.create_tag(
            name, description, type_of, self.namespace, private, self.user
        )
        expected = f"{self.namespace.name}/{name}"
        self.assertEqual(tag.path, expected)


class AbstractBaseValueTestCase(TestCase):
    """
    Exercises the AbstractBaseValue (ABV) model.
    """

    def setUp(self):
        self.user = User.objects.create_user(
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
        self.user = User.objects.create_user(
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
