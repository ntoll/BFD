"""
Tests exercising the log module.

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
