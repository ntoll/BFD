"""
Tests exercising the log module.

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
import platform
from django.test import TestCase
from datastore import log


class LogTestCase(TestCase):
    """
    Tests relating to the structlog setup in the BFD.
    """

    def test_host_info(self):
        """
        Ensure the correct values are annotated to the event_dict:

        * "hostname" - hostname of the computer.
        * "system" - the OS name, e.g. "Linux".
        * "release" - OS's release name.
        * "version" - OS's version number.
        * "machine" - computer's machine architecture, e.g. "i386".
        * "processor" - the computer's processer model.
        """
        event_dict = {}
        log.host_info(None, None, event_dict)
        host_info = platform.uname()
        self.assertEqual(event_dict["hostname"], host_info.node)
        self.assertEqual(event_dict["system"], host_info.system)
        self.assertEqual(event_dict["release"], host_info.release)
        self.assertEqual(event_dict["version"], host_info.version)
        self.assertEqual(event_dict["machine"], host_info.machine)
        self.assertEqual(event_dict["processor"], host_info.processor)
