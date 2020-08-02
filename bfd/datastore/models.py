"""
Defines the data layer as used in the relational database.

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
import time
from django.db import models
from django.contrib.auth import User
from django.utils.translation import gettext_lazy as _


#: Defines the valid types of data with which BFD can work.
VALID_DATA_TYPES = (
    ("s", "string"),
    ("b", "boolean"),
    ("i", "integer"),
    ("f", "float"),
    ("d", "datetime"),
    ("u", "duration"),
    ("a", "binary (with mime type)"),
)


def upload_to(instance, filename):
    """
    The object, namespace and tag form part of the path (along with a
    timestamp) for binary values tagged to objects.
    """
    return "{object_id}/{namespace}/{tag}/{timestamp}_{filename}".format(
        object_id=instance.object_id,
        namespace=instance.namespace.name,
        tag=instance.tag.name,
        timestamp=time.time(),
        filename=filename,
    )


class Namespace(models.Model):
    """
    Represents a Namespace - identifying who is tagging data to objects.
    """

    name = models.SlugField(
        max_length=128,
        unique=True,
        allow_unicode=True,
        help_text=_(
            "The namespace's name identifying who is tagging data to objects."
        ),
    )
    description = models.CharField(
        max_length=512,
        help_text=_(
            "A short description for more context about the Namespace."
        ),
    )
    admins = models.ManyToManyField(
        User,
        related_name="admins",
        help_text=_("Users who administer the namespace."),
    )


class Tag(models.Model):
    """
    Represents a Tag - identifying what is being tagged to objects.
    """

    name = models.SlugField(
        max_length=64,
        unique=True,
        allow_unicode=True,
        help_text=_(
            "The tag's name identifying what is being tagged to objects."
        ),
    )
    description = models.CharField(
        max_length=512,
        help_text=_("A short description for more context about the tag."),
    )
    type_of = models.CharField(
        choices=VALID_DATA_TYPES,
        max_length=1,
        help_text=_("Defines the type of data this tag stores."),
    )
    namespace = models.ForeignKey(
        "Namespace", help_text=_("The namespace to which this tag belongs.")
    )
    private = models.BooleanField(
        default=False,
        help_text=_("If true, data associated with this tag is private."),
    )
    users = models.ManyToManyField(
        User,
        related_name="users",
        help_text=_("Users who can add data via the tag."),
    )
    readers = models.ManyToManyField(
        User,
        related_name="readers",
        help_text=_(
            "If the tag is private, users who can read data added via the tag."
        ),
    )


class StringValue(models.Model):
    """
    Represents string values tagged to objects.
    """

    object_id = models.SlugField(
        max_length=512,
        allow_unicode=True,
        help_text=_("The unique unicode identifier for the object."),
    )
    namespace = models.ForeignKey(
        "Namespace",
        help_text=_("The namespace used to annotate data onto the object."),
    )
    tag = models.ForeignKey(
        "Tag", help_text=_("The tag used to annotate data onto the object.")
    )
    value = models.TextField(
        help_text=_(
            "The string data annotated onto the object via the namespace/tag."
        )
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["object_id", "namespace", "tag"], name="unique-str-val"
            )
        ]


class BooleanValue(models.Model):
    """
    Represents boolean values tagged to objects.
    """

    object_id = models.SlugField(
        max_length=512,
        allow_unicde=True,
        help_text=_("The unique unicode identifier for the object."),
    )
    namespace = models.ForeignKey(
        "Namespace",
        help_text=_("The namespace used to annotate data onto the object."),
    )
    tag = models.ForeignKey(
        "Tag", help_text=_("The tag used to annotate data onto the object.")
    )
    value = models.BooleanField(
        help_text=_(
            "The boolean data annotated onto the object via the namespace/tag."
        )
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["object_id", "namespace", "tag"],
                name="unique-bool-val",
            )
        ]


class IntegerValue(models.Model):
    """
    Represents integer values tagged to objects.
    """

    object_id = models.SlugField(
        max_length=512,
        allow_unicode=True,
        help_text=_("The unique unicode identifier for the object."),
    )
    namespace = models.ForeignKey(
        "Namespace",
        help_text=_("The namespace used to annotate data onto the object."),
    )
    tag = models.ForeignKey(
        "Tag", help_text=_("The tag used to annotate data onto the object.")
    )
    value = models.IntegerField(
        help_text=_(
            "The integer data annotated onto the object via the namespace/tag."
        )
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["object_id", "namespace", "tag"], name="unique-int-val"
            )
        ]


class FloatValue(models.Model):
    """
    Represents floating point values tagged to objects.
    """

    object_id = models.SlugField(
        max_length=512,
        allow_unicode=True,
        help_text=_("The unique unicode identifier for the object."),
    )
    namespace = models.ForeignKey(
        "Namespace",
        help_text=_("The namespace used to annotate data onto the object."),
    )
    tag = models.ForeignKey(
        "Tag", help_text=_("The tag used to annotate data onto the object.")
    )
    value = models.FloatField(
        help_text=_(
            "The float data annotated onto the object via the namespace/tag."
        )
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["object_id", "namespace", "tag"],
                name="unique-float-val",
            )
        ]


class DateTimeValue(models.Model):
    """
    Represents date-time values tagged to objects.
    """

    object_id = models.SlugField(
        max_length=512,
        allow_unicode=True,
        help_text=_("The unique unicode identifier for the object."),
    )
    namespace = models.ForeignKey(
        "Namespace",
        help_text=_("The namespace used to annotate data onto the object."),
    )
    tag = models.ForeignKey(
        "Tag", help_text=_("The tag used to annotate data onto the object.")
    )
    value = models.DateTimeField(
        help_text=_(
            "The datetime annotated onto the object via the namespace/tag."
        )
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["object_id", "namespace", "tag"],
                name="unique-datetime-val",
            )
        ]


class DurationValue(models.Model):
    """
    Represents duration / time-delta / inteval values tagged to objects.
    """

    object_id = models.SlugField(
        max_length=512,
        allow_unicode=True,
        help_text=_("The unique unicode identifier for the object."),
    )
    namespace = models.ForeignKey(
        "Namespace",
        help_text=_("The namespace used to annotate data onto the object."),
    )
    tag = models.ForeignKey(
        "Tag", help_text=_("The tag used to annotate data onto the object.")
    )
    value = models.DurationField(
        help_text=_(
            "The duration annotated onto the object via the namespace/tag."
        )
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["object_id", "namespace", "tag"],
                name="unique-duration-val",
            )
        ]


class BinaryValue(models.Model):
    """
    Represents arbitrary binary values tagged to objects. Must also have an
    associated mime-type.
    """

    object_id = models.SlugField(
        max_length=512,
        allow_unicode=True,
        help_text=_("The unique unicode identifier for the object."),
    )
    namespace = models.ForeignKey(
        "Namespace",
        help_text=_("The namespace used to annotate data onto the object."),
    )
    tag = models.ForeignKey(
        "Tag", help_text=_("The tag used to annotate data onto the object.")
    )
    value = models.FileField(
        upload_to=upload_to,
        help_text=_(
            "The binary value annotated onto the object via the namespace/tag."
        ),
    )
    mime = models.CharField(
        max_length=256,
        help_text=_("The mime type defining the type of binary value stored."),
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["object_id", "namespace", "tag"],
                name="unique-binary-val",
            )
        ]
