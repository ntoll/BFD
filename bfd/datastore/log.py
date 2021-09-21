"""
Configure structured logging.

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
