"""
Parses the simple query language into a data structure used to match objects
in the database layer.

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
import structlog  # type: ignore
from typing import Dict


logger = structlog.get_logger()


def parse(query: str) -> Dict:
    """
    Parse the query string and return a dictionary describing the propositions
    and their logical relation to each other.

    The result will be of the form (original query in quotes):

    "namespace/tag > 6"

    {
        "namespace/tag": {
            "operator": ">",
            "value": 6
        },
    }

    Logical operators for "and", "or" and "not" like this (where "and" and "or"
    share the same list like syntax for operands):

    "namespace2/tag2 = True and namespace3/tag3 like 'tuba'"

    {
        "and": [
            "namespace2/tag2": {
                "operator": "=",
                "value": True,
            },
            "namespace3/tag3": {
                "operator": "like",
                "value": "tuba",
            }
        ],
    }

    "namespace2/tag2 = True or namespace3/tag3 like 'tuba'"

    {
        "or": [
            "namespace2/tag2": {
                "operator": "=",
                "value": True,
            },
            "namespace3/tag3": {
                "operator": "like",
                "value": "tuba",
            }
        ],
    }

    "not namespace4/tag4 < 1.234"

    {
        "not": {
            "namespace4/tag4": {
                "operator": "<",
                "value": 1.234,
            }
        }
    }

    Nesting is allowed to build a structured query.
    """
