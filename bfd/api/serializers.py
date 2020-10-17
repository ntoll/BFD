"""
Serializers convert data types to serialized data (e.g. JSON) and back again.

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
import re
from rest_framework.exceptions import ValidationError  # type: ignore
from rest_framework import serializers  # type: ignore
from rest_framework.utils import html  # type: ignore
from datastore import models

# from datastore import logic


class TagPathField(serializers.Field):
    """
    Tag paths are serialized as strings (consisting of a namespace and tag name
    separated by a slash "/"). An incoming tagpath is checked for correctness.
    """

    default_error_messages = {
        "incorrect_type": (
            "Incorrect type. Expected a string, but got {input_type}"
        ),
        "incorrect_format": (
            "Incorrect format. Expected `namespace_name/tag_name`."
        ),
    }

    def to_representation(self, value: str) -> str:
        """
        Pass through the outgoing string value.
        """
        return value

    def to_internal_value(self, data: str) -> str:
        """
        Ensure the incoming data is a string and of the expected
        "namespace/tag" format. Raise a ValidationError exception if not the
        case.
        """
        if not isinstance(data, str):
            self.fail("incorrect_type", input_type=type(data).__name__)
        if not re.match(r"[-\w]+/[-\w]+", data):
            self.fail("incorrect_format")
        return data


class TagPathListField(serializers.ListField):
    """
    Represents a list of TagPathFields.
    """

    child = TagPathField()
    allow_empty = False


class TagValueDictField(serializers.DictField):
    """
    Represents a dictionary where the keys must be valid TagPathFields and the
    values arbitrary values (whose type and range are checked by the serializer
    rather than this field).
    """

    initial = {}
    default_error_messages = {
        "not_a_dict": (
            'Expected a dictionary of items but got type "{input_type}".'
        ),
        "empty": "This dictionary may not be empty.",
    }

    def get_value(self, dictionary):
        """
        Override the default field access in order to support dictionaries in
        HTML forms.
        """
        if html.is_html_input(dictionary):
            return html.parse_html_dict(dictionary, prefix=self.field_name)
        return dictionary.get(self.field_name, serializers.empty)

    def to_internal_value(self, data):
        """
        Ensure incoming data is a dictionary and run validation on entries.
        """
        if html.is_html_input(data):
            data = html.parse_html_dict(data)
        if not isinstance(data, dict):
            self.fail("not_a_dict", input_type=type(data).__name__)
        if not self.allow_empty and len(data) == 0:
            self.fail("empty")
        return self.run_child_validation(data)

    def to_representation(self, value):
        """
        Pass through the outgoing dictionary value.
        """
        return value

    def run_child_validation(self, data):
        """
        Ensure the dictionary keys are valid TagPathFields. Otherwise raise a
        ValidationError exception.
        """
        result = {}
        errors = {}
        for key, value in data.items():
            key_field = TagPathField()
            try:
                tag_path = key_field.run_validation(key)
                result[tag_path] = value
            except ValidationError as e:
                errors[key] = e.detail
        if errors:
            raise ValidationError(errors)
        return result


class TagPathList(serializers.Serializer):
    """
    Manages how lists of tag paths are serialized.
    """

    tag_paths = TagPathListField(
        required=True,
        label="Tag paths",
        help_text=("A list of tag-paths to use with the referenced object."),
    )


class RetrieveQuery(serializers.Serializer):
    """
    Manages how queries for retrieving values on matching objects are
    serialized.
    """

    select = TagPathListField(
        required=True,
        label="Select",
        help_text=(
            "A list of tag-paths for values to retrieve from matching objects."
        ),
    )
    where = serializers.CharField(
        required=True,
        label="Where",
        help_text="Criteria for matching objects expressed as BFQL.",
        style={"base_template": "textarea.html"},
    )


class UpdateQuery(serializers.Serializer):
    """
    Manages how queries for updating values on matching objects are serialized.
    """

    update = TagValueDictField(
        required=True,
        label="Update",
        help_text=(
            "A dictionary of tag-paths and values "
            "to annotate onto matching objects."
        ),
    )
    where = serializers.CharField(
        required=True,
        label="Where",
        help_text="Criteria for matching objects expressed as BFQL,",
        style={"base_template": "textarea.html"},
    )


class DeleteQuery(serializers.Serializer):
    """
    Manages how queries for deleting values from matching objects are
    serialized.
    """

    delete = TagPathListField(
        required=True,
        label="Delete",
        help_text=(
            "A list of tag-paths for values to delete from matching objects."
        ),
    )
    where = serializers.CharField(
        required=True,
        label="Where",
        help_text="Criteria for matching objects expressed as BFQL.",
        style={"base_template": "textarea.html"},
    )


class UserRoleSerializer(serializers.ModelSerializer):
    """
    Manages how users are serialized when being specified for roles.
    """

    username = serializers.CharField(required=True)

    class Meta:
        model = models.User
        fields = [
            "username",
        ]


class NamespaceSerializer(serializers.ModelSerializer):
    """
    Manages how Namespace data comes in/out of the API.
    """

    name = serializers.CharField(read_only=True)
    description = serializers.CharField(
        required=True, style={"base_template": "textarea.html"}
    )
    admins = UserRoleSerializer(many=True)

    class Meta:
        model = models.Namespace
        fields = ["name", "description", "admins"]


class TagSerializer(serializers.ModelSerializer):
    """
    Manages how Tag data comes in/out of the API.
    """

    name = serializers.CharField(read_only=True)
    description = serializers.CharField(
        required=True, style={"base_template": "textarea.html"}
    )
    type_of = serializers.ChoiceField(models.VALID_DATA_TYPES, read_only=True)
    private = serializers.BooleanField()
    users = UserRoleSerializer(many=True)
    readers = UserRoleSerializer(many=True)

    class Meta:
        model = models.Tag
        fields = [
            "name",
            "description",
            "type_of",
            "private",
            "users",
            "readers",
        ]


class StringValueSerializer(serializers.ModelSerializer):
    """
    Manages the serialization of string values annotated onto objects via a
    tag.
    """

    value = serializers.CharField(
        required=True, style={"base_template": "textarea.html"}
    )

    class Meta:
        model = models.StringValue
        fields = [
            "value",
        ]


class BooleanValueSerializer(serializers.ModelSerializer):
    """
    Manages the serialization of boolean values annotated onto objects via a
    tag.
    """

    value = serializers.BooleanField()

    class Meta:
        model = models.BooleanValue
        fields = [
            "value",
        ]


class IntegerValueSerializer(serializers.ModelSerializer):
    """
    Manages the serialization of integer values annotated onto objects via a
    tag.
    """

    value = serializers.IntegerField()

    class Meta:
        model = models.IntegerValue
        fields = [
            "value",
        ]


class FloatValueSerializer(serializers.ModelSerializer):
    """
    Manages the serialization of float values annotated onto objects via a
    tag.
    """

    value = serializers.FloatField()

    class Meta:
        model = models.FloatValue
        fields = [
            "value",
        ]


class DateTimeSerializer(serializers.ModelSerializer):
    """
    Manages the serialization of datetime values annotated onto objects via a
    tag.
    """

    value = serializers.DateTimeField()

    class Meta:
        model = models.DateTimeValue
        fields = [
            "value",
        ]


class DurationSerializer(serializers.ModelSerializer):
    """
    Manages the serialization of duration values annotated onto objects via a
    tag.
    """

    value = serializers.DurationField()

    class Meta:
        model = models.DurationValue
        fields = [
            "value",
        ]


class BinarySerializer(serializers.ModelSerializer):
    """
    Manages the serialization of binary values annotated onto objects via a
    tag.
    """

    value = serializers.FileField()
    mime = serializers.CharField(required=True, max_length=256)

    class Meta:
        model = models.BinaryValue
        fields = [
            "value",
            "mime",
        ]


class PointerSerializer(serializers.ModelSerializer):
    """
    Manages the serialization of URL values annotated onto objects via a
    tag.
    """

    value = serializers.URLField(max_length=512)

    class Meta:
        model = models.PointerValue
        fields = [
            "value",
        ]
