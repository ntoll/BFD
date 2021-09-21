"""
Tests exercising the lexer and parser that deal with queries.

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
from io import BytesIO
from datetime import datetime, timedelta, timezone
from dateutil.tz import tzoffset, tzlocal
from django.test import TestCase
from django.db.models import Q
from django.core.files import uploadedfile
from django.utils.timezone import make_aware
from datastore import query
from datastore import logic
from datastore import models


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

        If no timezone information is given, timezone information is added
        via Django's make_aware function to reflect configuration settings.
        """
        example = "2020-08-19"
        result = list(self.lexer.tokenize(example))
        token = result[0]
        self.assertEqual(token.type, "DATETIME")
        self.assertEqual(token.value, make_aware(datetime(2020, 8, 19)))
        example = "2020-08-19T15:40:30"
        result = list(self.lexer.tokenize(example))
        token = result[0]
        self.assertEqual(token.type, "DATETIME")
        self.assertEqual(
            token.value, make_aware(datetime(2020, 8, 19, 15, 40, 30))
        )
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

    def test_path(self):
        """
        A path is: unicode-namespace-slug/unicode-tag-slug
        """
        example = "namespace-汉字-slug/tag_汉字_slug"
        result = list(self.lexer.tokenize(example))
        token = result[0]
        self.assertEqual(token.type, "PATH")
        self.assertEqual(token.value, example)
        # Ensure all tag paths without duplications are logged in the lexer.
        example2 = "namespace/tag"
        result = list(self.lexer.tokenize(example2))
        token = result[0]
        self.assertEqual(token.type, "PATH")
        self.assertEqual(token.value, example2)
        list(self.lexer.tokenize(example))
        self.assertIn(example, self.lexer.tag_paths)
        self.assertIn(example2, self.lexer.tag_paths)
        self.assertEqual(2, len(self.lexer.tag_paths))

    def test_mime_type(self):
        """
        A MIME type is:

        mime:registry/name

        For example:

        mime:text/html
        MIME:application/vnd.oma.poc.optimized-progress-report+xml

        See RFC6836 and RFC4855.

        The value is modified to remove the pre-pended "mime:" to leave the
        remaining valid mime type value.
        """
        example = "mime:image/jpeg"
        result = list(self.lexer.tokenize(example))
        token = result[0]
        self.assertEqual(token.type, "MIME")
        self.assertEqual(token.value, "image/jpeg")

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
            "IIS",
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
        self.assertEqual(tokens[1].type, "PATH")
        self.assertEqual(tokens[2].type, "AND")
        self.assertEqual(tokens[3].type, "(")
        self.assertEqual(tokens[4].type, "PATH")
        self.assertEqual(tokens[5].type, "GE")
        self.assertEqual(tokens[6].type, "INT")
        self.assertEqual(tokens[7].type, "OR")
        self.assertEqual(tokens[8].type, "PATH")
        self.assertEqual(tokens[9].type, "IS")
        self.assertEqual(tokens[10].type, "FALSE")
        self.assertEqual(tokens[11].type, ")")
        query = "library/due=2026-08-19 or library/duration > 100d"
        tokens = list(self.lexer.tokenize(query))
        self.assertEqual(tokens[0].type, "PATH")
        self.assertEqual(tokens[1].type, "EQ")
        self.assertEqual(tokens[2].type, "DATETIME")
        self.assertEqual(tokens[3].type, "OR")
        self.assertEqual(tokens[4].type, "PATH")
        self.assertEqual(tokens[5].type, "GT")
        self.assertEqual(tokens[6].type, "DURATION")
        query = 'zoo/animal imatches "Elephant"'
        tokens = list(self.lexer.tokenize(query))
        self.assertEqual(tokens[0].type, "PATH")
        self.assertEqual(tokens[1].type, "IMATCHES")
        self.assertEqual(tokens[2].type, "STRING")
        query = "maths/pi != 3.141"  # :-)
        tokens = list(self.lexer.tokenize(query))
        self.assertEqual(tokens[0].type, "PATH")
        self.assertEqual(tokens[1].type, "NE")
        self.assertEqual(tokens[2].type, "FLOAT")
        query = "gallery/image is image/jpeg"
        tokens = list(self.lexer.tokenize(query))
        self.assertEqual(tokens[0].type, "PATH")
        self.assertEqual(tokens[1].type, "IS")
        self.assertEqual(tokens[2].type, "PATH")
        query = 'library/title iis "moby dick"'
        tokens = list(self.lexer.tokenize(query))
        self.assertEqual(tokens[0].type, "PATH")
        self.assertEqual(tokens[1].type, "IIS")
        self.assertEqual(tokens[2].type, "STRING")


class QueryParserTestCase(TestCase):
    """
    Ensure the QueryParser object takes the tokens from the lexer (see above)
    and returns the expected set of matching object_ids given various queries.
    """

    def setUp(self):
        self.lexer = query.QueryLexer()
        self.site_admin_user = models.User.objects.create_user(
            username="site_admin_user",
            email="test@user.com",
            password="password",
            is_superuser=True,
        )
        self.admin_user = models.User.objects.create_user(
            username="admin_user",
            email="test2@user.com",
            password="password",
        )
        self.tag_user = models.User.objects.create_user(
            username="tag_user",
            email="test3@user.com",
            password="password",
        )
        self.tag_reader = models.User.objects.create_user(
            username="tag_reader",
            email="test4@user.com",
            password="password",
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
            admins=[
                self.admin_user,
            ],
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
            users=[
                self.tag_user,
            ],
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
            readers=[
                self.tag_reader,
            ],
        )

    def test_init_readable_tag(self):
        """
        Ensure that the tagpaths are checked for read permission with the
        referenced user.

        In this case, the tag is readable by the referenced user.
        """
        list(self.lexer.tokenize('test_namespace/public_tag matches "hello"'))
        parser = query.QueryParser(self.admin_user, self.lexer.tag_paths)
        self.assertEqual(len(parser.tags), 1)
        self.assertIn(self.public_tag.path, parser.tags)
        self.assertEqual(parser.tags[self.public_tag.path], self.public_tag)

    def test_init_invisible_tag(self):
        """
        Ensure that the tagpaths are checked for read permission with the
        referenced user.

        In this case the tag exists but is not readable by the referenced
        user.
        """
        list(self.lexer.tokenize('test_namespace/reader_tag matches "hello"'))
        with self.assertRaises(ValueError) as ex:
            query.QueryParser(self.normal_user, self.lexer.tag_paths)
        msg = ex.exception.args[0]
        self.assertIn("test_namespace/reader_tag", msg)

    def test_init_missing_tag(self):
        """
        Ensure that the tagpaths are checked for read permission with the
        referenced user.

        In this case the tag does not exist.
        """
        list(self.lexer.tokenize('test_namespace/missing_tag matches "hello"'))
        with self.assertRaises(ValueError) as ex:
            query.QueryParser(self.normal_user, self.lexer.tag_paths)
        msg = ex.exception.args[0]
        self.assertIn("test_namespace/missing_tag", msg)

    def test_evaluate_query(self):
        """
        Given a tag path, an indication of the type of object to which such a
        query could be applied, a Q object (defining an appropriate query) and
        an optional Q object defining what to exclude:

        * Check the tag is of the appropriate type to which the queries could
          be applied (raise a ValueError if not),
        * Return a set containing the object_ids of matching objects annotated
          by the tag that match the queries.
        """
        val = self.public_tag.annotate(
            self.admin_user, "test_object", "a test value"
        )
        val.save()
        list(self.lexer.tokenize('test_namespace/public_tag matches "hello"'))
        parser = query.QueryParser(self.admin_user, self.lexer.tag_paths)
        result = parser._evaluate_query(
            "test_namespace/public_tag",
            {
                "string",
                "url",
            },
            "MATCHES",
            Q(value__contains="test"),
        )
        self.assertEqual(len(result), 1)
        self.assertIn("test_object", result)

    def test_evaluate_query_unknown_tag(self):
        """
        If the query is for an unknown tag, an informative ValueError exception
        is raised.
        """
        val = self.public_tag.annotate(
            self.admin_user, "test_object", "a test value"
        )
        val.save()
        list(self.lexer.tokenize('test_namespace/public_tag matches "hello"'))
        parser = query.QueryParser(self.admin_user, self.lexer.tag_paths)
        with self.assertRaises(ValueError) as ex:
            parser._evaluate_query(
                "test_namespace/unknown_tag",
                {
                    "string",
                    "url",
                },
                "MATCHES",
                Q(value__contains="test"),
            )
        msg = ex.exception.args[0]
        self.assertEqual("Unknown tag: test_namespace/unknown_tag", msg)

    def test_evaluate_query_wrong_type_of_operator(self):
        """
        If the query uses an operator that can't work with the type of the
        referenced tag, an informative ValueError exception is raised.
        """
        val = self.public_tag.annotate(
            self.admin_user, "test_object", "a test value"
        )
        val.save()
        list(self.lexer.tokenize('test_namespace/public_tag matches "hello"'))
        parser = query.QueryParser(self.admin_user, self.lexer.tag_paths)
        with self.assertRaises(ValueError) as ex:
            parser._evaluate_query(
                "test_namespace/public_tag",
                {"int", "float", "datetime", "duration"},
                "MATCHES",
                Q(value__contains="test"),
            )
        msg = ex.exception.args[0]
        expected = (
            'Cannot use operator "MATCHES" on tag: test_namespace/public_tag '
            "(string)"
        )
        self.assertEqual(expected, msg)

    def test_parenthesis_expr(self):
        """
        Parenthesis define scope to produce expected results.
        """
        val1 = self.public_tag.annotate(
            self.admin_user, "test_object1", "val1"
        )
        val2 = self.user_tag.annotate(self.admin_user, "test_object1", True)
        val3 = self.reader_tag.annotate(self.admin_user, "test_object2", 42)
        val1.save()
        val2.save()
        val3.save()
        tokens = list(
            self.lexer.tokenize(
                "has test_namespace/public_tag and "
                "(test_namespace/reader_tag = 42 or "
                "test_namespace/user_tag is true)"
            )
        )
        parser = query.QueryParser(self.admin_user, self.lexer.tag_paths)
        result = parser.parse((x for x in tokens))
        self.assertEqual(len(result), 1)
        self.assertIn("test_object1", result)

    def test_and_expr(self):
        """
        A logical AND operator returns the expected results.
        """
        val1 = self.public_tag.annotate(
            self.admin_user, "test_object1", "val1"
        )
        val2 = self.user_tag.annotate(self.admin_user, "test_object1", True)
        val3 = self.public_tag.annotate(
            self.admin_user, "test_object2", "val1"
        )
        val1.save()
        val2.save()
        val3.save()
        tokens = list(
            self.lexer.tokenize(
                'test_namespace/public_tag is "val1" '
                "and test_namespace/user_tag is true"
            )
        )
        parser = query.QueryParser(self.admin_user, self.lexer.tag_paths)
        result = parser.parse((x for x in tokens))
        self.assertEqual(len(result), 1)
        self.assertIn("test_object1", result)

    def test_exclude_expr(self):
        """
        A logical AND operator to exclude presence of a tag returns the
        expected results.
        """
        val1 = self.public_tag.annotate(
            self.admin_user, "test_object1", "val1"
        )
        val2 = self.user_tag.annotate(self.admin_user, "test_object1", True)
        val3 = self.public_tag.annotate(
            self.admin_user, "test_object2", "val1"
        )
        val1.save()
        val2.save()
        val3.save()
        tokens = list(
            self.lexer.tokenize(
                'test_namespace/public_tag is "val1" '
                "and missing test_namespace/user_tag"
            )
        )
        parser = query.QueryParser(self.admin_user, self.lexer.tag_paths)
        result = parser.parse((x for x in tokens))
        self.assertEqual(len(result), 1)
        self.assertIn("test_object2", result)

    def test_or_expr(self):
        """
        A logical OR operator returns the expected results.
        """
        val1 = self.public_tag.annotate(
            self.admin_user, "test_object1", "val1"
        )
        val2 = self.public_tag.annotate(
            self.admin_user, "test_object2", "val2"
        )
        val3 = self.public_tag.annotate(
            self.admin_user, "test_object3", "val3"
        )
        val1.save()
        val2.save()
        val3.save()
        tokens = list(
            self.lexer.tokenize(
                'test_namespace/public_tag is "val1" '
                'or test_namespace/public_tag is "val2"'
            )
        )
        parser = query.QueryParser(self.admin_user, self.lexer.tag_paths)
        result = parser.parse((x for x in tokens))
        self.assertEqual(len(result), 2)
        self.assertIn("test_object1", result)
        self.assertIn("test_object2", result)

    def test_has_path(self):
        """
        Check expected result from a query for the presence of a tag on an
        object.
        """
        val1 = self.public_tag.annotate(
            self.admin_user, "test_object1", "a test value"
        )
        val2 = self.user_tag.annotate(self.admin_user, "test_object2", True)
        val3 = self.public_tag.annotate(
            self.admin_user, "test_object3", "another test value"
        )
        val1.save()
        val2.save()
        val3.save()
        tokens = list(self.lexer.tokenize("has test_namespace/public_tag"))
        parser = query.QueryParser(self.admin_user, self.lexer.tag_paths)
        result = parser.parse((x for x in tokens))
        self.assertEqual(len(result), 2)
        self.assertIn("test_object1", result)
        self.assertIn("test_object3", result)

    def test_path_is_mime(self):
        """
        Check expected result from a query asking for objects tagged with a
        binary blob of a certain MIME type (e.g. image/png).
        """
        binary_tag = logic.create_tag(
            user=self.site_admin_user,
            name="bin-tag",
            description="A tag for annotating binary data.",
            type_of="a",
            namespace=self.test_namespace,
            private=False,
        )
        val = uploadedfile.InMemoryUploadedFile(
            file=BytesIO(b"hello"),
            field_name="",
            name="file.txt",
            content_type="text/text",
            size=5,
            charset="utf-8",
        )
        annotation = binary_tag.annotate(self.admin_user, "test_object1", val)
        annotation.save()
        tokens = list(
            self.lexer.tokenize("test_namespace/bin-tag is mime:text/text")
        )
        parser = query.QueryParser(self.admin_user, self.lexer.tag_paths)
        result = parser.parse((x for x in tokens))
        self.assertEqual(len(result), 1)
        self.assertIn("test_object1", result)

    def test_path_is_string(self):
        """
        Check expected results from a query asking for objects tagged with a
        string/pointer that exactly matches the search term.
        """
        pointer_tag = logic.create_tag(
            user=self.site_admin_user,
            name="pointer-tag",
            description="A tag for pointing at things via a URL.",
            type_of="p",
            namespace=self.test_namespace,
            private=False,
        )
        val1 = "https://ntoll.org/"
        val2 = "Hello"
        annotation1 = pointer_tag.annotate(
            self.admin_user, "test_object1", val1
        )
        annotation2 = self.public_tag.annotate(
            self.admin_user, "test_object2", val2
        )
        annotation1.save()
        annotation2.save()
        # Check pointer match.
        lexer = query.QueryLexer()
        tokens1 = list(
            lexer.tokenize(
                'test_namespace/pointer-tag is "https://ntoll.org/"'
            )
        )
        parser = query.QueryParser(self.admin_user, lexer.tag_paths)
        result = parser.parse((x for x in tokens1))
        self.assertEqual(len(result), 1)
        self.assertIn("test_object1", result)
        # Check string match.
        tokens2 = list(
            self.lexer.tokenize('test_namespace/public_tag is "Hello"')
        )
        parser = query.QueryParser(self.admin_user, self.lexer.tag_paths)
        result = parser.parse((x for x in tokens2))
        self.assertEqual(len(result), 1)
        self.assertIn("test_object2", result)

    def test_path_iis_string(self):
        """
        Check expected results from a query asking for objects tagged with a
        string/pointer that case insensitively matches the search term.
        """
        pointer_tag = logic.create_tag(
            user=self.site_admin_user,
            name="pointer-tag",
            description="A tag for pointing at things via a URL.",
            type_of="p",
            namespace=self.test_namespace,
            private=False,
        )
        val1 = "https://ntoll.org/"
        val2 = "Hello"
        annotation1 = pointer_tag.annotate(
            self.admin_user, "test_object1", val1
        )
        annotation2 = self.public_tag.annotate(
            self.admin_user, "test_object2", val2
        )
        annotation1.save()
        annotation2.save()
        # Check pointer match.
        lexer = query.QueryLexer()
        tokens1 = list(
            lexer.tokenize(
                'test_namespace/pointer-tag iis "https://NTOLL.ORG/"'
            )
        )
        parser = query.QueryParser(self.admin_user, lexer.tag_paths)
        result = parser.parse((x for x in tokens1))
        self.assertEqual(len(result), 1)
        self.assertIn("test_object1", result)
        # Check string match.
        tokens2 = list(
            self.lexer.tokenize('test_namespace/public_tag iis "helLO"')
        )
        parser = query.QueryParser(self.admin_user, self.lexer.tag_paths)
        result = parser.parse((x for x in tokens2))
        self.assertEqual(len(result), 1)
        self.assertIn("test_object2", result)

    def test_path_matches_string(self):
        """
        Check expected results from a query asking for objects tagged with a
        string/pointer that contains the search term.
        """
        pointer_tag = logic.create_tag(
            user=self.site_admin_user,
            name="pointer-tag",
            description="A tag for pointing at things via a URL.",
            type_of="p",
            namespace=self.test_namespace,
            private=False,
        )
        val1 = "https://ntoll.org/"
        val2 = "Hello, world!"
        annotation1 = pointer_tag.annotate(
            self.admin_user, "test_object1", val1
        )
        annotation2 = self.public_tag.annotate(
            self.admin_user, "test_object2", val2
        )
        annotation1.save()
        annotation2.save()
        # Check pointer match.
        lexer = query.QueryLexer()
        tokens1 = list(
            lexer.tokenize('test_namespace/pointer-tag matches "ntoll.org"')
        )
        parser = query.QueryParser(self.admin_user, lexer.tag_paths)
        result = parser.parse((x for x in tokens1))
        self.assertEqual(len(result), 1)
        self.assertIn("test_object1", result)
        # Check string match.
        tokens2 = list(
            self.lexer.tokenize('test_namespace/public_tag matches "Hello"')
        )
        parser = query.QueryParser(self.admin_user, self.lexer.tag_paths)
        result = parser.parse((x for x in tokens2))
        self.assertEqual(len(result), 1)
        self.assertIn("test_object2", result)

    def test_path_imatches_string(self):
        """
        Check expected results from a query asking for objects tagged with a
        string/pointer that case insensitively contains the search term.
        """
        pointer_tag = logic.create_tag(
            user=self.site_admin_user,
            name="pointer-tag",
            description="A tag for pointing at things via a URL.",
            type_of="p",
            namespace=self.test_namespace,
            private=False,
        )
        val1 = "https://ntoll.org/"
        val2 = "Hello"
        annotation1 = pointer_tag.annotate(
            self.admin_user, "test_object1", val1
        )
        annotation2 = self.public_tag.annotate(
            self.admin_user, "test_object2", val2
        )
        annotation1.save()
        annotation2.save()
        # Check pointer match.
        lexer = query.QueryLexer()
        tokens1 = list(
            lexer.tokenize('test_namespace/pointer-tag imatches "NTOLL.ORG"')
        )
        parser = query.QueryParser(self.admin_user, lexer.tag_paths)
        result = parser.parse((x for x in tokens1))
        self.assertEqual(len(result), 1)
        self.assertIn("test_object1", result)
        # Check string match.
        tokens2 = list(
            self.lexer.tokenize('test_namespace/public_tag imatches "HELLO"')
        )
        parser = query.QueryParser(self.admin_user, self.lexer.tag_paths)
        result = parser.parse((x for x in tokens2))
        self.assertEqual(len(result), 1)
        self.assertIn("test_object2", result)

    def test_path_is_boolean(self):
        """
        Check expected result from a query asking for objects tagged with a
        boolean value.
        """
        boolean_tag = logic.create_tag(
            user=self.site_admin_user,
            name="bool-tag",
            description="A tag for annotating boolean data.",
            type_of="b",
            namespace=self.test_namespace,
            private=False,
        )
        annotation1 = boolean_tag.annotate(
            self.admin_user, "test_object1", True
        )
        annotation2 = boolean_tag.annotate(
            self.admin_user, "test_object2", False
        )
        annotation1.save()
        annotation2.save()
        # Check False
        lexer = query.QueryLexer()
        tokens1 = list(lexer.tokenize("test_namespace/bool-tag is False"))
        parser = query.QueryParser(self.admin_user, lexer.tag_paths)
        result = parser.parse((x for x in tokens1))
        self.assertEqual(len(result), 1)
        self.assertIn("test_object2", result)
        # Check True
        tokens = list(self.lexer.tokenize("test_namespace/bool-tag is true"))
        parser = query.QueryParser(self.admin_user, self.lexer.tag_paths)
        result = parser.parse((x for x in tokens))
        self.assertEqual(len(result), 1)
        self.assertIn("test_object1", result)

    def test_path_ne_scalar(self):
        """
        Not equal to (!=) used with a scalar value returns the expected result.
        """
        int_tag = logic.create_tag(
            user=self.site_admin_user,
            name="int-tag",
            description="A tag for annotating integer data.",
            type_of="i",
            namespace=self.test_namespace,
            private=False,
        )
        annotation1 = int_tag.annotate(self.admin_user, "test_object1", 0)
        annotation2 = int_tag.annotate(self.admin_user, "test_object2", 100)
        annotation1.save()
        annotation2.save()
        tokens = list(self.lexer.tokenize("test_namespace/int-tag != 100"))
        parser = query.QueryParser(self.admin_user, self.lexer.tag_paths)
        result = parser.parse((x for x in tokens))
        self.assertEqual(len(result), 1)
        self.assertIn("test_object1", result)

    def test_path_ge_scalar(self):
        """
        Greater than or equal to (>=) used with a scalar value returns the
        expected result.
        """
        float_tag = logic.create_tag(
            user=self.site_admin_user,
            name="float-tag",
            description="A tag for annotating floating point data.",
            type_of="f",
            namespace=self.test_namespace,
            private=False,
        )
        annotation1 = float_tag.annotate(self.admin_user, "test_object1", 0.0)
        annotation2 = float_tag.annotate(self.admin_user, "test_object2", 1.23)
        annotation3 = float_tag.annotate(
            self.admin_user, "test_object3", -1.23
        )
        annotation1.save()
        annotation2.save()
        annotation3.save()
        tokens = list(self.lexer.tokenize("test_namespace/float-tag >= 0.0"))
        parser = query.QueryParser(self.admin_user, self.lexer.tag_paths)
        result = parser.parse((x for x in tokens))
        self.assertEqual(len(result), 2)
        self.assertIn("test_object1", result)
        self.assertIn("test_object2", result)

    def test_path_le_scalar(self):
        """
        Less than or equal to (>=) used with a scalar value returns the
        expected result.
        """
        datetime_tag = logic.create_tag(
            user=self.site_admin_user,
            name="dt-tag",
            description="A tag for annotating datetime data.",
            type_of="d",
            namespace=self.test_namespace,
            private=False,
        )
        annotation1 = datetime_tag.annotate(
            self.admin_user,
            "test_object1",
            datetime(2020, 8, 19, tzinfo=timezone.utc),
        )
        annotation2 = datetime_tag.annotate(
            self.admin_user,
            "test_object2",
            datetime(2019, 8, 19, tzinfo=timezone.utc),
        )
        annotation3 = datetime_tag.annotate(
            self.admin_user,
            "test_object3",
            datetime(2021, 8, 19, tzinfo=timezone.utc),
        )
        annotation1.save()
        annotation2.save()
        annotation3.save()
        tokens = list(
            self.lexer.tokenize("test_namespace/dt-tag <= 2020-08-19")
        )
        parser = query.QueryParser(self.admin_user, self.lexer.tag_paths)
        result = parser.parse((x for x in tokens))
        self.assertEqual(len(result), 2)
        self.assertIn("test_object1", result)
        self.assertIn("test_object2", result)

    def test_path_gt_scalar(self):
        """
        Great than (>) used with a scalar value returns the expected result.
        """
        dur_tag = logic.create_tag(
            user=self.site_admin_user,
            name="dur-tag",
            description="A tag for annotating duration data.",
            type_of="u",
            namespace=self.test_namespace,
            private=False,
        )
        annotation1 = dur_tag.annotate(
            self.admin_user, "test_object1", timedelta(seconds=1024)
        )
        annotation2 = dur_tag.annotate(
            self.admin_user, "test_object2", timedelta(days=1024)
        )
        annotation1.save()
        annotation2.save()
        tokens = list(self.lexer.tokenize("test_namespace/dur-tag > 100d"))
        parser = query.QueryParser(self.admin_user, self.lexer.tag_paths)
        result = parser.parse((x for x in tokens))
        self.assertEqual(len(result), 1)
        self.assertIn("test_object2", result)

    def test_path_lt_scalar(self):
        """
        Less than (<) used with a scalar value returns the expected result.
        """
        int_tag = logic.create_tag(
            user=self.site_admin_user,
            name="int-tag",
            description="A tag for annotating integer data.",
            type_of="i",
            namespace=self.test_namespace,
            private=False,
        )
        annotation1 = int_tag.annotate(self.admin_user, "test_object1", 0)
        annotation2 = int_tag.annotate(self.admin_user, "test_object2", 100)
        annotation1.save()
        annotation2.save()
        tokens = list(self.lexer.tokenize("test_namespace/int-tag < 100"))
        parser = query.QueryParser(self.admin_user, self.lexer.tag_paths)
        result = parser.parse((x for x in tokens))
        self.assertEqual(len(result), 1)
        self.assertIn("test_object1", result)

    def test_path_eq_scalar(self):
        """
        Equal to (=) used with a scalar value returns the expected result.
        """
        int_tag = logic.create_tag(
            user=self.site_admin_user,
            name="int-tag",
            description="A tag for annotating integer data.",
            type_of="i",
            namespace=self.test_namespace,
            private=False,
        )
        annotation1 = int_tag.annotate(self.admin_user, "test_object1", 0)
        annotation2 = int_tag.annotate(self.admin_user, "test_object2", 100)
        annotation1.save()
        annotation2.save()
        tokens = list(self.lexer.tokenize("test_namespace/int-tag = 100"))
        parser = query.QueryParser(self.admin_user, self.lexer.tag_paths)
        result = parser.parse((x for x in tokens))
        self.assertEqual(len(result), 1)
        self.assertIn("test_object2", result)

    def test_syntax_error(self):
        """
        A problem query results in a syntax error indicating where the error
        is.
        """
        tokens = list(self.lexer.tokenize("test_namespace/public_tag and 100"))
        parser = query.QueryParser(self.admin_user, self.lexer.tag_paths)
        with self.assertRaises(SyntaxError) as ex:
            parser.parse((x for x in tokens))
        msg = ex.exception.args[0]
        self.assertEquals(
            'Cannot parse AND (with value "and") on line 1, character 26.', msg
        )


class EvaluateTestCase(TestCase):
    """
    Ensure the evaluate function returns the expected results and/or raises the
    expected errors.
    """

    def setUp(self):
        self.lexer = query.QueryLexer()
        self.site_admin_user = models.User.objects.create_user(
            username="site_admin_user",
            email="test@user.com",
            password="password",
            is_superuser=True,
        )
        self.admin_user = models.User.objects.create_user(
            username="admin_user",
            email="test2@user.com",
            password="password",
        )
        self.tag_user = models.User.objects.create_user(
            username="tag_user",
            email="test3@user.com",
            password="password",
        )
        self.tag_reader = models.User.objects.create_user(
            username="tag_reader",
            email="test4@user.com",
            password="password",
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
            admins=[
                self.admin_user,
            ],
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
            users=[
                self.tag_user,
            ],
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
            readers=[
                self.tag_reader,
            ],
        )

    def test_evaluate_good_case(self):
        """
        A valid query produces the expected result.
        """
        val1 = self.public_tag.annotate(
            self.admin_user, "test_object1", "val1"
        )
        val2 = self.user_tag.annotate(self.admin_user, "test_object1", True)
        val3 = self.reader_tag.annotate(self.admin_user, "test_object2", 42)
        val1.save()
        val2.save()
        val3.save()
        q = (
            "has test_namespace/public_tag and "
            "(test_namespace/reader_tag = 42 or "
            "test_namespace/user_tag is true)"
        )
        result = query.evaluate(self.admin_user, q)
        self.assertEqual(len(result), 1)
        self.assertIn("test_object1", result)

    def test_evaluate_empty_query(self):
        """
        An empty query results in a ValueError exception.
        """
        with self.assertRaises(ValueError) as ex:
            query.evaluate(self.admin_user, "")
        msg = ex.exception.args[0]
        self.assertEquals("Query does not make sense. Please try again.", msg)

    def test_evaluate_syntax_error(self):
        """
        A problem query results in a syntax error with a helpful message.
        """
        with self.assertRaises(SyntaxError) as ex:
            query.evaluate(
                self.admin_user, "test_namespace/public_tag and 100"
            )
        msg = ex.exception.args[0]
        self.assertEquals(
            'Cannot parse AND (with value "and") on line 1, character 26.', msg
        )
