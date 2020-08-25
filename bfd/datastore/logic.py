"""
Defines the logical operations that make use of the data layer.

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
from typing import Sequence
from django.http import HttpRequest  # type: ignore
from django.contrib.auth.models import User  # type: ignore
from django.utils.translation import gettext_lazy as _  # type: ignore
from datastore import models

# from datastore.query import parse


logger = structlog.get_logger()


def create_namespace(
    user: User, name: str, description: str, admins: Sequence
) -> models.Namespace:
    """
    Create a new namespace with the referenced description and user objects as
    administrators.
    """
    if user.is_superuser or user.username == name:
        n = models.Namespace.create(name=name, description=description)
        if admins:
            n.admins.add(*admins)
        logger.msg(
            "Create namespace.",
            user=user.username,
            namespace=name,
            description=description,
            admins=[admin.username for admin in admins],
        )
        return n
    else:
        raise PermissionError(
            _("User doesn't have permission to create a new namespace.")
        )


def update_namespace_description(
    user: User, name: str, description: str
) -> models.Namespace:
    """
    Update the description of the namespace with the referenced name.
    """
    n = models.Namespace.objects.get(name=name)
    n.description = description
    n.save()
    logger.msg(
        "Update namespace description.",
        user=user.username,
        namespace=name,
        description=description,
    )
    return n


def add_namespace_admins(
    user: User, name: str, admins: Sequence
) -> models.Namespace:
    """
    Add the referenced user objects as administrators of the Namespace.
    """
    n = models.Namespace.objects.get(name=name)
    n.admins.add(*admins)
    logger.msg(
        "Add namespace administrators.",
        user=user.username,
        namespace=name,
        admins=[admin.username for admin in admins],
    )
    return n


def remove_namespace_admins(
    user: User, name: str, admins: Sequence
) -> models.Namespace:
    """
    Remove the referenced user objects as administrators of the Namespace.
    """
    n = models.Namespace.objects.get(name=name)
    n.admins.remove(*admins)
    logger.msg(
        "Remove namespace administrators.",
        user=user.username,
        namespace=name,
        admins=[admin.username for admin in admins],
    )
    return n


def create_tag(
    user: User,
    name: str,
    description: str,
    type_of: str,
    namespace: models.Namespace,
    private: bool,
    users: Sequence,
    readers: Sequence,
) -> models.Tag:
    """
    Create a new tag with the referenced name, description, type and namespace.
    Only users may use the resulting tag to annotate data onto objects.
    If the private flag is True then the readers should contain
    users who are exceptions to the private flag. Users may read and annotate
    with the tag. Readers may only read.
    """
    t = models.Tag.create(
        name=name,
        description=description,
        type_of=type_of,
        namespace=namespace,
        private=private,
    )
    if users:
        t.users.add(*users)
    if readers:
        t.readers.add(*readers)
    logger.msg(
        "Create tag.",
        user=user.username,
        name=name,
        description=description,
        type_of=t.get_type_of_display(),
        namespace=namespace.name,
        private=private,
        users=[u.username for u in users],
        readers=[r.username for r in readers],
    )
    return t


def update_tag_description(
    user: User, name: str, namespace: str, description: str
) -> models.Tag:
    """
    Update the description of the tag with the referenced name and namespace.
    """
    n = models.Namespace.objects.get(name=namespace)
    t = models.Tag.objects.get(name=name, namespace=n)
    t.description = description
    t.save()
    logger.msg(
        "Update tag description.",
        user=user.username,
        tag=name,
        namespace=namespace,
        description=description,
    )
    return t


def set_tag_private(
    user: User, name: str, namespace: str, private: bool
) -> models.Tag:
    """
    Set the referenced tag's private flag.
    """
    n = models.Namespace.objects.get(name=namespace)
    t = models.Tag.objects.get(name=name, namespace=n)
    t.private = private
    t.save()
    logger.msg(
        "Update tag privacy.",
        user=user.username,
        tag=name,
        namespace=namespace,
        private=private,
    )
    return t


def add_tag_users(
    user: User, name: str, namespace: str, users: Sequence
) -> models.Tag:
    """
    Add the referenced user objects to the tag's users list (who can both
    annotate and read the tag).
    """
    n = models.Namespace.objects.get(name=namespace)
    t = models.Tag.objects.get(name=name, namespace=n)
    t.users.add(*users)
    logger.msg(
        "Add tag users.",
        user=user.username,
        tag=name,
        namespace=namespace,
        users=[u.username for u in users],
    )
    return t


def remove_tag_users(
    user: User, name: str, namespace: str, users: Sequence
) -> models.Tag:
    """
    Remove the referenced user object from the tag's users list (who can both
    annotate and read the tag).
    """
    n = models.Namespace.objects.get(name=namespace)
    t = models.Tag.objects.get(name=name, namespace=n)
    t.users.remove(*users)
    logger.msg(
        "Remove tag users.",
        user=user.username,
        tag=name,
        namespace=namespace,
        users=[u.username for u in users],
    )
    return t


def add_tag_readers(
    user: User, name: str, namespace: str, readers: Sequence
) -> models.Tag:
    """
    Add the referenced user objects to the tag's readers list (who can read a
    private tag).
    """
    n = models.Namespace.objects.get(name=namespace)
    t = models.Tag.objects.get(name=name, namespace=n)
    t.readers.add(*readers)
    logger.msg(
        "Add tag readers.",
        user=user.username,
        tag=name,
        namespace=namespace,
        readers=[r.username for r in readers],
    )
    return t


def remove_tag_readers(
    user: User, name: str, namespace: str, readers: Sequence
) -> models.Tag:
    """
    Remove the referenced user objects from the tag's readers list (those who
    can read a private tag).
    """
    n = models.Namespace.objects.get(name=namespace)
    t = models.Tag.objects.get(name=name, namespace=n)
    t.readers.remove(*readers)
    logger.msg(
        "Remove tag readers.",
        user=user.username,
        tag=name,
        namespace=namespace,
        readers=[r.username for r in readers],
    )
    return t


def get_object_tags(user: User, object_id: str) -> Sequence[str]:
    """
    Return all the tags associated with the referenced object that are visible
    to the referenced user.
    """


def get_object_tag_value(user: User, object_id: str, namespace: str, tag: str):
    """
    Return the value associated with the namespace/tag pair on the referenced
    object given its visibility to the referenced user.
    """


def get_object_values(user: User, object_id: str, tags: Sequence):
    """
    Get the values associated with the referenced tags on the referenced object
    that are visible to the referenced user.
    """


def get_object_query(user: User, query: str, tags: Sequence):
    """
    Get the values associated with the referenced tags on objects that match
    the propositions found in the referenced query. Only tags/values visible to
    the referenced user will be returned.

    The tags sequence should be of the form:
    [
        "namespace1/tag1",
        "namespace2/tag2",
        ... etc...
    ]
    """


def set_object_tag_value(
    user: User, object_id: str, namespace: str, tag: str, value: HttpRequest
):
    """
    Set the referenced namespace/tag on the specified object to the value
    contained within the incoming HttpRequest. Assumes the privileges of the
    referenced user.

    The type of the value in the HttpRequest is infered (and checked against)
    the type of the referenced tag.

    If the operation failed, an exception will be raised.
    """


def set_object_tag_values(user: User, object_tag_values: Sequence):
    """
    Set a number of unique namespace/tag values on each of the objects
    referenced in the sequence. Assumes the privileges of the referenced user.

    The object_tag_values should be of the form:

    [
        {
            "object_id": "my object1",
            values: {
                "namespace/tag": "a value to store",
                "namespace2/tag2": 123,
            },
        },
        {
            "object_id": "my object2",
            values: {
                "namespace3/ta3": "a unique value",
                "namespace2/tag2": 456,
            },
        },
        ... next object with other unique tag values...
    ]

    If the operation failed, an exception will be raised.
    """


def set_object_tag_values_by_query(
    user: User, query: Sequence, tag_values: Sequence
):
    """
    Sets the same namespace/tag values to each of the objects matched by the
    sequence of predicates in the query. Assumes the privileges of the
    referenced user.

    If the operation failed, an exception will be raised.
    """
