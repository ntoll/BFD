"""
Parses the simple query language into matching objects in the database layer.
Uses the Sly (https://sly.readthedocs.io/en/latest/) lexer/parser library by
Dave Beazley. Thanks to the "dynamic" nature of SLY, mypy and flake8 complain,
hence all the "type: ignore" and "noqa" comment-flags to silence them.

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
from typing import List, Set, Tuple, Union
from sly import Lexer, Parser  # type: ignore
from dateutil.parser import parse as datetime_parser  # type: ignore
from django.db.models import Q  # type: ignore
from django.utils import timezone  # type: ignore
from datastore import utils
from datastore import models


logger = structlog.get_logger()


class QueryLexer(Lexer):
    """
    A simple Sly based lexer for the query language.
    """

    def __init__(self):
        super().__init__()
        self.tag_paths = set()

    tokens = {
        PATH,  # type: ignore # noqa
        MIME,  # type: ignore # noqa
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
        IIS,  # type: ignore # noqa
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
        to a Python datetime. If the parsed datetime doesn't include timezone
        information, a timezone is added based on the current Django timezone
        configuration.
        """
        dt = datetime_parser(t.value)
        if not dt.tzinfo:
            dt = timezone.make_aware(dt)
        t.value = dt
        return t

    @_(r"\"([^\\\"]+|\\\"|\\\\)*\"")  # type: ignore
    def STRING(self, t):
        """
        Strings of unicode characters enclosed in double quotes.
        """
        t.value = t.value[1:-1]
        return t

    @_(r"[-\w]+/[-\w]+")  # type: ignore
    def PATH(self, t):
        """
        Paths are added to the tag_path set so their read permission can be
        checked before evaluating operations. No other change is made.
        """
        self.tag_paths.add(t.value)
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

    @_(r"(?i)mime:(application|audio|font|example|image|message|model|multipart|text|video){1}/[-\.\w]+[\+\-\w]*")  # type: ignore # noqa
    def MIME(self, t):
        """
        Remove the prepended "mime:"
        """
        t.value = t.value[5:]
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
    HAS = r"(?i)has"
    MISSING = r"(?i)missing"
    AND = r"(?i)and"
    OR = r"(?i)or"
    MATCHES = r"(?i)matches"
    IMATCHES = r"(?i)imatches"
    IS = r"(?i)is"
    IIS = r"(?i)iis"
    NE = r"!="
    GE = r">="
    LE = r"<="
    GT = r">"
    LT = r"<"
    EQ = r"="

    # Syntax error handling.

    def error(self, t):
        raise SyntaxError(
            f"Unknown token: line {self.lineno}, character: {t.value[0]}"
        )


class QueryParser(Parser):
    """
    Sly based parser for the query language.
    """

    tokens = QueryLexer.tokens

    precedence = (("left", "AND", "OR"),)

    def __init__(self, user: models.User, tag_paths: Set[str]):
        super().__init__()
        # tagpaths are used to check read permissions for the query and
        # retrieve tag instances to use to get the result sets.
        tag_tuples: List[Tuple[str, str]] = []
        for path in tag_paths:
            n, t = path.split("/")
            tag_tuples.append((n, t))
        tags_to_read = models.get_readers_query(user, tag_tuples)
        self.tags = {}
        for tag in tags_to_read:
            # self.tags contains tag instances to use to create result sets
            # from the database.
            self.tags[tag.uuid] = tag
        if len(tags_to_read) != len(tag_paths):
            # The user doesn't have permission to read certain tags, or the
            # referenced tags do not exist. So raise a value error referencing
            # the problem tags so the user has a clue where the problem may be
            # found.
            missing_tags = []
            for tag in tag_paths:
                n, t = path.split("/")
                uuid = utils.get_uuid(n, t)
                if uuid not in self.tags:
                    missing_tags.append(tag)
            raise ValueError(
                "The following tags cannot be read: " + ", ".join(missing_tags)
            )

    def _evaluate_query(
        self,
        tag_path: str,
        applies_to: Set[str],
        operator: str,
        query: Union[None, Q] = None,
        exclude: Union[None, Q] = None,
    ) -> Set[str]:
        """
        Match objects annotated with the tag_path via the referenced query and
        optional exclusion.

        If the tag is not of a type to which the query applies, raise a
        ValueError exception.

        Returns a set containing the object_ids of matches.
        """
        n, t = tag_path.split("/")
        uuid = utils.get_uuid(n, t)
        tag = self.tags.get(uuid)
        if tag:
            type_of = tag.get_type_of_display()
            if type_of in applies_to:
                return tag.filter(query, exclude)
            else:
                raise ValueError(
                    f'Cannot use operator "{operator}" on tag: {tag_path} '
                    f"({type_of})"
                )
        else:
            raise ValueError(f"Unknown tag: {tag_path}")

    # Grammar rules and actions.

    @_('"(" expr ")"')  # type: ignore
    def expr(self, p):  # type: ignore # noqa
        """
        Parenthesis contain the scope of the enclosed expression.
        """
        return p.expr

    @_("query")  # type: ignore
    def expr(self, p):  # type: ignore # noqa
        """
        A query, on its own, is a valid expression.
        """
        return p.query

    @_("expr AND expr")  # type: ignore
    def expr(self, p):  # type: ignore # noqa
        """
        The result sets from two queries can be treated with a logical AND
        (set intersection).
        """
        return p.expr0.intersection(p.expr1)

    @_("expr AND exclusion")  # type: ignore
    def expr(self, p):  # type: ignore # noqa
        """
        The result set from a logical AND can exclude results for objects
        that have a certain tag.
        """
        n, t = p.exclusion.split("/")
        uuid = utils.get_uuid(n, t)
        matches = self._evaluate_query(
            p.exclusion,
            {
                "string",
                "boolean",
                "integer",
                "float",
                "datetime",
                "duration",
                "binary",
                "pointer",
            },
            "EXCLUDE",
            Q(object_id__in=p.expr) & Q(uuid=uuid),
        )
        return p.expr.difference(matches)

    @_("expr OR expr")  # type: ignore
    def expr(self, p):  # type: ignore # noqa
        """
        The result sets from two queries can be treated with a logical OR
        (set union).
        """
        return p.expr0.union(p.expr1)

    @_("HAS PATH")  # type: ignore
    def query(self, p):  # type: ignore # noqa
        """
        Query for presence of a tag on an object.
        """
        namespace, tag = p.PATH.split("/")
        uuid = utils.get_uuid(namespace, tag)
        return self._evaluate_query(
            p.PATH,
            {
                "string",
                "boolean",
                "integer",
                "float",
                "datetime",
                "duration",
                "binary",
                "pointer",
            },
            p.HAS,
            Q(uuid__exact=uuid),
        )

    @_("PATH IS MIME")  # type: ignore
    def query(self, p):  # type: ignore # noqa
        """
        Query for MIME type.
        """
        return self._evaluate_query(
            p.PATH, {"binary"}, p.IS, Q(mime__iexact=p.MIME)
        )

    @_("PATH IS STRING")  # type: ignore
    def query(self, p):  # type: ignore # noqa
        """
        Query for string equality.
        """
        return self._evaluate_query(
            p.PATH, {"string", "pointer"}, p.IS, Q(value__exact=p.STRING)
        )

    @_("PATH IIS STRING")  # type: ignore
    def query(self, p):  # type: ignore # noqa
        """
        Query for case insensitive string equality.
        """
        return self._evaluate_query(
            p.PATH, {"string", "pointer"}, p.IIS, Q(value__iexact=p.STRING)
        )

    @_("PATH MATCHES STRING")  # type: ignore
    def query(self, p):  # type: ignore # noqa
        """
        Query for string matching (the string contains the search term).
        """
        return self._evaluate_query(
            p.PATH,
            {"string", "pointer"},
            p.MATCHES,
            Q(value__contains=p.STRING),
        )

    @_("PATH IMATCHES STRING")  # type: ignore
    def query(self, p):  # type: ignore # noqa
        """
        Query for case insensitive string matching (the string contains the
        search term).
        """
        return self._evaluate_query(
            p.PATH,
            {"string", "pointer"},
            p.IMATCHES,
            Q(value__icontains=p.STRING),
        )

    @_("PATH IS boolean")  # type: ignore
    def query(self, p):  # type: ignore # noqa
        """
        Query for a boolean value.
        """
        return self._evaluate_query(
            p.PATH, {"boolean",}, p.IS, Q(value__exact=p.boolean)
        )

    @_("PATH operator scalar")  # type: ignore
    def query(self, p):  # type: ignore # noqa
        """
        Query for scalar comparisons.
        """
        query = None
        exclude = None
        if p.operator == "!=":
            exclude = Q(value__exact=p.scalar)
        elif p.operator == ">=":
            query = Q(value__gte=p.scalar)
        elif p.operator == "<=":
            query = Q(value__lte=p.scalar)
        elif p.operator == ">":
            query = Q(value__gt=p.scalar)
        elif p.operator == "<":
            query = Q(value__lt=p.scalar)
        elif p.operator == "=":
            query = Q(value__exact=p.scalar)
        return self._evaluate_query(
            p.PATH,
            {"integer", "float", "datetime", "duration",},
            p.operator,
            query,
            exclude,
        )

    @_("TRUE")  # type: ignore
    def boolean(self, p):  # type: ignore # noqa
        return p.TRUE

    @_("FALSE")  # type: ignore
    def boolean(self, p):  # type: ignore # noqa
        return p.FALSE

    @_("INT")  # type: ignore
    def scalar(self, p):  # type: ignore # noqa
        return p.INT

    @_("FLOAT")  # type: ignore
    def scalar(self, p):  # type: ignore # noqa
        return p.FLOAT

    @_("DURATION")  # type: ignore
    def scalar(self, p):  # type: ignore # noqa
        return p.DURATION

    @_("DATETIME")  # type: ignore
    def scalar(self, p):  # type: ignore # noqa
        return p.DATETIME

    @_("EQ")  # type: ignore
    def operator(self, p):  # type: ignore # noqa
        return p.EQ

    @_("NE")  # type: ignore
    def operator(self, p):  # type: ignore # noqa
        return p.NE

    @_("GE")  # type: ignore
    def operator(self, p):  # type: ignore # noqa
        return p.GE

    @_("LE")  # type: ignore
    def operator(self, p):  # type: ignore # noqa
        return p.LE

    @_("GT")  # type: ignore
    def operator(self, p):  # type: ignore # noqa
        return p.GT

    @_("LT")  # type: ignore
    def operator(self, p):  # type: ignore # noqa
        return p.LT

    @_("MISSING PATH")  # type: ignore
    def exclusion(self, p):  # type: ignore # noqa
        """
        Exclusion of objects with a certain tag.
        """
        return p.PATH

    def error(self, p):
        msg = (
            f'Cannot parse {p.type} (with value "{p.value}") on line '
            f"{p.lineno}, character {p.index}."
        )
        raise SyntaxError(msg)


def evaluate(user: models.User, query: str) -> Set[str]:
    """
    Evaluate the query string and return a set of matching object_ids. Log this
    query, the user who created it and the result set. If a problem is
    encountered, log the exception and re-raise.
    """
    try:
        # Tokenize.
        lexer = QueryLexer()
        tokens = list(lexer.tokenize(query))
        if tokens:
            # Check tag read permissions.
            parser = QueryParser(user, lexer.tag_paths)
            # Parse.
            result = parser.parse((t for t in tokens))
            logger.msg(
                "Evaluate query.",
                user=user.username,
                query=query,
                result=list(result),
            )
            return result
        else:
            raise ValueError("Query does not make sense. Please try again.")
    except Exception as ex:
        # Log the exception and re-raise.
        logger.msg(
            "Query exception.", user=user.username, query=query, exc_info=ex,
        )
        raise ex
