"""
Parses the simple query language into matching objects in the database layer.
Uses the Sly (https://sly.readthedocs.io/en/latest/) lexer/parser library by
Dave Beazley.

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
from datetime import timedelta
from typing import List
from sly import Lexer  # type: ignore
from dateutil.parser import parse as datetime_parser  # type: ignore


logger = structlog.get_logger()


#: Valid registry names for MIME types. See: RFC6836, RFC4855.
MIME_REGISTRIES = [
    "application",
    "audio",
    "font",
    "example",
    "image",
    "message",
    "model",
    "multipart",
    "text",
    "video",
]


class QueryLexer(Lexer):
    """
    A simple Sly based lexer for the query language.
    """

    tokens = {
        PATH,  # type: ignore # noqa
        STRING,  # type: ignore # noqa
        TRUE,  # type: ignore # noqa
        FALSE,  # type: ignore # noqa
        INT,  # type: ignore # noqa
        FLOAT,  # type: ignore # noqa
        DATETIME,  # type: ignore # noqa
        DURATION,  # type: ignore # noqa
        HAS,  # type: ignore # noqa
        MISSING,  # type: ignore # noqa
        AND,  # type: ignore # noqa
        OR,  # type: ignore # noqa
        MATCHES,  # type: ignore # noqa
        IMATCHES,  # type: ignore # noqa
        IS,  # type: ignore # noqa
        EQ,  # type: ignore # noqa
        NE,  # type: ignore # noqa
        GT,  # type: ignore # noqa
        LT,  # type: ignore # noqa
        GE,  # type: ignore # noqa
        LE,  # type: ignore # noqa
    }

    # Characters to ignore.
    ignore = " \t"

    # Complex tokens - convert tokens to native Python data types.

    @_(r"([\d]{4}-[\d]{2}-[\d]{2})(T[\d]{2}:[\d]{2}:[\d]{2})?(Z|[+-][\d]{2}:[\d]{2})?")  # type: ignore # noqa
    def DATETIME(self, t):
        """
        A datetime expressed as https://www.w3.org/TR/NOTE-datetime. Resolves
        to a Python datetime.
        """
        t.value = datetime_parser(t.value)
        return t

    @_(r"\"([^\\\"]+|\\\"|\\\\)*\"")  # type: ignore
    def STRING(self, t):
        """
        Strings of unicode characters enclosed in double quotes.
        """
        t.value = t.value[1:-1]
        return t

    # Floats must come before integers.
    @_(r"-?\d+\.\d+(e-?\d+)?")  # type: ignore
    def FLOAT(self, t):
        """
        Real numbers (expressed as floating point).
        """
        t.value = float(t.value)
        return t

    @_(r"[\d]+[s|d]{1}")  # type: ignore
    def DURATION(self, t):
        """
        A duration, resolves to a Python timedelta.
        """
        amount = int(t.value[:-1])
        if t.value.endswith("d"):
            # Timedelta of days.
            t.value = timedelta(days=amount)
        else:
            # Timedelta of seconds.
            t.value = timedelta(seconds=amount)
        return t

    @_(r"-?\d+")  # type: ignore
    def INT(self, t):
        """
        Integers.
        """
        t.value = int(t.value)
        return t

    @_(r"(?i)true")  # type: ignore
    def TRUE(self, t):
        """
        True (boolean).
        """
        t.value = True
        return t

    @_(r"(?i)false")  # type: ignore
    def FALSE(self, t):
        """
        False (boolean).
        """
        t.value = False
        return t

    # Line number tracking.

    @_(r"\n+")  # type: ignore
    def ignore_newline(self, t):
        self.lineno += t.value.count("\n")

    # Simple tokens

    literals = {
        "(",
        ")",
    }
    PATH = r"[-\w]+/[-\w]+"
    HAS = r"(?i)has"
    MISSING = r"(?i)missing"
    AND = r"(?i)and"
    OR = r"(?i)or"
    MATCHES = r"(?i)matches"
    IMATCHES = r"(?i)imatches"
    IS = r"(?i)is"
    NE = r"!="
    GE = r">="
    LE = r"<="
    GT = r">"
    LT = r"<"
    EQ = r"="

    # Syntax error handling.

    def error(self, t):
        raise SyntaxError(f"Line {self.lineno}: {t.value[0]}")


# class QueryParser(Parser):
#     """
#     Sly based parser for the query language.
#     """
#
#     tokens = QueryLexer.tokens
#
#     # Grammar rules and actions.


def parse(query: str) -> List[str]:
    """
    Parse the query string and return a list of matching object_ids.
    """
    # Tokenize.
    # lexer = QueryLexer()
    # tokens = lexer.tokenize(str)
    # tags = lexer.tagpaths
    # Check tag read permissions.
    # Parse.
    # Extract matching object_ids.
