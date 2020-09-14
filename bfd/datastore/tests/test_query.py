"""
Tests exercising the lexer and parser that deal with queries.

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
from datetime import datetime, timedelta
from dateutil.tz import tzoffset, tzlocal
from django.test import TestCase
from datastore import query


class QueryLexerTestCase(TestCase):
    """
    Tests relating to the regular expressions used to identify tokens in the
    lexing of the query.
    """

    def setUp(self):
        self.lexer = query.QueryLexer()

    def test_datetime(self):
        """
        A datetime is:

        * 2020-08-19 (just the date)
        * 2020-08-19T15:40:30 (the date and time)
        * 2020-08-19T15:40:30-06:30 (the date, time and timezone offset)
        * 2020-08-19T15:40:30Z ("Zulu" time denoting UTC timezone)
        """
        example = "2020-08-19"
        result = list(self.lexer.tokenize(example))
        token = result[0]
        self.assertEqual(token.type, "DATETIME")
        self.assertEqual(token.value, datetime(2020, 8, 19))
        example = "2020-08-19T15:40:30"
        result = list(self.lexer.tokenize(example))
        token = result[0]
        self.assertEqual(token.type, "DATETIME")
        self.assertEqual(token.value, datetime(2020, 8, 19, 15, 40, 30))
        example = "2020-08-19T15:40:30-06:30"
        result = list(self.lexer.tokenize(example))
        token = result[0]
        self.assertEqual(token.type, "DATETIME")
        self.assertEqual(
            token.value,
            datetime(2020, 8, 19, 15, 40, 30, tzinfo=tzoffset(None, -23400)),
        )
        example = "2020-08-19T15:40:30Z"
        result = list(self.lexer.tokenize(example))
        token = result[0]
        self.assertEqual(token.type, "DATETIME")
        self.assertEqual(
            token.value, datetime(2020, 8, 19, 15, 40, 30, tzinfo=tzlocal())
        )

    def test_string(self):
        """
        A string is: "hello, world! \" escaped. \\ 汉字"
        """
        # Escaped comma.
        example = '"hello, world! \\" escaped. Don\'t forget \\\\ 汉字"'
        result = list(self.lexer.tokenize(example))
        token = result[0]
        self.assertEqual(token.type, "STRING")
        self.assertEqual(
            token.value, "hello, world! \\\" escaped. Don't forget \\\\ 汉字"
        )
        # Escaped double quote.
        example = '"hello, world! escaped. Don\'t forget \\\\ 汉字"'
        result = list(self.lexer.tokenize(example))
        token = result[0]
        self.assertEqual(token.type, "STRING")
        self.assertEqual(
            token.value, "hello, world! escaped. Don't forget \\\\ 汉字"
        )

    def test_float(self):
        """
        A float is: 1.234 or -1.234 or 1.234e4
        """
        example = "1.234"
        result = list(self.lexer.tokenize(example))
        token = result[0]
        self.assertEqual(token.type, "FLOAT")
        self.assertEqual(token.value, 1.234)
        example = "-1.234"
        result = list(self.lexer.tokenize(example))
        token = result[0]
        self.assertEqual(token.type, "FLOAT")
        self.assertEqual(token.value, -1.234)
        example = "1.234e4"
        result = list(self.lexer.tokenize(example))
        token = result[0]
        self.assertEqual(token.type, "FLOAT")
        self.assertEqual(token.value, 1.234e4)

    def test_tagpath(self):
        """
        A tag path is: unicode-namespace-slug/unicode-tag-slug

        Matched tag paths are added to the lexer's tagpaths set for later
        permissions processing.
        """
        example = "namespace-汉字-slug/tag_汉字_slug"
        result = list(self.lexer.tokenize(example))
        token = result[0]
        self.assertEqual(token.type, "TAGPATH")
        self.assertEqual(token.value, example)
        self.assertIn(example, self.lexer.tagpaths)

    def test_duration(self):
        """
        A duration is expressed as an integer followed by a unit of measurement
        as days or seconds:

        * 100d (100 days)
        * 3600s (3600 seconds)
        """
        example = "100d"
        result = list(self.lexer.tokenize(example))
        token = result[0]
        self.assertEqual(token.type, "DURATION")
        self.assertEqual(token.value, timedelta(days=100))
        example = "3600s"
        result = list(self.lexer.tokenize(example))
        token = result[0]
        self.assertEqual(token.type, "DURATION")
        self.assertEqual(token.value, timedelta(seconds=3600))

    def test_int(self):
        """
        A float is: 1234 or -1234
        """
        example = "1234"
        result = list(self.lexer.tokenize(example))
        token = result[0]
        self.assertEqual(token.type, "INT")
        self.assertEqual(token.value, 1234)
        example = "-1234"
        result = list(self.lexer.tokenize(example))
        token = result[0]
        self.assertEqual(token.type, "INT")
        self.assertEqual(token.value, -1234)

    def test_true(self):
        """
        A boolean True is: (case insensitive) True.
        """
        example = "True"
        result = list(self.lexer.tokenize(example))
        token = result[0]
        self.assertEqual(token.type, "TRUE")
        self.assertEqual(token.value, True)
        example = "TRUE"
        result = list(self.lexer.tokenize(example))
        token = result[0]
        self.assertEqual(token.type, "TRUE")
        self.assertEqual(token.value, True)

    def test_false(self):
        """
        A boolean False is: (case insensitive) False.
        """
        example = "False"
        result = list(self.lexer.tokenize(example))
        token = result[0]
        self.assertEqual(token.type, "FALSE")
        self.assertEqual(token.value, False)
        example = "FALSE"
        result = list(self.lexer.tokenize(example))
        token = result[0]
        self.assertEqual(token.type, "FALSE")
        self.assertEqual(token.value, False)

    def test_case_insensitive_simple_tokens(self):
        """
        The keywords are case-insensitively matched. The comparison operators
        evaluate to the expected tokens. The literals evaluate to themselves.
        """
        # Case insensitive keywords.
        keywords = [
            "HAS",
            "MISSING",
            "AND",
            "OR",
            "MATCHES",
            "IMATCHES",
            "IS",
        ]
        for k in keywords:
            result = list(self.lexer.tokenize(k))
            token = result[0]
            self.assertEqual(token.type, k)
            self.assertEqual(token.value, k)
            # Works no matter the case.
            result = list(self.lexer.tokenize(k.lower()))
            token = result[0]
            self.assertEqual(token.type, k)
            self.assertEqual(token.value, k.lower())
        # Comparisons evaluate to their names.
        comparisons = {
            "=": "EQ",
            "!=": "NE",
            ">": "GT",
            "<": "LT",
            ">=": "GE",
            "<=": "LE",
        }
        for comparison, name in comparisons.items():
            result = list(self.lexer.tokenize(comparison))
            token = result[0]
            self.assertEqual(token.type, name)
            self.assertEqual(token.value, comparison)
        # Literals always evaluate to themselves.
        literals = ["(", ")"]
        for literal in literals:
            result = list(self.lexer.tokenize(literal))
            token = result[0]
            self.assertEqual(token.type, literal)
            self.assertEqual(token.value, literal)

    def test_ignore_newline(self):
        """
        A newline increments the lineno property of the instance.
        """
        list(self.lexer.tokenize("\n\n123\n\n"))
        self.assertEqual(self.lexer.lineno, 5)

    def test_syntax_error(self):
        """
        If there's a syntax error, an exception is thrown.
        """
        with self.assertRaises(SyntaxError):
            list(self.lexer.tokenize("FOO"))

    def test_complete_queries(self):
        """
        To ensure interactions between the various tokenizing rules, various
        valid queries are evaluated.
        """
        query = (
            "has namespace-汉字-slug/tag_汉字_slug and "
            "(name/tag>=4 or foo/bar is False)"
        )
        tokens = list(self.lexer.tokenize(query))
        self.assertEqual(tokens[0].type, "HAS")
        self.assertEqual(tokens[1].type, "TAGPATH")
        self.assertEqual(tokens[2].type, "AND")
        self.assertEqual(tokens[3].type, "(")
        self.assertEqual(tokens[4].type, "TAGPATH")
        self.assertEqual(tokens[5].type, "GE")
        self.assertEqual(tokens[6].type, "INT")
        self.assertEqual(tokens[7].type, "OR")
        self.assertEqual(tokens[8].type, "TAGPATH")
        self.assertEqual(tokens[9].type, "IS")
        self.assertEqual(tokens[10].type, "FALSE")
        self.assertEqual(tokens[11].type, ")")
        query = "library/due=2026-08-19 or library/duration > 100d"
        tokens = list(self.lexer.tokenize(query))
        self.assertEqual(tokens[0].type, "TAGPATH")
        self.assertEqual(tokens[1].type, "EQ")
        self.assertEqual(tokens[2].type, "DATETIME")
        self.assertEqual(tokens[3].type, "OR")
        self.assertEqual(tokens[4].type, "TAGPATH")
        self.assertEqual(tokens[5].type, "GT")
        self.assertEqual(tokens[6].type, "DURATION")
        query = 'zoo/animal imatches "Elephant"'
        tokens = list(self.lexer.tokenize(query))
        self.assertEqual(tokens[0].type, "TAGPATH")
        self.assertEqual(tokens[1].type, "IMATCHES")
        self.assertEqual(tokens[2].type, "STRING")
        query = "maths/pi != 3.141"  # :-)
        tokens = list(self.lexer.tokenize(query))
        self.assertEqual(tokens[0].type, "TAGPATH")
        self.assertEqual(tokens[1].type, "NE")
        self.assertEqual(tokens[2].type, "FLOAT")
