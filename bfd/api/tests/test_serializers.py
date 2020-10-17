"""
Tests for the  custom serialization code used by the API application.

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
from unittest import mock
from api import serializers
from rest_framework.exceptions import ValidationError
from django.test import TestCase


class TagPathFieldTestCase(TestCase):
    """
    Exercises the bespoke TagPathField.
    """

    def test_to_representation(self):
        """
        The string representation of the tag path is simply passed through
        without any change.
        """
        field = serializers.TagPathField()
        val = "namespace/tag"
        self.assertEqual(val, field.to_representation(val))

    def test_to_internal_value_not_string(self):
        """
        When validation is called, to_internal raises a ValidationError if the
        passed in value is not a string.
        """
        field = serializers.TagPathField()
        val = 1
        with self.assertRaises(ValidationError):
            field.run_validation(val)

    def test_to_internal_value_incorrect_format(self):
        """
        When an incorrectly formatted string is passed in, during validation,
        to_internal raises a ValidationError.
        """
        field = serializers.TagPathField()
        val = "incorrect-tag-path"
        with self.assertRaises(ValidationError):
            field.run_validation(val)

    def test_to_internal_value_is_correct(self):
        """
        A valid tag path passes validation.
        """
        field = serializers.TagPathField()
        val = "namespace-name/tag_name"
        result = field.run_validation(val)
        self.assertEqual(result, val)


class TagValueDictFieldTestCase(TestCase):
    """
    Exercises the TagValueDictField. This is a bespoke DictField that ensures
    keys are valid TagPathFields.
    """

    def test_get_value_is_html(self):
        """
        Ensure that getting the value of the field works with HTML form fields.
        """
        field = serializers.TagValueDictField()
        field.field_name = "test_field"
        test_dict = {}
        mock_html = mock.MagicMock()
        mock_html.parse_html_dict.return_value = "it worked!"
        with mock.patch("api.serializers.html", mock_html):
            result = field.get_value(test_dict)
            self.assertEqual("it worked!", result)
            mock_html.is_html_input.assert_called_once_with(test_dict)
            mock_html.parse_html_dict.assert_called_once_with(
                test_dict, prefix=field.field_name
            )

    def test_get_value(self):
        """
        Ensure that getting the value of the field works with native dictionary
        representations.
        """
        field = serializers.TagValueDictField()
        field.field_name = "test_field"
        test_dict = mock.MagicMock()
        test_dict.get.return_value = "it worked!"
        mock_html = mock.MagicMock()
        mock_html.is_html_input.return_value = False
        with mock.patch("api.serializers.html", mock_html):
            result = field.get_value(test_dict)
            self.assertEqual("it worked!", result)
            test_dict.get.assert_called_once_with(
                field.field_name, serializers.serializers.empty
            )

    def test_to_internal_value_html_input(self):
        """
        If the input data is from an HTML form, ensure it is parsed into a
        dictionary object before further validation occurs.
        """
        field = serializers.TagValueDictField()
        field.field_name = "test_field"
        test_dict = "a dict in html"
        mock_html = mock.MagicMock()
        mock_html.is_html_input.return_value = True
        dict_result = {
            "namespace_name/tag-name": "a value",
        }
        mock_html.parse_html_dict.return_value = dict_result
        with mock.patch("api.serializers.html", mock_html):
            result = field.to_internal_value(test_dict)
            self.assertEqual(dict_result, result)

    def test_to_internal_value_not_dict(self):
        """
        When validation is called, to_internal raises a ValidationError if the
        passed in value is not a dictionary.
        """
        field = serializers.TagValueDictField()
        val = 123
        mock_html = mock.MagicMock()
        mock_html.is_html_input.return_value = False
        with mock.patch("api.serializers.html", mock_html):
            with self.assertRaises(ValidationError):
                field.to_internal_value(val)

    def test_to_internal_value_is_empty(self):
        """
        When validation is called, to_internal raises a ValidationError if the
        passed in value is not a dictionary.
        """
        field = serializers.TagValueDictField(allow_empty=False)
        val = {}
        mock_html = mock.MagicMock()
        mock_html.is_html_input.return_value = False
        with mock.patch("api.serializers.html", mock_html):
            with self.assertRaises(ValidationError):
                field.to_internal_value(val)

    def test_to_representation(self):
        """
        The dict representation is simply passed through without any change.
        """
        field = serializers.TagValueDictField()
        val = {
            "namespace_name/tag-name": "a value",
        }
        self.assertEqual(val, field.to_representation(val))

    def test_run_child_validation(self):
        """
        A dictionary containing correctly formatted keys is checked and
        returned without raising any errors.
        """
        field = serializers.TagValueDictField()
        val = {
            "namespace_name/tag-name": "a value",
        }
        result = field.run_child_validation(val)
        self.assertEqual(result, val)

    def test_run_child_validation_bad_key(self):
        """
        A dictionary with an incorrectly formatted key results in a
        ValidationError exception being thrown.
        """
        field = serializers.TagValueDictField()
        val = {
            "namespace_name--tag-name": "a value",
        }
        with self.assertRaises(ValidationError):
            field.run_child_validation(val)
