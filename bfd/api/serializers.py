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
from rest_framework import serializers
from datastore import models

# from datastore import logic


class TagPathField(serializers.Field):
    """
    Tag paths (consisting of a namespace and tag name separated by a slash
    "/") are serialized as strings. An incoming tagpath is checked for
    correctness.
    """

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        return data


class UserRoleSerializer(serializers.Serializer):
    """
    Manages how users are serialized when being specified for roles.
    """

    username = serializers.CharField(required=True)

    class Meta:
        model = models.User
        fields = [
            "username",
        ]


class NamespaceSerializer(serializers.Serializer):
    """
    Manages how Namespace data comes in/out of the API.
    """

    name = serializers.CharField(required=True, read_only=True)
    description = serializers.CharField(
        required=True, style={"base_template": "textarea.html"}
    )
    admins = UserRoleSerializer(many=True)

    class Meta:
        model = models.Namespace
        fields = ["name", "description", "admins"]


class TagSerializer(serializers.Serializer):
    """
    Manages how Tag data comes in/out of the API.
    """

    name = serializers.CharField(required=True, read_only=True)
    description = serializers.CharField(
        required=True, style={"base_template": "textarea.html"}
    )
    type_of = serializers.ChoiceField(
        models.VALID_DATA_TYPES, required=True, read_only=True
    )
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


class StringValueSerializer(serializers.Serializer):
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


class BooleanValueSerializer(serializers.Serializer):
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


class IntegerValueSerializer(serializers.Serializer):
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


class FloatValueSerializer(serializers.Serializer):
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


class DateTimeSerializer(serializers.Serializer):
    """
    Manages the serialization of datetime values annotated onto objects via a
    tag.
    """

    value = serializers.DatetimeField()

    class Meta:
        model = models.DateTimeValue
        fields = [
            "value",
        ]


class DurationSerializer(serializers.Serializer):
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


class BinarySerializer(serializers.Serializer):
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


class PointerSerializer(serializers.Serializer):
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
