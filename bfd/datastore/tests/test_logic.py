"""
Tests for the datastore logic used to define the behaviour of the API.

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
from django.test import TestCase
from datastore import logic
from datastore import models


class NamespaceTestCase(TestCase):
    """
    Exercises the namespace related administrative functions.
    """

    def setUp(self):
        self.site_admin_user = models.User.objects.create_user(
            username="site_admin_user",
            email="test@user.com",
            password="password",
            is_superuser=True,
        )
        self.admin_user = models.User.objects.create_user(
            username="admin_user", email="test2@user.com", password="password",
        )
        self.tag_user = models.User.objects.create_user(
            username="tag_user", email="test3@user.com", password="password",
        )
        self.tag_reader = models.User.objects.create_user(
            username="tag_reader", email="test4@user.com", password="password",
        )
        self.normal_user = models.User.objects.create_user(
            username="normal_user",
            email="test5@user.com",
            password="password",
        )
        self.namespace_name = "test_namespace"
        self.namespace_description = "This is a test namespace."
        self.test_namespace = logic.create_namespace(
            self.site_admin_user,
            self.namespace_name,
            self.namespace_description,
            admins=[self.admin_user,],
        )
        self.public_tag_name = "public_tag"
        self.public_tag_description = "This is a public tag."
        self.public_tag_type_of = "s"
        self.public_tag = logic.create_tag(
            user=self.site_admin_user,
            name=self.public_tag_name,
            description=self.public_tag_description,
            type_of=self.public_tag_type_of,
            namespace=self.test_namespace,
            private=False,
        )
        self.user_tag_name = "user_tag"
        self.user_tag_description = "This is a user tag."
        self.user_tag_type_of = "b"
        self.user_tag = logic.create_tag(
            user=self.site_admin_user,
            name=self.user_tag_name,
            description=self.user_tag_description,
            type_of=self.user_tag_type_of,
            namespace=self.test_namespace,
            private=True,
            users=[self.tag_user,],
        )
        self.reader_tag_name = "reader_tag"
        self.reader_tag_description = "This is a reader tag."
        self.reader_tag_type_of = "i"
        self.reader_tag = logic.create_tag(
            user=self.site_admin_user,
            name=self.reader_tag_name,
            description=self.reader_tag_description,
            type_of=self.reader_tag_type_of,
            namespace=self.test_namespace,
            private=True,
            readers=[self.tag_reader,],
        )

    def test_create_namespace_as_site_admin(self):
        """
        Ensure a site admin user who creates the namespace is assigned the
        expected admin role.
        """
        name = "my_namespace"
        description = "This is a test namespace."
        mock_logger = mock.MagicMock()
        with mock.patch("datastore.logic.logger", mock_logger):
            ns = logic.create_namespace(
                self.site_admin_user, name, description
            )
            self.assertEqual(ns.name, name)
            self.assertEqual(ns.description, description)
            self.assertIn(self.site_admin_user, ns.admins.all())
            mock_logger.msg.assert_called_once_with(
                "Create namespace.",
                user=self.site_admin_user.username,
                namespace=name,
                description=description,
                admins=[self.site_admin_user.username,],
            )

    def test_create_namespace_as_site_admin_with_admin_list(self):
        """
        Ensure a site admin user who creates the namespace is assigned the
        expected admin role along with any further users included in the
        admin list.
        """
        name = "my_namespace"
        description = "This is a test namespace."
        admins = [
            self.admin_user,
        ]
        mock_logger = mock.MagicMock()
        with mock.patch("datastore.logic.logger", mock_logger):
            ns = logic.create_namespace(
                self.site_admin_user, name, description, admins
            )
            self.assertEqual(ns.name, name)
            self.assertEqual(ns.description, description)
            self.assertIn(self.site_admin_user, ns.admins.all())
            mock_logger.msg.assert_called_once_with(
                "Create namespace.",
                user=self.site_admin_user.username,
                namespace=name,
                description=description,
                admins=[
                    self.site_admin_user.username,
                    self.admin_user.username,
                ],
            )

    def test_create_namespace_with_regular_users_username(self):
        """
        Non-site-admin users are allowed to create namespaces that match their
        username.
        """
        name = self.admin_user.username
        description = "This is a test namespace."
        mock_logger = mock.MagicMock()
        with mock.patch("datastore.logic.logger", mock_logger):
            ns = logic.create_namespace(self.admin_user, name, description)
            self.assertEqual(ns.name, name)
            self.assertEqual(ns.description, description)
            self.assertIn(self.admin_user, ns.admins.all())
            mock_logger.msg.assert_called_once_with(
                "Create namespace.",
                user=self.admin_user.username,
                namespace=name,
                description=description,
                admins=[self.admin_user.username,],
            )

    def test_create_namespace_fails_with_non_site_admin_user(self):
        """
        Non-site-admin users are not allowed to create namespaces that do not
        match their username.
        """
        name = "my_namespace"
        description = "This is a test namespace."
        with self.assertRaises(PermissionError):
            logic.create_namespace(self.admin_user, name, description)

    def test_get_namespace_as_normal_user(self):
        """
        Regular users see a limited set of attributes on only those aspects of
        the namespace for which they have privileges to see.

        In this case, the normal user can see the public tag but none of the
        private tags because they are not either a user or reader of those
        tags.
        """
        result = logic.get_namespace(self.normal_user, self.namespace_name)
        self.assertEqual(result["name"], self.namespace_name)
        self.assertEqual(result["description"], self.namespace_description)
        self.assertEqual(1, len(result["tags"]))
        tag1 = result["tags"][0]
        self.assertEqual(tag1["name"], self.public_tag_name)
        self.assertEqual(tag1["description"], self.public_tag_description)
        self.assertEqual(tag1["type_of"], "string")

    def test_get_namespace_as_user(self):
        """
        Regular users see a limited set of attributes on only those aspects of
        the namespace for which they have privileges to see.

        In this case, the user can see the public tag, and the private tag in
        which they are assigned a user role.
        """
        result = logic.get_namespace(self.tag_user, self.namespace_name)
        self.assertEqual(result["name"], self.namespace_name)
        self.assertEqual(result["description"], self.namespace_description)
        self.assertEqual(2, len(result["tags"]))
        tag1 = result["tags"][0]
        tag2 = result["tags"][1]
        self.assertEqual(tag1["name"], self.public_tag_name)
        self.assertEqual(tag1["description"], self.public_tag_description)
        self.assertEqual(tag1["type_of"], "string")
        self.assertEqual(tag2["name"], self.user_tag_name)
        self.assertEqual(tag2["description"], self.user_tag_description)
        self.assertEqual(tag2["type_of"], "boolean")

    def test_get_namespace_as_reader(self):
        """
        Regular users see a limited set of attributes on only those aspects of
        the namespace for which they have privileges to see.

        In this case, the user can see the public tag, and the private tag in
        which they are assigned a reader role.
        """
        result = logic.get_namespace(self.tag_reader, self.namespace_name)
        self.assertEqual(result["name"], self.namespace_name)
        self.assertEqual(result["description"], self.namespace_description)
        self.assertEqual(2, len(result["tags"]))
        tag1 = result["tags"][0]
        tag2 = result["tags"][1]
        self.assertEqual(tag1["name"], self.public_tag_name)
        self.assertEqual(tag1["description"], self.public_tag_description)
        self.assertEqual(tag1["type_of"], "string")
        self.assertEqual(tag2["name"], self.reader_tag_name)
        self.assertEqual(tag2["description"], self.reader_tag_description)
        self.assertEqual(tag2["type_of"], "integer")

    def test_get_namespace_as_namespace_admin(self):
        """
        Users who have the role of the namespace admin see an enhanced view of
        the namespace and child tags: system meta-data about roles, changes
        made and visibility.
        """
        result = logic.get_namespace(self.admin_user, self.namespace_name)
        self.assertEqual(result["name"], self.namespace_name)
        self.assertEqual(result["description"], self.namespace_description)
        self.assertEqual(result["created_by"], self.site_admin_user.username)
        self.assertEqual(
            result["created_on"], str(self.test_namespace.created_on)
        )
        self.assertEqual(result["updated_by"], self.site_admin_user.username)
        self.assertEqual(
            result["updated_on"], str(self.test_namespace.updated_on)
        )
        self.assertEqual(3, len(result["tags"]))
        tag1 = result["tags"][0]
        tag2 = result["tags"][1]
        tag3 = result["tags"][2]
        # Tag 1
        self.assertEqual(tag1["name"], self.public_tag_name)
        self.assertEqual(tag1["description"], self.public_tag_description)
        self.assertEqual(tag1["type_of"], "string")
        self.assertEqual(tag1["created_by"], self.site_admin_user.username)
        self.assertEqual(tag1["created_on"], str(self.public_tag.created_on))
        self.assertFalse(tag1["private"])
        self.assertEqual(tag1["updated_by"], self.site_admin_user.username)
        self.assertEqual(tag1["updated_on"], str(self.public_tag.updated_on))
        self.assertEqual(tag1["users"], [self.site_admin_user.username,])
        self.assertEqual(tag1["readers"], [])
        # Tag 2
        self.assertEqual(tag2["name"], self.reader_tag_name)
        self.assertEqual(tag2["description"], self.reader_tag_description)
        self.assertEqual(tag2["type_of"], "integer")
        self.assertEqual(tag2["created_by"], self.site_admin_user.username)
        self.assertEqual(tag2["created_on"], str(self.reader_tag.created_on))
        self.assertTrue(tag2["private"])
        self.assertEqual(tag2["updated_by"], self.site_admin_user.username)
        self.assertEqual(tag2["updated_on"], str(self.reader_tag.updated_on))
        self.assertEqual(tag2["users"], [self.site_admin_user.username,])
        self.assertEqual(tag2["readers"], [self.tag_reader.username,])
        # Tag 3
        self.assertEqual(tag3["name"], self.user_tag_name)
        self.assertEqual(tag3["description"], self.user_tag_description)
        self.assertEqual(tag3["type_of"], "boolean")
        self.assertEqual(tag3["created_by"], self.site_admin_user.username)
        self.assertEqual(tag3["created_on"], str(self.user_tag.created_on))
        self.assertTrue(tag3["private"])
        self.assertEqual(tag3["updated_by"], self.site_admin_user.username)
        self.assertEqual(tag3["updated_on"], str(self.user_tag.updated_on))
        self.assertEqual(
            tag3["users"],
            [self.site_admin_user.username, self.tag_user.username,],
        )
        self.assertEqual(tag3["readers"], [])

    def test_get_namespace_as_site_admin(self):
        """
        Users who are a site admin see an enhanced view of the namespace and
        child tags: system meta-data about roles, changes made and visibility.
        """
        result = logic.get_namespace(self.site_admin_user, self.namespace_name)
        self.assertEqual(result["name"], self.namespace_name)
        self.assertEqual(result["description"], self.namespace_description)
        self.assertEqual(result["created_by"], self.site_admin_user.username)
        self.assertEqual(
            result["created_on"], str(self.test_namespace.created_on)
        )
        self.assertEqual(result["updated_by"], self.site_admin_user.username)
        self.assertEqual(
            result["updated_on"], str(self.test_namespace.updated_on)
        )
        self.assertEqual(3, len(result["tags"]))
        tag1 = result["tags"][0]
        tag2 = result["tags"][1]
        tag3 = result["tags"][2]
        # Tag 1
        self.assertEqual(tag1["name"], self.public_tag_name)
        self.assertEqual(tag1["description"], self.public_tag_description)
        self.assertEqual(tag1["type_of"], "string")
        self.assertEqual(tag1["created_by"], self.site_admin_user.username)
        self.assertEqual(tag1["created_on"], str(self.public_tag.created_on))
        self.assertFalse(tag1["private"])
        self.assertEqual(tag1["updated_by"], self.site_admin_user.username)
        self.assertEqual(tag1["updated_on"], str(self.public_tag.updated_on))
        self.assertEqual(tag1["users"], [self.site_admin_user.username,])
        self.assertEqual(tag1["readers"], [])
        # Tag 2
        self.assertEqual(tag2["name"], self.reader_tag_name)
        self.assertEqual(tag2["description"], self.reader_tag_description)
        self.assertEqual(tag2["type_of"], "integer")
        self.assertEqual(tag2["created_by"], self.site_admin_user.username)
        self.assertEqual(tag2["created_on"], str(self.reader_tag.created_on))
        self.assertTrue(tag2["private"])
        self.assertEqual(tag2["updated_by"], self.site_admin_user.username)
        self.assertEqual(tag2["updated_on"], str(self.reader_tag.updated_on))
        self.assertEqual(tag2["users"], [self.site_admin_user.username,])
        self.assertEqual(tag2["readers"], [self.tag_reader.username,])
        # Tag 3
        self.assertEqual(tag3["name"], self.user_tag_name)
        self.assertEqual(tag3["description"], self.user_tag_description)
        self.assertEqual(tag3["type_of"], "boolean")
        self.assertEqual(tag3["created_by"], self.site_admin_user.username)
        self.assertEqual(tag3["created_on"], str(self.user_tag.created_on))
        self.assertTrue(tag3["private"])
        self.assertEqual(tag3["updated_by"], self.site_admin_user.username)
        self.assertEqual(tag3["updated_on"], str(self.user_tag.updated_on))
        self.assertEqual(
            tag3["users"],
            [self.site_admin_user.username, self.tag_user.username,],
        )
        self.assertEqual(tag3["readers"], [])

    def test_update_namespace_description_as_admin(self):
        """
        Those with administrator privileges on the namesapce are able to
        update the namespace's description.
        """
        new_description = "This is an updated namespace description."
        mock_logger = mock.MagicMock()
        with mock.patch("datastore.logic.logger", mock_logger):
            result = logic.update_namespace_description(
                self.admin_user, self.namespace_name, new_description
            )
        self.assertEqual(result.description, new_description)
        mock_logger.msg.assert_called_once_with(
            "Update namespace description.",
            user=self.admin_user.username,
            namespace=self.namespace_name,
            description=new_description,
        )

    def test_update_namespace_description_as_site_admin(self):
        """
        Those with site administrator privileges are able to update the
        namespace's description.
        """
        new_description = "This is an updated namespace description."
        mock_logger = mock.MagicMock()
        with mock.patch("datastore.logic.logger", mock_logger):
            result = logic.update_namespace_description(
                self.site_admin_user, self.namespace_name, new_description
            )
        self.assertEqual(result.description, new_description)
        mock_logger.msg.assert_called_once_with(
            "Update namespace description.",
            user=self.site_admin_user.username,
            namespace=self.namespace_name,
            description=new_description,
        )

    def test_update_namespace_description_as_normal_user(self):
        """
        Normal users may not update a namespace's description - a
        PermissionError is raised as a result.
        """
        new_description = "This is an updated namespace description."
        with self.assertRaises(PermissionError):
            logic.update_namespace_description(
                self.normal_user, self.namespace_name, new_description
            )

    def test_add_namespace_admins_as_admin(self):
        """
        Admin users are allowed to add other users to the admin role.
        """
        new_admins = [self.normal_user, self.tag_reader]
        mock_logger = mock.MagicMock()
        with mock.patch("datastore.logic.logger", mock_logger):
            result = logic.add_namespace_admins(
                self.admin_user, self.namespace_name, new_admins
            )
        current_admins = result.admins.all()
        for user in new_admins:
            self.assertIn(user, current_admins)
        mock_logger.msg.assert_called_once_with(
            "Add namespace administrators.",
            user=self.admin_user.username,
            namespace=self.namespace_name,
            admins=[u.username for u in new_admins],
        )

    def test_add_namespace_admins_as_site_admin(self):
        """
        Site admin users are allowed to add other users to the admin role.
        """
        new_admins = [self.normal_user, self.tag_reader]
        mock_logger = mock.MagicMock()
        with mock.patch("datastore.logic.logger", mock_logger):
            result = logic.add_namespace_admins(
                self.site_admin_user, self.namespace_name, new_admins
            )
        current_admins = result.admins.all()
        for user in new_admins:
            self.assertIn(user, current_admins)
        mock_logger.msg.assert_called_once_with(
            "Add namespace administrators.",
            user=self.site_admin_user.username,
            namespace=self.namespace_name,
            admins=[u.username for u in new_admins],
        )

    def test_add_namespace_admins_as_normal_user(self):
        """
        Normal users may not add other users to the admin role - a
        PermissionError is raised as a result.
        """
        new_admins = [self.normal_user, self.tag_reader]
        with self.assertRaises(PermissionError):
            logic.add_namespace_admins(
                self.normal_user, self.namespace_name, new_admins
            )

    def test_remove_namespace_admins_as_admin(self):
        """
        Admin users are allowed to remove other users (including themselves)
        from the admin role.
        """
        old_admins = [self.admin_user, self.tag_reader]
        mock_logger = mock.MagicMock()
        with mock.patch("datastore.logic.logger", mock_logger):
            result = logic.remove_namespace_admins(
                self.admin_user, self.namespace_name, old_admins
            )
        current_admins = result.admins.all()
        for user in old_admins:
            self.assertNotIn(user, current_admins)
        mock_logger.msg.assert_called_once_with(
            "Remove namespace administrators.",
            user=self.admin_user.username,
            namespace=self.namespace_name,
            admins=[u.username for u in old_admins],
        )

    def test_remove_namespace_admins_as_site_admin(self):
        """
        Site admin users are allowed to remove other users from the admin role.
        """
        old_admins = [self.admin_user, self.tag_reader]
        mock_logger = mock.MagicMock()
        with mock.patch("datastore.logic.logger", mock_logger):
            result = logic.remove_namespace_admins(
                self.site_admin_user, self.namespace_name, old_admins
            )
        current_admins = result.admins.all()
        for user in old_admins:
            self.assertNotIn(user, current_admins)
        mock_logger.msg.assert_called_once_with(
            "Remove namespace administrators.",
            user=self.site_admin_user.username,
            namespace=self.namespace_name,
            admins=[u.username for u in old_admins],
        )

    def test_remove_namespace_admins_as_normal_user(self):
        """
        Normal users may not remove other users from the admin role - a
        PermissionError is raised as a result.
        """
        old_admins = [
            self.admin_user,
        ]
        with self.assertRaises(PermissionError):
            logic.remove_namespace_admins(
                self.normal_user, self.namespace_name, old_admins
            )


class TagTestCase(TestCase):
    """
    Exercises the tag related administrative functions.
    """

    def setUp(self):
        self.site_admin_user = models.User.objects.create_user(
            username="site_admin_user",
            email="test@user.com",
            password="password",
            is_superuser=True,
        )
        self.admin_user = models.User.objects.create_user(
            username="admin_user", email="test2@user.com", password="password",
        )
        self.tag_user = models.User.objects.create_user(
            username="tag_user", email="test3@user.com", password="password",
        )
        self.tag_reader = models.User.objects.create_user(
            username="tag_reader", email="test4@user.com", password="password",
        )
        self.normal_user = models.User.objects.create_user(
            username="normal_user",
            email="test5@user.com",
            password="password",
        )
        self.namespace_name = "test_namespace"
        self.namespace_description = "This is a test namespace."
        self.test_namespace = logic.create_namespace(
            self.site_admin_user,
            self.namespace_name,
            self.namespace_description,
            admins=[self.admin_user,],
        )
        self.public_tag_name = "public_tag"
        self.public_tag_description = "This is a public tag."
        self.public_tag_type_of = "s"
        self.public_tag = logic.create_tag(
            user=self.admin_user,
            name=self.public_tag_name,
            description=self.public_tag_description,
            type_of=self.public_tag_type_of,
            namespace=self.test_namespace,
            private=False,
        )
        self.user_tag_name = "user_tag"
        self.user_tag_description = "This is a user tag."
        self.user_tag_type_of = "b"
        self.user_tag = logic.create_tag(
            user=self.admin_user,
            name=self.user_tag_name,
            description=self.user_tag_description,
            type_of=self.user_tag_type_of,
            namespace=self.test_namespace,
            private=True,
            users=[self.tag_user,],
        )
        self.reader_tag_name = "reader_tag"
        self.reader_tag_description = "This is a reader tag."
        self.reader_tag_type_of = "i"
        self.reader_tag = logic.create_tag(
            user=self.admin_user,
            name=self.reader_tag_name,
            description=self.reader_tag_description,
            type_of=self.reader_tag_type_of,
            namespace=self.test_namespace,
            private=True,
            readers=[self.tag_reader,],
        )

    def test_create_tag_as_site_admin(self):
        """
        Ensure a site admin user who creates the tag is assigned the
        expected user role and the tag's creation is logged.
        """
        name = "my_tag"
        description = "This is a test tag."
        type_of = "s"  # string
        is_private = False
        mock_logger = mock.MagicMock()
        with mock.patch("datastore.logic.logger", mock_logger):
            tag = logic.create_tag(
                self.site_admin_user,
                name,
                description,
                type_of,
                self.test_namespace,
                is_private,
            )
            self.assertEqual(tag.name, name)
            self.assertEqual(tag.description, description)
            self.assertEqual(tag.type_of, type_of)
            self.assertEqual(tag.namespace, self.test_namespace)
            self.assertFalse(tag.private)
            self.assertIn(self.site_admin_user, tag.users.all())
            self.assertEqual(0, len(tag.readers.all()))
            mock_logger.msg.assert_called_once_with(
                "Create tag.",
                user=self.site_admin_user.username,
                name=name,
                description=description,
                type_of=tag.get_type_of_display(),
                namespace=self.test_namespace.name,
                private=is_private,
                users=[self.site_admin_user.username,],
                readers=[],
            )

    def test_create_tag_as_admin(self):
        """
        Ensure a namespace admin user who creates the tag is assigned the
        expected user role and the tag's creation is logged.
        """
        name = "my_tag"
        description = "This is a test tag."
        type_of = "s"  # string
        is_private = False
        mock_logger = mock.MagicMock()
        with mock.patch("datastore.logic.logger", mock_logger):
            tag = logic.create_tag(
                self.admin_user,
                name,
                description,
                type_of,
                self.test_namespace,
                is_private,
            )
            self.assertEqual(tag.name, name)
            self.assertEqual(tag.description, description)
            self.assertEqual(tag.type_of, type_of)
            self.assertEqual(tag.namespace, self.test_namespace)
            self.assertFalse(tag.private)
            self.assertIn(self.admin_user, tag.users.all())
            self.assertEqual(0, len(tag.readers.all()))
            mock_logger.msg.assert_called_once_with(
                "Create tag.",
                user=self.admin_user.username,
                name=name,
                description=description,
                type_of=tag.get_type_of_display(),
                namespace=self.test_namespace.name,
                private=is_private,
                users=[self.admin_user.username,],
                readers=[],
            )

    def test_create_tag_with_users_and_readers_list(self):
        """
        If there are users with users and readers roles passed into the
        create_tag function, then they are found with the expected roles in
        relation to the tag.
        """
        name = "my_tag"
        description = "This is a test tag."
        type_of = "s"  # string
        is_private = False
        users = [
            self.tag_user,
        ]
        readers = [
            self.tag_reader,
        ]
        mock_logger = mock.MagicMock()
        with mock.patch("datastore.logic.logger", mock_logger):
            tag = logic.create_tag(
                self.site_admin_user,
                name,
                description,
                type_of,
                self.test_namespace,
                is_private,
                users,
                readers,
            )
            self.assertEqual(tag.name, name)
            self.assertEqual(tag.description, description)
            self.assertEqual(tag.type_of, type_of)
            self.assertEqual(tag.namespace, self.test_namespace)
            self.assertFalse(tag.private)
            self.assertEqual(2, len(tag.users.all()))
            self.assertIn(self.site_admin_user, tag.users.all())
            self.assertIn(self.tag_user, tag.users.all())
            self.assertEqual(1, len(tag.readers.all()))
            self.assertIn(self.tag_reader, tag.readers.all())
            mock_logger.msg.assert_called_once_with(
                "Create tag.",
                user=self.site_admin_user.username,
                name=name,
                description=description,
                type_of=tag.get_type_of_display(),
                namespace=self.test_namespace.name,
                private=is_private,
                users=[self.site_admin_user.username, self.tag_user.username,],
                readers=[self.tag_reader.username,],
            )

    def test_create_tag_with_normal_user(self):
        """
        A user who isn't a site admin or who has the role of admin for the
        referenced namespace cannot create a new tag. A PermissionError is
        raised instead.
        """
        name = "my_tag"
        description = "This is a test tag."
        type_of = "s"  # string
        is_private = False
        with self.assertRaises(PermissionError):
            logic.create_tag(
                self.normal_user,
                name,
                description,
                type_of,
                self.test_namespace,
                is_private,
            )

    def test_get_tag_as_admin_user(self):
        """
        Those with administrator privileges on the namespace are able to see
        the full metadata associated with the referenced tag.
        """
        n = models.Namespace.objects.get(name=self.namespace_name)
        tag = models.Tag.objects.get(name=self.public_tag_name, namespace=n)
        result = logic.get_tag(
            self.admin_user, self.public_tag_name, self.namespace_name
        )
        self.assertEqual(result["name"], tag.name)
        self.assertEqual(result["namespace"], n.name)
        self.assertEqual(result["description"], tag.description)
        self.assertEqual(result["path"], tag.path)
        self.assertEqual(result["type_of"], tag.get_type_of_display())
        self.assertEqual(result["private"], tag.private)
        self.assertEqual(
            result["users"], [user.username for user in tag.users.all()]
        )
        self.assertEqual(
            result["readers"],
            [reader.username for reader in tag.readers.all()],
        )
        self.assertEqual(result["created_by"], tag.created_by.username)
        self.assertEqual(result["created_on"], str(tag.created_on))
        self.assertEqual(result["updated_by"], tag.updated_by.username)
        self.assertEqual(result["updated_on"], str(tag.updated_on))

    def test_get_tag_as_tag_user(self):
        """
        Those with user privileges on the tag are able to see limited metadata
        associated with the referenced tag.
        """
        n = models.Namespace.objects.get(name=self.namespace_name)
        tag = models.Tag.objects.get(name=self.public_tag_name, namespace=n)
        tag.users.add(self.tag_user)
        tag.private = True
        tag.save()
        result = logic.get_tag(
            self.tag_user, self.public_tag_name, self.namespace_name
        )
        self.assertEqual(result["name"], tag.name)
        self.assertEqual(result["namespace"], n.name)
        self.assertEqual(result["description"], tag.description)
        self.assertEqual(result["path"], tag.path)
        self.assertEqual(result["type_of"], tag.get_type_of_display())
        self.assertEqual(result["private"], tag.private)

    def test_get_tag_as_tag_reader(self):
        """
        Those with reader privileges on the tag are able to see limited
        metadata associated with the referenced tag.
        """
        n = models.Namespace.objects.get(name=self.namespace_name)
        tag = models.Tag.objects.get(name=self.public_tag_name, namespace=n)
        tag.readers.add(self.tag_reader)
        tag.private = True
        tag.save()
        result = logic.get_tag(
            self.tag_reader, self.public_tag_name, self.namespace_name
        )
        self.assertEqual(result["name"], tag.name)
        self.assertEqual(result["namespace"], n.name)
        self.assertEqual(result["description"], tag.description)
        self.assertEqual(result["path"], tag.path)
        self.assertEqual(result["type_of"], tag.get_type_of_display())
        self.assertEqual(result["private"], tag.private)

    def test_get_tag_as_normal_user(self):
        """
        Normal users can see limited metadata associated with the referenced
        non-private tag.
        """
        n = models.Namespace.objects.get(name=self.namespace_name)
        tag = models.Tag.objects.get(name=self.public_tag_name, namespace=n)
        result = logic.get_tag(
            self.normal_user, self.public_tag_name, self.namespace_name
        )
        self.assertEqual(result["name"], tag.name)
        self.assertEqual(result["namespace"], n.name)
        self.assertEqual(result["description"], tag.description)
        self.assertEqual(result["path"], tag.path)
        self.assertEqual(result["type_of"], tag.get_type_of_display())
        self.assertEqual(result["private"], tag.private)

    def test_get_tag_as_private_normal_user(self):
        """
        Normal users cannot see any metadata associated with a non-private tag.
        Results in a PermissionError being thrown.
        """
        n = models.Namespace.objects.get(name=self.namespace_name)
        tag = models.Tag.objects.get(name=self.public_tag_name, namespace=n)
        tag.private = True
        tag.save()
        with self.assertRaises(PermissionError):
            logic.get_tag(
                self.normal_user, self.public_tag_name, self.namespace_name
            )

    def test_update_tag_description_as_admin(self):
        """
        Those with administrator privileges on the namesapce are able to
        update the tag's description.
        """
        new_description = "This is an updated tag description."
        mock_logger = mock.MagicMock()
        with mock.patch("datastore.logic.logger", mock_logger):
            result = logic.update_tag_description(
                self.admin_user,
                self.public_tag_name,
                self.namespace_name,
                new_description,
            )
        self.assertEqual(result.description, new_description)
        mock_logger.msg.assert_called_once_with(
            "Update tag description.",
            user=self.admin_user.username,
            tag=self.public_tag_name,
            namespace=self.namespace_name,
            description=new_description,
        )

    def test_update_tag_description_as_site_admin(self):
        """
        Those with site administrator privileges are able to update the
        tag's description.
        """
        new_description = "This is an updated tag description."
        mock_logger = mock.MagicMock()
        with mock.patch("datastore.logic.logger", mock_logger):
            result = logic.update_tag_description(
                self.site_admin_user,
                self.public_tag_name,
                self.namespace_name,
                new_description,
            )
        self.assertEqual(result.description, new_description)
        mock_logger.msg.assert_called_once_with(
            "Update tag description.",
            user=self.site_admin_user.username,
            tag=self.public_tag_name,
            namespace=self.namespace_name,
            description=new_description,
        )

    def test_update_tag_description_as_normal_user(self):
        """
        Normal users may not update a namespace's description - a
        PermissionError is raised as a result.
        """
        new_description = "This is an updated namespace description."
        with self.assertRaises(PermissionError):
            logic.update_tag_description(
                self.normal_user,
                self.public_tag_name,
                self.namespace_name,
                new_description,
            )

    def test_set_tag_private_as_admin(self):
        """
        Those with administrator privileges on the namesapce are able to
        update the tag's "private" flag.
        """
        self.assertFalse(self.public_tag.private)
        mock_logger = mock.MagicMock()
        with mock.patch("datastore.logic.logger", mock_logger):
            result = logic.set_tag_private(
                self.admin_user,
                self.public_tag_name,
                self.namespace_name,
                True,
            )
        self.assertTrue(result.private)
        mock_logger.msg.assert_called_once_with(
            "Update tag privacy.",
            user=self.admin_user.username,
            tag=self.public_tag_name,
            namespace=self.namespace_name,
            private=True,
        )

    def test_set_tag_private_as_site_admin(self):
        """
        Those with site administrator privileges are able to update the
        tag's "private" flag.
        """
        self.assertFalse(self.public_tag.private)
        mock_logger = mock.MagicMock()
        with mock.patch("datastore.logic.logger", mock_logger):
            result = logic.set_tag_private(
                self.site_admin_user,
                self.public_tag_name,
                self.namespace_name,
                True,
            )
        self.assertTrue(result.private)
        mock_logger.msg.assert_called_once_with(
            "Update tag privacy.",
            user=self.site_admin_user.username,
            tag=self.public_tag_name,
            namespace=self.namespace_name,
            private=True,
        )

    def test_set_tag_private_as_normal_user(self):
        """
        Normal users may not update a tag's "private" flag - a
        PermissionError is raised as a result.
        """
        self.assertFalse(self.public_tag.private)
        with self.assertRaises(PermissionError):
            logic.set_tag_private(
                self.normal_user,
                self.public_tag_name,
                self.namespace_name,
                True,
            )

    def test_add_tag_users_as_admin(self):
        """
        Admin users are allowed to add users to the users role.
        """
        new_users = [
            self.normal_user,
            self.tag_user,
        ]
        mock_logger = mock.MagicMock()
        with mock.patch("datastore.logic.logger", mock_logger):
            result = logic.add_tag_users(
                self.admin_user,
                self.public_tag_name,
                self.namespace_name,
                new_users,
            )
        current_users = result.users.all()
        for user in new_users:
            self.assertIn(user, current_users)
        mock_logger.msg.assert_called_once_with(
            "Add tag users.",
            user=self.admin_user.username,
            tag=self.public_tag_name,
            namespace=self.namespace_name,
            users=[u.username for u in new_users],
        )

    def test_add_tag_users_as_site_admin(self):
        """
        Site admin users are allowed to add users to the users role for the
        tag.
        """
        new_users = [
            self.normal_user,
            self.tag_user,
        ]
        mock_logger = mock.MagicMock()
        with mock.patch("datastore.logic.logger", mock_logger):
            result = logic.add_tag_users(
                self.site_admin_user,
                self.public_tag_name,
                self.namespace_name,
                new_users,
            )
        current_users = result.users.all()
        for user in new_users:
            self.assertIn(user, current_users)
        mock_logger.msg.assert_called_once_with(
            "Add tag users.",
            user=self.site_admin_user.username,
            tag=self.public_tag_name,
            namespace=self.namespace_name,
            users=[u.username for u in new_users],
        )

    def test_add_tag_users_as_normal_user(self):
        """
        Normal users may not add other users to the users role - a
        PermissionError is raised as a result.
        """
        new_users = [
            self.normal_user,
            self.tag_user,
        ]
        with self.assertRaises(PermissionError):
            logic.add_tag_users(
                self.normal_user,
                self.public_tag_name,
                self.namespace_name,
                new_users,
            )

    def test_remove_tag_users_as_admin(self):
        """
        Admin users are allowed to remove other users (including themselves)
        from the users role associated with the tag.
        """
        old_users = [self.tag_user]
        logic.add_tag_users(
            self.site_admin_user,
            self.public_tag_name,
            self.namespace_name,
            old_users,
        )
        mock_logger = mock.MagicMock()
        with mock.patch("datastore.logic.logger", mock_logger):
            result = logic.remove_tag_users(
                self.admin_user,
                self.public_tag_name,
                self.namespace_name,
                old_users,
            )
        current_users = result.users.all()
        for user in old_users:
            self.assertNotIn(user, current_users)
        mock_logger.msg.assert_called_once_with(
            "Remove tag users.",
            user=self.admin_user.username,
            tag=self.public_tag_name,
            namespace=self.namespace_name,
            users=[u.username for u in old_users],
        )

    def test_remove_tag_users_as_site_admin(self):
        """
        Site admin users are allowed to remove other users from the tag's
        users role.
        """
        old_users = [self.tag_user]
        logic.add_tag_users(
            self.site_admin_user,
            self.public_tag_name,
            self.namespace_name,
            old_users,
        )
        mock_logger = mock.MagicMock()
        with mock.patch("datastore.logic.logger", mock_logger):
            result = logic.remove_tag_users(
                self.site_admin_user,
                self.public_tag_name,
                self.namespace_name,
                old_users,
            )
        current_users = result.users.all()
        for user in old_users:
            self.assertNotIn(user, current_users)
        mock_logger.msg.assert_called_once_with(
            "Remove tag users.",
            user=self.site_admin_user.username,
            tag=self.public_tag_name,
            namespace=self.namespace_name,
            users=[u.username for u in old_users],
        )

    def test_remove_tag_users_as_normal_user(self):
        """
        Normal users may not remove other users from the tag's users role - a
        PermissionError is raised as a result.
        """
        old_users = [
            self.tag_user,
        ]
        with self.assertRaises(PermissionError):
            logic.remove_tag_users(
                self.normal_user,
                self.public_tag_name,
                self.namespace_name,
                old_users,
            )

    def test_add_tag_readers_as_admin(self):
        """
        Admin users are allowed to add users to the readers role.
        """
        new_readers = [
            self.normal_user,
            self.tag_reader,
        ]
        mock_logger = mock.MagicMock()
        with mock.patch("datastore.logic.logger", mock_logger):
            result = logic.add_tag_readers(
                self.admin_user,
                self.public_tag_name,
                self.namespace_name,
                new_readers,
            )
        current_readers = result.readers.all()
        for user in new_readers:
            self.assertIn(user, current_readers)
        mock_logger.msg.assert_called_once_with(
            "Add tag readers.",
            user=self.admin_user.username,
            tag=self.public_tag_name,
            namespace=self.namespace_name,
            readers=[u.username for u in new_readers],
        )

    def test_add_tag_readers_as_site_admin(self):
        """
        Site admin users are allowed to add users to the readers role for the
        tag.
        """
        new_readers = [
            self.normal_user,
            self.tag_reader,
        ]
        mock_logger = mock.MagicMock()
        with mock.patch("datastore.logic.logger", mock_logger):
            result = logic.add_tag_readers(
                self.site_admin_user,
                self.public_tag_name,
                self.namespace_name,
                new_readers,
            )
        current_readers = result.readers.all()
        for user in new_readers:
            self.assertIn(user, current_readers)
        mock_logger.msg.assert_called_once_with(
            "Add tag readers.",
            user=self.site_admin_user.username,
            tag=self.public_tag_name,
            namespace=self.namespace_name,
            readers=[u.username for u in new_readers],
        )

    def test_add_tag_readers_as_normal_user(self):
        """
        Normal users may not add other users to the readers role - a
        PermissionError is raised as a result.
        """
        new_readers = [
            self.normal_user,
            self.tag_user,
        ]
        with self.assertRaises(PermissionError):
            logic.add_tag_readers(
                self.normal_user,
                self.public_tag_name,
                self.namespace_name,
                new_readers,
            )

    def test_remove_tag_readers_as_admin(self):
        """
        Admin users are allowed to remove other users (including themselves)
        from the readers role associated with the tag.
        """
        old_readers = [self.tag_reader]
        logic.add_tag_readers(
            self.site_admin_user,
            self.public_tag_name,
            self.namespace_name,
            old_readers,
        )
        mock_logger = mock.MagicMock()
        with mock.patch("datastore.logic.logger", mock_logger):
            result = logic.remove_tag_readers(
                self.admin_user,
                self.public_tag_name,
                self.namespace_name,
                old_readers,
            )
        current_readers = result.readers.all()
        for user in old_readers:
            self.assertNotIn(user, current_readers)
        mock_logger.msg.assert_called_once_with(
            "Remove tag readers.",
            user=self.admin_user.username,
            tag=self.public_tag_name,
            namespace=self.namespace_name,
            readers=[u.username for u in old_readers],
        )

    def test_remove_tag_readers_as_site_admin(self):
        """
        Site admin users are allowed to remove other users from the tag's
        readers role.
        """
        old_readers = [self.tag_reader]
        logic.add_tag_readers(
            self.site_admin_user,
            self.public_tag_name,
            self.namespace_name,
            old_readers,
        )
        mock_logger = mock.MagicMock()
        with mock.patch("datastore.logic.logger", mock_logger):
            result = logic.remove_tag_readers(
                self.site_admin_user,
                self.public_tag_name,
                self.namespace_name,
                old_readers,
            )
        current_readers = result.readers.all()
        for user in old_readers:
            self.assertNotIn(user, current_readers)
        mock_logger.msg.assert_called_once_with(
            "Remove tag readers.",
            user=self.site_admin_user.username,
            tag=self.public_tag_name,
            namespace=self.namespace_name,
            readers=[u.username for u in old_readers],
        )

    def test_remove_tag_readers_as_normal_user(self):
        """
        Normal users may not remove other users from the tag's readers role - a
        PermissionError is raised as a result.
        """
        old_readers = [
            self.tag_reader,
        ]
        with self.assertRaises(PermissionError):
            logic.remove_tag_readers(
                self.normal_user,
                self.public_tag_name,
                self.namespace_name,
                old_readers,
            )

    def test_get_users_query_as_site_admin_user(self):
        """
        Given a user and a list of candidate tags, ensure a QuerySet is
        returned that finds all the Tag instances the user is able to use to
        annotate values onto objects.

        Site admin users always match all tags.
        """
        tag_list = [
            (self.namespace_name, self.public_tag_name),
            (self.namespace_name, self.user_tag_name),
            (self.namespace_name, self.reader_tag_name),
        ]
        result = logic.get_users_query(self.site_admin_user, tag_list)
        self.assertEqual(3, len(result))
        self.assertIn(self.public_tag, result)
        self.assertIn(self.user_tag, result)
        self.assertIn(self.reader_tag, result)

    def test_get_users_query_as_admin_user(self):
        """
        Given a user and a list of candidate tags, ensure a QuerySet is
        returned that finds all the Tag instances the user is able to use to
        annotate values onto objects.

        Users who are administrators of the parent namespace always match all
        child tags.
        """
        tag_list = [
            (self.namespace_name, self.public_tag_name),
            (self.namespace_name, self.user_tag_name),
            (self.namespace_name, self.reader_tag_name),
        ]
        result = logic.get_users_query(self.admin_user, tag_list)
        self.assertEqual(3, len(result))
        self.assertIn(self.public_tag, result)
        self.assertIn(self.user_tag, result)
        self.assertIn(self.reader_tag, result)

    def test_get_users_query_as_user(self):
        """
        Given a user and a list of candidate tags, ensure a QuerySet is
        returned that finds all the Tag instances the user is able to use to
        annotate values onto objects.

        A user can only see tags for which it has the "user" role.
        """
        tag_list = [
            (self.namespace_name, self.public_tag_name),
            (self.namespace_name, self.user_tag_name),
            (self.namespace_name, self.reader_tag_name),
        ]
        result = logic.get_users_query(self.tag_user, tag_list)
        self.assertEqual(1, len(result))
        self.assertIn(self.user_tag, result)

    def test_get_users_query_as_reader(self):
        """
        Given a user and a list of candidate tags, ensure a QuerySet is
        returned that finds all the Tag instances the user is able to use to
        annotate values onto objects.

        If a user has a reader role associated with a private tag, it makes no
        difference to their ability to be a user of that tag.
        """
        tag_list = [
            (self.namespace_name, self.public_tag_name),
            (self.namespace_name, self.user_tag_name),
            (self.namespace_name, self.reader_tag_name),
        ]
        result = logic.get_users_query(self.tag_reader, tag_list)
        self.assertEqual(0, len(result))

    def test_get_users_query_as_normal_user(self):
        """
        Given a user and a list of candidate tags, ensure a QuerySet is
        returned that finds all the Tag instances the user is able to use to
        annotate values onto objects.

        Users without the "users" role, don't get any matches.
        """
        tag_list = [
            (self.namespace_name, self.public_tag_name),
            (self.namespace_name, self.user_tag_name),
            (self.namespace_name, self.reader_tag_name),
        ]
        result = logic.get_users_query(self.normal_user, tag_list)
        self.assertEqual(0, len(result))

    def test_get_readers_query_as_site_admin(self):
        """
        Given a user and a list of candidate tags, ensure a QuerySet is
        returned that finds all the Tag instances the user is able to use to
        read values from objects (either public tags, or tags for which the
        user has a "reader" role).

        A site admin can always use tags to read values.
        """
        tag_list = [
            (self.namespace_name, self.public_tag_name),
            (self.namespace_name, self.user_tag_name),
            (self.namespace_name, self.reader_tag_name),
        ]
        result = logic.get_readers_query(self.site_admin_user, tag_list)
        self.assertEqual(3, len(result))
        self.assertIn(self.public_tag, result)
        self.assertIn(self.user_tag, result)
        self.assertIn(self.reader_tag, result)

    def test_get_readers_query_as_admin_user(self):
        """
        Given a user and a list of candidate tags, ensure a QuerySet is
        returned that finds all the Tag instances the user is able to use to
        read values from objects (either public tags, or tags for which the
        user has a "reader" role).

        If a user has administrator role for the parent namespace, they can
        always use tags to read values.
        """
        tag_list = [
            (self.namespace_name, self.public_tag_name),
            (self.namespace_name, self.user_tag_name),
            (self.namespace_name, self.reader_tag_name),
        ]
        result = logic.get_readers_query(self.admin_user, tag_list)
        self.assertEqual(3, len(result))
        self.assertIn(self.public_tag, result)
        self.assertIn(self.user_tag, result)
        self.assertIn(self.reader_tag, result)

    def test_get_readers_query_as_tag_reader_user(self):
        """
        Given a user and a list of candidate tags, ensure a QuerySet is
        returned that finds all the Tag instances the user is able to use to
        read values from objects (either public tags, or tags for which the
        user has a "reader" role).

        A user with readers role on a tag can read using that tag.
        """
        tag_list = [
            (self.namespace_name, self.public_tag_name),
            (self.namespace_name, self.user_tag_name),
            (self.namespace_name, self.reader_tag_name),
        ]
        result = logic.get_readers_query(self.tag_reader, tag_list)
        self.assertEqual(2, len(result))
        self.assertIn(self.public_tag, result)
        self.assertIn(self.reader_tag, result)

    def test_get_readers_query_as_tag_user(self):
        """
        Given a user and a list of candidate tags, ensure a QuerySet is
        returned that finds all the Tag instances the user is able to use to
        read values from objects (either public tags, or tags for which the
        user has a "reader" role).

        A user with users role on a tag can also read using that tag.
        """
        tag_list = [
            (self.namespace_name, self.public_tag_name),
            (self.namespace_name, self.user_tag_name),
            (self.namespace_name, self.reader_tag_name),
        ]
        result = logic.get_readers_query(self.tag_user, tag_list)
        self.assertEqual(2, len(result))
        self.assertIn(self.public_tag, result)
        self.assertIn(self.user_tag, result)

    def test_get_readers_query_as_normal_user(self):
        """
        Given a user and a list of candidate tags, ensure a QuerySet is
        returned that finds all the Tag instances the user is able to use to
        read values from objects (either public tags, or tags for which the
        user has a "reader" role).

        Normal users with no particular role only see public tags with which to
        read values.
        """
        tag_list = [
            (self.namespace_name, self.public_tag_name),
            (self.namespace_name, self.user_tag_name),
            (self.namespace_name, self.reader_tag_name),
        ]
        result = logic.get_readers_query(self.normal_user, tag_list)
        self.assertEqual(1, len(result))
        self.assertIn(self.public_tag, result)

    def test_check_users_tags_as_admin_user(self):
        """
        Given a user and a collection of namespace/tag tuples, ensure the
        expected True value is returned if the user has permission to use the
        referenced tags to annotate values onto objects.

        In this case, if a user is an admin of the parent namespace, the
        response is always True.
        """
        tag_list = [
            (self.namespace_name, self.public_tag_name),
            (self.namespace_name, self.user_tag_name),
            (self.namespace_name, self.reader_tag_name),
        ]
        self.assertTrue(logic.check_users_tags(self.admin_user, tag_list))

    def test_check_users_tags_as_site_admin(self):
        """
        Given a user and a collection of namespace/tag tuples, ensure the
        expected True value is returned if the user has permission to use the
        referenced tags to annotate values onto objects.

        In this case, if a user is a site admin so the response is always True.
        """
        tag_list = [
            (self.namespace_name, self.public_tag_name),
            (self.namespace_name, self.user_tag_name),
            (self.namespace_name, self.reader_tag_name),
        ]
        self.assertTrue(logic.check_users_tags(self.site_admin_user, tag_list))

    def test_check_users_tags_as_normal_user(self):
        """
        Given a user and a collection of namespace/tag tuples, ensure the
        expected True value is returned if the user has permission to use the
        referenced tags to annotate values onto objects.

        In this case, if a user is a normal user and the tags are not in scope
        with them, so the result will be False.
        """
        tag_list = [
            (self.namespace_name, self.public_tag_name),
            (self.namespace_name, self.user_tag_name),
            (self.namespace_name, self.reader_tag_name),
        ]
        self.assertFalse(logic.check_users_tags(self.normal_user, tag_list))

    def test_check_users_tags_as_tag_user(self):
        """
        Given a user and a collection of namespace/tag tuples, ensure the
        expected True value is returned if the user has permission to use the
        referenced tags to annotate values onto objects.

        In this case, if a user is a tag user the response is True. If the tag
        collection contains a tag for which the user doesn't have the "user"
        role, then the response if False.
        """
        tag_list = [
            (self.namespace_name, self.user_tag_name),
        ]
        self.assertTrue(logic.check_users_tags(self.tag_user, tag_list))
        tag_list = [
            (self.namespace_name, self.public_tag_name),
            (self.namespace_name, self.user_tag_name),
        ]
        self.assertFalse(logic.check_users_tags(self.tag_user, tag_list))

    def test_check_users_tags_with_duplicate_tags(self):
        """
        Given a user and a collection of namespace/tag tuples, ensure the
        expected True value is returned if the user has permission to use the
        referenced tags to annotate values onto objects.

        If there are duplicates of the same tag, this doesn't effect the
        outcome.
        """
        tag_list = [
            (self.namespace_name, self.user_tag_name),
            (self.namespace_name, self.user_tag_name),
            (self.namespace_name, self.user_tag_name),
            (self.namespace_name, self.user_tag_name),
            (self.namespace_name, self.user_tag_name),
        ]
        self.assertTrue(logic.check_users_tags(self.tag_user, tag_list))

    def test_check_users_tags_as_tag_reader(self):
        """
        Given a user and a collection of namespace/tag tuples, ensure the
        expected True value is returned if the user has permission to use the
        referenced tags to annotate values onto objects.

        In this case, if a user is a tag reader the response is False because
        reader's cannot use the tag to annotate (they can only read values
        associated with it), unless, of course, they are also have the "users"
        role..
        """
        tag_list = [
            (self.namespace_name, self.reader_tag_name),
        ]
        self.assertFalse(logic.check_users_tags(self.tag_reader, tag_list))
