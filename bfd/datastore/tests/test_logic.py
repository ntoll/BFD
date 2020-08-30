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
        result = logic.update_namespace_description(
            self.admin_user, self.namespace_name, new_description
        )
        self.assertEqual(result.description, new_description)

    def test_update_namespace_description_as_site_admin(self):
        """
        Those with site administrator privileges are able to update the
        namespace's description.
        """
        new_description = "This is an updated namespace description."
        result = logic.update_namespace_description(
            self.site_admin_user, self.namespace_name, new_description
        )
        self.assertEqual(result.description, new_description)

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
        result = logic.add_namespace_admins(
            self.admin_user, self.namespace_name, new_admins
        )
        current_admins = result.admins.all()
        for user in new_admins:
            self.assertIn(user, current_admins)

    def test_add_namespace_admins_as_site_admin(self):
        """
        Site admin users are allowed to add other users to the admin role.
        """
        new_admins = [self.normal_user, self.tag_reader]
        result = logic.add_namespace_admins(
            self.site_admin_user, self.namespace_name, new_admins
        )
        current_admins = result.admins.all()
        for user in new_admins:
            self.assertIn(user, current_admins)

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
        result = logic.remove_namespace_admins(
            self.admin_user, self.namespace_name, old_admins
        )
        current_admins = result.admins.all()
        for user in old_admins:
            self.assertNotIn(user, current_admins)

    def test_remove_namespace_admins_as_site_admin(self):
        """
        Site admin users are allowed to remove other users from the admin role.
        """
        old_admins = [self.admin_user, self.tag_reader]
        result = logic.remove_namespace_admins(
            self.site_admin_user, self.namespace_name, old_admins
        )
        current_admins = result.admins.all()
        for user in old_admins:
            self.assertNotIn(user, current_admins)

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
