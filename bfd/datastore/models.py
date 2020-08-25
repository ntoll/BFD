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
from . import utils
from django.db import models  # type: ignore
from django.contrib.auth.models import User  # type: ignore
from django.utils.translation import gettext_lazy as _  # type: ignore


#: Defines the valid types of data with which BFD can work.
VALID_DATA_TYPES = (
    ("s", "string"),
    ("b", "boolean"),
    ("i", "integer"),
    ("f", "float"),
    ("d", "datetime"),
    ("u", "duration"),
    ("a", "binary"),
    ("p", "pointer"),
)


class NamespaceManager(models.Manager):
    """
    Custom manager for the Namespace model. Ensures certain fields are updated
    correctly.
    """

    def create_namespace(
        self, name: str, description: str, user: User
    ) -> models.Model:
        """
        Correctly create a new namespace in the database.
        """
        namespace = self.create(
            name=name,
            description=description,
            created_by=user,
            updated_by=user,
        )
        namespace.admins.add(user)
        return namespace


class Namespace(models.Model):
    """
    Represents a Namespace - identifying who is tagging data to objects.
    """

    name = models.SlugField(
        max_length=64,
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
    created_by = models.ForeignKey(
        User,
        related_name="namespace_created_by_user",
        on_delete=models.PROTECT,
        help_text=_("The user who created the namespace."),
    )
    created_on = models.DateTimeField(
        auto_now_add=True,
        help_text=_("The date and time this namespace was created."),
    )
    updated_by = models.ForeignKey(
        User,
        related_name="namespace_updated_by_user",
        on_delete=models.PROTECT,
        help_text=_("The user who last updated the namespace."),
    )
    updated_on = models.DateTimeField(
        auto_now=True,
        help_text=_("The date and time this namespace was last updated."),
    )

    objects = NamespaceManager()


class TagManager(models.Manager):
    """
    Custom manager for the Tag model. Ensures certain fields are created
    and updated correctly.
    """

    def create_tag(
        self,
        name: str,
        description: str,
        type_of: str,
        namespace: Namespace,
        private: bool,
        user: User,
    ) -> models.Model:
        """
        Correctly check and create a new tag in the database.
        """
        if user not in namespace.admins.all():
            raise PermissionError("User not an admin of the parent namespace.")
        uuid = utils.get_uuid(namespace.name, name)
        tag = self.create(
            name=name,
            description=description,
            type_of=type_of,
            namespace=namespace,
            uuid=uuid,
            private=private,
            created_by=user,
            updated_by=user,
        )
        if private:
            tag.users.add(user)
            tag.readers.add(user)
        return tag


class Tag(models.Model):
    """
    Represents a Tag - identifying what is being tagged to objects.
    """

    name = models.SlugField(
        max_length=64,
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
        "Namespace",
        on_delete=models.CASCADE,
        help_text=_("The namespace to which this tag belongs."),
    )
    uuid = models.UUIDField(
        db_index=True,
        editable=False,
        help_text=_("A UUID representing the namespace/tag path."),
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
    created_by = models.ForeignKey(
        User,
        related_name="tag_created_by_user",
        on_delete=models.PROTECT,
        help_text=_("The user who created the tag."),
    )
    created_on = models.DateTimeField(
        auto_now_add=True,
        help_text=_("The date and time this tag was created."),
    )
    updated_by = models.ForeignKey(
        User,
        related_name="tag_updated_by_user",
        on_delete=models.PROTECT,
        help_text=_("The user who last updated the tag."),
    )
    updated_on = models.DateTimeField(
        auto_now=True,
        help_text=_("The date and time this tag was last updated."),
    )

    objects = TagManager()

    @property
    def path(self) -> str:
        """
        Return the human readable path for the tag.
        """
        return f"{self.namespace.name}/{self.name}"

    def is_user(self, user: User) -> bool:
        """
        Return a boolean indication if the referenced user is able to write
        values associated with this tag (the user can make use of this tag).
        """
        return self.users.filter(pk=user.pk).exists()

    def is_reader(self, user: User) -> bool:
        """
        Return a boolean indication if the referenced user is able to read
        values associated with this tag.

        Non-private tags are visible to all.

        If the tag is marked as private, only those who are explicitly
        designated readers or who are able to write via this tag have
        visibility of it.
        """
        return (
            (not self.private)
            or self.readers.filter(pk=user.pk).exists()
            or self.users.filter(pk=user.pk).exists()
        )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["namespace", "name"], name="unique-namespace-tag"
            )
        ]


class AbstractBaseValue(models.Model):
    """
    An abstract base class for all value classes. This will never become a
    table in the database. However, the attributes and Meta class will be used
    / inherited by the child classes when they are turned into database tables.
    """

    object_id = models.SlugField(
        max_length=512,
        allow_unicode=True,
        help_text=_("The unique unicode identifier for the object."),
    )
    uuid = models.UUIDField(
        db_index=True,
        editable=False,
        help_text=_("A UUID representing the namespace/tag path."),
    )
    namespace = models.ForeignKey(
        "Namespace",
        on_delete=models.CASCADE,
        help_text=_("The namespace used to annotate data onto the object."),
    )
    tag = models.ForeignKey(
        "Tag",
        on_delete=models.CASCADE,
        help_text=_("The tag used to annotate data onto the object."),
    )
    last_updated_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        help_text=_("The user who most recently updated the value."),
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        help_text=_("The date and time the value was last updated."),
    )

    @property
    def path(self):
        """
        Return the human readable path for the value.
        """
        return f"{self.object_id}/{self.namespace.name}/{self.tag.name}"

    class Meta:
        abstract = True


class StringValue(AbstractBaseValue):
    """
    Represents string values tagged to objects.
    """

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


class BooleanValue(AbstractBaseValue):
    """
    Represents boolean values tagged to objects.
    """

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


class IntegerValue(AbstractBaseValue):
    """
    Represents integer values tagged to objects.
    """

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


class FloatValue(AbstractBaseValue):
    """
    Represents floating point values tagged to objects.
    """

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


class DateTimeValue(AbstractBaseValue):
    """
    Represents date-time values tagged to objects.
    """

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


class DurationValue(AbstractBaseValue):
    """
    Represents duration / time-delta / inteval values tagged to objects.
    """

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


def upload_to(instance: AbstractBaseValue, filename: str) -> str:
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


class BinaryValue(AbstractBaseValue):
    """
    Represents arbitrary binary values tagged to objects. Must also have an
    associated mime-type.
    """

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


class PointerValue(AbstractBaseValue):
    """
    Represents a pointer to a resource elsewhere online. The pointer's value is
    in the form of a URL to the linked resource.
    """

    value = models.URLField(
        max_length=512,
        help_text=_(
            "The URL value annotated onto the object via the namespace/tag."
        ),
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["object_id", "namespace", "tag"],
                name="unique-pointer-val",
            )
        ]
