"""
Tests exercising the utils module.

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
import uuid
from django.test import TestCase
from django.conf import settings
from datastore import utils


class UtilsTestCase(TestCase):
    """
    Tests relating to the global utility funtions.
    """

    def test_get_uuid(self):
        """
        Ensure the get_uuid method returns a UUID5 based upon the
        settings.BFD_UUID and the passed in namespace and tag name.
        """
        namespace = "my_namespace"
        tag = "my_tag"
        expected = uuid.uuid5(uuid.uuid5(settings.BFD_UUID, namespace), tag)
        self.assertEqual(utils.get_uuid(namespace, tag), expected)
