"""
Defines the data layer as used in the relational database.

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
import time
from typing import Union, Dict, Type, Set
from datetime import datetime, timedelta
from django.core.files import uploadedfile  # type: ignore
from django.apps import apps  # type: ignore
from django.db import models  # type: ignore
from django.contrib.auth.hashers import make_password  # type: ignore
from django.contrib.auth.models import (  # type: ignore
    AbstractUser,
    UserManager,
)
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


class BFDUserManager(UserManager):
    """
    Overrides Django's built-in UserManager class to ensure the User model's
    fields are verified:

    * The username must be a valid SLUG.
    * The email must be valid.
    """

    def _create_user(
        self, username: str, email: str, password: str, **extra_fields
    ):
        """
        Create and save a user with the given username, email, and password.

        In addition, check, create and save a namespace for the new user.
        """
        if not username:
            raise ValueError(_("The given username must be set"))
        if Namespace.objects.filter(name=username).exists():
            raise ValueError(
                _("The namespace for that username is already taken.")
            )
        email = self.normalize_email(email)
        # Lookup the real model class from the global app registry so this
        # manager method can be used in migrations. This is fine because
        # managers are by definition working on the real model.
        GlobalUserModel = apps.get_model(
            self.model._meta.app_label, self.model._meta.object_name
        )
        username = GlobalUserModel.normalize_username(username)
        user = self.model(username=username, email=email, **extra_fields)
        user.password = make_password(password)
        user.clean_fields()  # Validate the username and email.
        user.save(using=self._db)
        # Create the user's default namespace.
        Namespace.objects.create_namespace(
            username, f"The personal namespace for the user: {username}.", user
        )
        return user


class User(AbstractUser):
    """
    A user of the BFD. Just like a regular Django user except their username
    must be a valid SLUG field (so they get a validly named namespace that is
    also their username, for their own personal use).
    """

    username = models.SlugField(
        _("username"),
        max_length=64,
        allow_unicode=True,
        unique=True,
        help_text=_("Required. 64 characters or fewer. Must be a valid SLUG."),
        error_messages={
            "unique": _("A user with that username already exists.")
        },
    )

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"

    objects = BFDUserManager()


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
    tag_path = models.CharField(
        db_index=True,
        editable=False,
        max_length=129,
        help_text=_("A string representing the namespace/tag path."),
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
    updated_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        help_text=_("The user who most recently updated the value."),
    )
    updated_on = models.DateTimeField(
        auto_now=True,
        help_text=_("The date and time the value was last updated."),
    )

    @property
    def full_path(self) -> str:
        """
        Return the human readable path for the value.
        """
        return f"{self.object_id}/{self.namespace.name}/{self.tag.name}"

    @classmethod
    def python_type(cls) -> type:
        """
        Return the Python type for the values the child class stores against
        an object.

        This must be overridden in the child class.
        """
        raise NotImplementedError

    class Meta:
        abstract = True


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

    class Meta:
        ordering = [
            "name",
        ]


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
            raise PermissionError(
                _("User not an admin of the parent namespace.")
            )
        tag = self.create(
            name=name,
            description=description,
            type_of=type_of,
            namespace=namespace,
            path=f"{namespace.name}/{name}",
            private=private,
            created_by=user,
            updated_by=user,
        )
        if private:
            tag.users.add(user)
        return tag


class Tag(models.Model):
    """
    Represents a Tag - identifying what is being tagged to objects.
    """

    name = models.SlugField(
        max_length=64,
        allow_unicode=True,
        db_index=True,
        editable=False,
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
        editable=False,
        help_text=_("Defines the type of data this tag stores."),
    )
    namespace = models.ForeignKey(
        "Namespace",
        on_delete=models.CASCADE,
        editable=False,
        help_text=_("The namespace to which this tag belongs."),
    )
    path = models.CharField(
        db_index=True,
        editable=False,
        max_length=129,
        help_text=_("A string representation of the namespace/tag path."),
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

    def is_reader(self, user: User) -> bool:
        """
        Return a boolean indication if the referenced user is able to read
        values associated with this tag.

        Non-private tags are visible to all.

        If the tag is marked as private, only those who are explicitly
        designated readers or who are able to write via this tag have
        visibility of it.
        """
        if user.is_superuser:
            return True
        return (
            (not self.private)
            or self.readers.filter(pk=user.pk).exists()
            or self.users.filter(pk=user.pk).exists()
            or self.namespace.admins.filter(pk=user.pk).exists()
        )

    def annotate(
        self,
        user: User,
        object_id: str,
        value: Union[
            str,
            bool,
            int,
            float,
            datetime,
            timedelta,
            uploadedfile.UploadedFile,
        ],
    ) -> AbstractBaseValue:
        """
        Given a value, return a child instance of AbstractBaseValue that
        represents the typed value annotated onto the referenced object by the
        referenced user.

        For example, if this tag is a "type_of" "string", then passing in
        a valid string value will result in a StringValue instance being
        returned. This instance represents a value annotated to the referenced
        object via this tag. This instance IS NOT YET SAVED when it is
        returned, since this allows it either to be added to a bulk update
        transaction or saved as a single object into the database.
        """
        cls = VALUE_TYPE_MAP.get(self.type_of)
        if cls:
            if isinstance(value, cls.python_type()):
                instance = cls(
                    object_id=object_id,
                    tag_path=self.path,
                    namespace=self.namespace,
                    tag=self,
                    updated_by=user,
                    value=value,
                )
                if cls == BinaryValue and isinstance(
                    value, uploadedfile.UploadedFile
                ):
                    instance.mime = value.content_type
                instance.full_clean()
                return instance
            else:
                raise TypeError(_("Wrong value type for tag: ") + self.path)
        else:
            raise ValueError(_("Unknown data type for tag: ") + self.path)

    def filter(
        self,
        query: Union[None, models.Q] = None,
        exclude: Union[None, models.Q] = None,
    ) -> Set[str]:
        """
        Returns a set of object_ids of objects that match the given query and
        exclusion for values annotated with this tag (raises a ValueError if
        neither a query nor exclusion are passed in). This query is evaluated
        for the referenced user. If this user doesn't have permission to read
        the value of this tag, a PermissionError exception is raised.
        """
        if query is None and exclude is None:
            raise ValueError("Filtering requires a query or exclusion.")
        cls = VALUE_TYPE_MAP[self.type_of]
        set_name = cls.__name__.lower() + "_set"
        db_query = getattr(self, set_name)
        if query and exclude:
            result = db_query.filter(query).exclude(exclude)
        elif query:
            result = db_query.filter(query)
        else:
            result = db_query.exclude(exclude)
        return {match.object_id for match in result}

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["namespace", "name"], name="unique-namespace-tag"
            )
        ]
        ordering = [
            "name",
        ]


class StringValue(AbstractBaseValue):
    """
    Represents string values tagged to objects.
    """

    value = models.TextField(
        help_text=_(
            "The string data annotated onto the object via the namespace/tag."
        )
    )

    @classmethod
    def python_type(self) -> type:
        """
        A StringValue instance represents a Python string.
        """
        return str

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

    @classmethod
    def python_type(self) -> type:
        """
        A BooleanValue instance represents a Python bool.
        """
        return bool

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

    @classmethod
    def python_type(self) -> type:
        """
        An IntegerValue instance represents a Python integer.
        """
        return int

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

    @classmethod
    def python_type(self) -> type:
        """
        A FloatValue instance represents a Python float.
        """
        return float

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

    @classmethod
    def python_type(self) -> type:
        """
        A DateTimeValue instance represents a Python datetime.
        """
        return datetime

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

    @classmethod
    def python_type(self) -> type:
        """
        A DurationValue instance represents a Python str expressing duration.
        """
        return timedelta

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

    @classmethod
    def python_type(self) -> type:
        """
        A BinaryValue instance represents a raw binary file saved to disk.
        """
        return uploadedfile.UploadedFile

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

    @classmethod
    def python_type(self) -> type:
        """
        A PointerValue instance represents a URL pointing at something else.
        """
        return str

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["object_id", "namespace", "tag"],
                name="unique-pointer-val",
            )
        ]


#: Maps the types of values onto children of the AbstractBaseValue class.
VALUE_TYPE_MAP: Dict["str", Type[AbstractBaseValue]] = {
    "s": StringValue,
    "b": BooleanValue,
    "i": IntegerValue,
    "f": FloatValue,
    "d": DateTimeValue,
    "u": DurationValue,
    "a": BinaryValue,
    "p": PointerValue,
}


def get_users_query(user: User, tag_paths: Set[str]) -> models.query.QuerySet:
    """
    Given a list of namespace/tag paths of interest, return a query to get
    all the tags in that list that the referenced user is allowed to make use
    of to annotate values onto objects.
    """
    # Find the number of matching tags that are either public, where the user
    # has the role "user" associated with the tag or where the user is an admin
    # of the parent namespace. Working in this way means we only have a single
    # lazy database query that can be further modified before being executed.
    # Performance of this check is therefore relatively quick since it's done
    # at the database layer, rather than in Python.
    query = Tag.objects.filter(path__in=tag_paths)
    if not user.is_superuser:
        query = query.filter(
            models.Q(users__id=user.id)
            | models.Q(namespace__admins__id=user.id)
        ).distinct()
    return query


def get_readers_query(
    user: User, tag_paths: Set[str]
) -> models.query.QuerySet:
    """
    Given a list of namespace/tag paths of interest, return a query to get all
    the tags in that list that the referenced user is allowed to use to read
    values from objects.
    """
    # Find the number of matching tags that are either public, where the user
    # has the roles "user" or "reader" associated with the tag or where the
    # user is an admin of the parent namespace. Working in this way means we
    # only have a single lazy database query that can be further modified
    # before being executed. Performance of this check is therefore relatively
    # quick since it's done at the database layer, rather than in Python.
    query = Tag.objects.filter(path__in=tag_paths)
    if not user.is_superuser:
        query = query.filter(
            models.Q(private=False)
            | models.Q(users__id=user.id)
            | models.Q(readers__id=user.id)
            | models.Q(namespace__admins__id=user.id)
        ).distinct()
    return query
