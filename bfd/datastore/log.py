"""
Configure structured logging.

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
import structlog  # type: ignore
import platform


# Gather host system information.
host = platform.uname()


def host_info(logger, log_method, event_dict: dict) -> dict:
    """
    Add useful information to each log entry about the system upon which the
    application is running.
    """
    event_dict["hostname"] = host.node  # hostname of the computer.
    event_dict["system"] = host.system  # OS name, e.g. "Linux".
    event_dict["release"] = host.release  # OS release name.
    event_dict["version"] = host.version  # OS release number.
    event_dict["machine"] = host.machine  # machine architecture, e.g. "i386".
    event_dict["processor"] = host.processor  # processor model.
    return event_dict


# Each log will be timestamped (ISO_8601), have details of the host system,
# nicely format exceptions if found via the 'exc_info' key, and render as JSON.
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        host_info,
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ]
)
