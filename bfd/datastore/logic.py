"""
Defines the logical operations that make use of the data layer.

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
import structlog  # type: ignore
from typing import Sequence, Union, List, Dict, Set
from django.db.models import Q  # type: ignore
from django.http import HttpRequest  # type: ignore
from django.contrib.auth.models import User  # type: ignore
from django.utils.translation import gettext_lazy as _  # type: ignore
from datastore import models

# from datastore.query import evaluate


logger = structlog.get_logger()


def create_namespace(
    user: User,
    name: str,
    description: str,
    admins: Union[Sequence[User], None] = None,
) -> models.Namespace:
    """
    Create a new namespace with the referenced description and user objects as
    administrators. The user who creates the namespace is automatically
    assigned administrator status.

    Only site admins can create new arbitrary namespaces.

    Regular users may only create a namespace if the name of the namespace is
    the same as their (unique) username.

    Any other user making such a request will result in a PermissionError
    being thrown.
    """
    if user.is_admin or user.username == name:
        n = models.Namespace.objects.create_namespace(
            name=name, description=description, user=user
        )
        admin_list: List[User] = [
            user,
        ]
        if admins:
            admin_list += [u for u in admins if u.id != user.id]
        n.admins.add(*admin_list)
        logger.msg(
            "Create namespace.",
            user=user.username,
            namespace=name,
            description=description,
            admins=[admin.username for admin in admin_list],
        )
        return n
    else:
        raise PermissionError(
            _("User doesn't have permission to create a new namespace.")
        )


def get_namespace(user: User, name: str) -> Dict:
    """
    Return a dictionary representation of the referenced Namespace as viewed by
    the referenced user (with associated privileges).

    Admin users see all attributes of all aspects of the namespace. Regular
    users see a limited set of attributes on only those aspects of the
    namespace for which they have privileges to see.
    """
    n = models.Namespace.objects.get(name=name)
    result = {
        "name": n.name,
        "description": n.description,
    }
    tags: List[Dict] = []
    if user.is_admin or n.admins.filter(pk=user.pk).exists():
        result["created_by"] = n.created_by.username
        result["created_on"] = str(n.created_on)
        result["updated_by"] = n.updated_by.username
        result["updated_on"] = str(n.updated_on)
        result["admins"] = [admin.username for admin in n.admins.all()]
        for tag in n.tag_set.all():
            tags.append(
                {
                    "name": tag.name,
                    "description": tag.description,
                    "type_of": tag.get_type_of_display(),
                    "private": tag.private,
                    "users": [user.username for user in tag.users.all()],
                    "readers": [
                        reader.username for reader in tag.readers.all()
                    ],
                    "created_by": tag.created_by.username,
                    "created_on": str(tag.created_on),
                    "updated_by": tag.updated_by.username,
                    "updated_on": str(tag.updated_on),
                }
            )
    else:
        # Get all public tags, or tags where the user is a user or reader.
        query = n.tag_set.filter(
            Q(private=False) | Q(users__id=user.id) | Q(readers__id=user.id)
        )
        for tag in query:
            tags.append(
                {
                    "name": tag.name,
                    "description": tag.description,
                    "type_of": tag.get_type_of_display(),
                }
            )
    result["tags"] = tags
    return result


def update_namespace_description(
    user: User, name: str, description: str
) -> models.Namespace:
    """
    Update the description of the namespace with the referenced name.

    Only site admins or regular users in the namespace's "admins" group may
    make this change.

    Any other user making such a request will result in a PermissionError
    being thrown.
    """
    n = models.Namespace.objects.get(name=name)
    if user.is_admin or n.admins.filter(pk=user.pk).exists():
        n.description = description
        n.save()
        logger.msg(
            "Update namespace description.",
            user=user.username,
            namespace=name,
            description=description,
        )
        return n
    else:
        raise PermissionError(
            _("User doesn't have permission to describe a namespace.")
        )


def add_namespace_admins(
    user: User, name: str, admins: Sequence[User]
) -> models.Namespace:
    """
    Add the referenced user objects as administrators of the Namespace.

    Only site admins or regular users in the namespace's "admins" group may
    make this change.

    Any other user making such a request will result in a PermissionError
    being thrown.
    """
    n = models.Namespace.objects.get(name=name)
    if user.is_admin or n.admins.filter(pk=user.pk).exists():
        n.admins.add(*admins)
        logger.msg(
            "Add namespace administrators.",
            user=user.username,
            namespace=name,
            admins=[admin.username for admin in admins],
        )
        return n
    else:
        raise PermissionError(
            _("User doesn't have permission to add admins to namespace.")
        )


def remove_namespace_admins(
    user: User, name: str, admins: Sequence[User]
) -> models.Namespace:
    """
    Remove the referenced user objects as administrators of the Namespace.

    Only site admins or regular users in the namespace's "admins" group may
    make this change.

    Any other user making such a request will result in a PermissionError
    being thrown.
    """
    n = models.Namespace.objects.get(name=name)
    if user.is_admin or n.admins.filter(pk=user.pk).exists():
        n.admins.remove(*admins)
        logger.msg(
            "Remove namespace administrators.",
            user=user.username,
            namespace=name,
            admins=[admin.username for admin in admins],
        )
        return n
    else:
        raise PermissionError(
            _("User doesn't have permission to remove admins from namespace.")
        )


def create_tag(
    user: User,
    name: str,
    description: str,
    type_of: str,
    namespace: models.Namespace,
    private: bool,
    users: Union[Sequence[User], None] = None,
    readers: Union[Sequence[User], None] = None,
) -> models.Tag:
    """
    Create a new tag with the referenced name, description, type and namespace.
    Only users may use the resulting tag to annotate data onto objects.

    If the private flag is True then the readers should contain users who are
    exceptions to the private flag.

    Users may read and annotate with the tag. Readers may only read.

    Only site admins or regular users in the parent namespace's "admins" group
    may make this change.

    Any other user making such a request will result in a PermissionError
    being thrown.
    """
    if user.is_admin or namespace.admins.filter(pk=user.pk).exists():
        t = models.Tag.objects.create_tag(
            user=user,
            name=name,
            description=description,
            type_of=type_of,
            namespace=namespace,
            private=private,
        )
        users_list: List[User] = [
            user,
        ]
        if users:
            users_list += [u for u in users if u.id != user.id]
        t.users.add(*users_list)
        if readers:
            t.readers.add(*readers)
        else:
            readers = []
        logger.msg(
            "Create tag.",
            user=user.username,
            name=name,
            description=description,
            type_of=t.get_type_of_display(),
            namespace=namespace.name,
            private=private,
            users=[u.username for u in users_list],
            readers=[r.username for r in readers],
        )
        return t
    else:
        raise PermissionError(
            _("User doesn't have permission to create a tag in the namespace.")
        )


def get_tag(user: User, name: str, namespace: str) -> Dict:
    """
    Return a dictionary representation of the referenced tag as viewed by
    the referenced user (with associated privileges).

    Admin users of the parent namespace see all attributes of all aspects of
    the tag. Regular users see a limited set of attributes on only those
    aspects of the tag for which they have privileges to see.
    """
    n = models.Namespace.objects.get(name=namespace)
    tag = models.Tag.objects.get(name=name, namespace=n)
    if user.is_admin or n.admins.filter(pk=user.pk).exists():
        result = {
            "name": tag.name,
            "namespace": n.name,
            "description": tag.description,
            "path": tag.path,
            "type_of": tag.get_type_of_display(),
            "private": tag.private,
            "users": [user.username for user in tag.users.all()],
            "readers": [reader.username for reader in tag.readers.all()],
            "created_by": tag.created_by.username,
            "created_on": str(tag.created_on),
            "updated_by": tag.updated_by.username,
            "updated_on": str(tag.updated_on),
        }
    else:
        if tag.is_reader(user):
            result = {
                "name": tag.name,
                "namespace": n.name,
                "description": tag.description,
                "path": tag.path,
                "type_of": tag.get_type_of_display(),
                "private": tag.private,
            }
        else:
            raise PermissionError(
                _("User doesn't have permission to view the tag.")
            )
    return result


def update_tag_description(
    user: User, name: str, namespace: str, description: str
) -> models.Tag:
    """
    Update the description of the tag with the referenced name and namespace.

    Only site admins or regular users in the parent namespace's "admins" group
    may make this change.

    Any other user making such a request will result in a PermissionError
    being thrown.
    """
    n = models.Namespace.objects.get(name=namespace)
    if user.is_admin or n.admins.filter(pk=user.pk).exists():
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
    else:
        raise PermissionError(
            _("User doesn't have permission to update the tag.")
        )


def set_tag_private(
    user: User, name: str, namespace: str, private: bool
) -> models.Tag:
    """
    Set the referenced tag's private flag.

    Only site admins or regular users in the parent namespace's "admins" group
    may make this change.

    Any other user making such a request will result in a PermissionError
    being thrown.
    """
    n = models.Namespace.objects.get(name=namespace)
    if user.is_admin or n.admins.filter(pk=user.pk).exists():
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
    else:
        raise PermissionError(
            _("User doesn't have permission to update the tag.")
        )


def add_tag_users(
    user: User, name: str, namespace: str, users: Sequence[User]
) -> models.Tag:
    """
    Add the referenced user objects to the tag's users list (who can both
    annotate and read the tag).

    Only site admins or regular users in the parent namespace's "admins" group
    may make this change.

    Any other user making such a request will result in a PermissionError
    being thrown.
    """
    n = models.Namespace.objects.get(name=namespace)
    if user.is_admin or n.admins.filter(pk=user.pk).exists():
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
    else:
        raise PermissionError(
            _("User doesn't have permission to add users to the tag.")
        )


def remove_tag_users(
    user: User, name: str, namespace: str, users: Sequence[User]
) -> models.Tag:
    """
    Remove the referenced user object from the tag's users list (who can both
    annotate and read the tag).

    Only site admins or regular users in the parent namespace's "admins" group
    may make this change.

    Any other user making such a request will result in a PermissionError
    being thrown.
    """
    n = models.Namespace.objects.get(name=namespace)
    if user.is_admin or n.admins.filter(pk=user.pk).exists():
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
    else:
        raise PermissionError(
            _("User doesn't have permission to remove users from the tag.")
        )


def add_tag_readers(
    user: User, name: str, namespace: str, readers: Sequence[User]
) -> models.Tag:
    """
    Add the referenced user objects to the tag's readers list (who can read a
    private tag).

    Only site admins or regular users in the parent namespace's "admins" group
    may make this change.

    Any other user making such a request will result in a PermissionError
    being thrown.
    """
    n = models.Namespace.objects.get(name=namespace)
    if user.is_admin or n.admins.filter(pk=user.pk).exists():
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
    else:
        raise PermissionError(
            _("User doesn't have permission to add readers to the tag.")
        )


def remove_tag_readers(
    user: User, name: str, namespace: str, readers: Sequence[User]
) -> models.Tag:
    """
    Remove the referenced user objects from the tag's readers list (those who
    can read a private tag).

    Only site admins or regular users in the parent namespace's "admins" group
    may make this change.

    Any other user making such a request will result in a PermissionError
    being thrown.
    """
    n = models.Namespace.objects.get(name=namespace)
    if user.is_admin or n.admins.filter(pk=user.pk).exists():
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
    else:
        raise PermissionError(
            _("User doesn't have permission to remove readers from the tag.")
        )


def check_users_tags(user: models.User, tags: Set[str]) -> bool:
    """
    Given a list of namespace/tag tuples, return a boolean to indicate that the
    referenced user is allowed to use such tags to annotate values onto
    objects.
    """
    # Site admins always have privileges.
    if user.is_admin:
        return True
    # Count the number of tags that the user has permission to use.
    tag_matches = models.get_users_query(user, tags).count()
    # If the number of tag_matches is the same as the number of unique tags to
    # be checked, then the user MUST have permission to read on all the
    # referenced tags.
    return tag_matches == len(set(tags))


def check_readers_tags(user: models.User, tags: Set[str]) -> bool:
    """
    Given a list of namespace/tag tuples, return a boolean to indicate that the
    referenced user is allowed to use such tags to read the values annotated
    onto objects.
    """
    # Site admins always have privileges.
    if user.is_admin:
        return True
    # Count the number of tags that the user has permission to use.
    tag_matches = models.get_readers_query(user, tags).count()
    # If the number of tag_matches is the same as the number of unique tags to
    # be checked, then the user MUST have permission to read on all the
    # referenced tags.
    return tag_matches == len(set(tags))


def set_object_tag_value(
    user: models.User,
    object_id: str,
    namespace: str,
    tag: str,
    value: HttpRequest,
):
    """
    Set the referenced namespace/tag on the specified object to the value
    contained within the incoming HttpRequest. Assumes the privileges of the
    referenced user.

    The type of the value in the HttpRequest is infered (and checked against)
    the type of the referenced tag.

    If the operation failed, an exception will be raised.
    """


def set_object_tag_values(user: User, object_tag_values: Sequence[Dict]):
    """
    Set a number of unique namespace/tag values on each of the objects
    referenced in the sequence. Assumes the privileges of the referenced user.

    The object_tag_values should be of the form:

    [
        {
            "object_id": "my-object1",
            "values": {
                "namespace/tag": "a value to store",
                "namespace2/tag2": 123,
            },
        },
        {
            "object_id": "my-object2",
            "values": {
                "namespace3/ta3": "a unique value",
                "namespace2/tag2": 456,
            },
        },
        ... next object with other unique tag values...
    ]

    If the operation failed, an exception will be raised.
    """


def set_object_tag_values_by_query(
    user: User, query: str, tag_values: Sequence[Dict]
):
    """
    Sets the same namespace/tag values to each of the objects matched by the
    BFQL query. Assumes the privileges of the referenced user.

    If the operation failed, an exception will be raised.
    """


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


def get_object_tag_values_by_query(user: User, query: str, tags: Sequence):
    """
    Get the values associated with the referenced tags on objects that match
    the BFQL query. Only tags/values visible to the referenced user will be
    returned.

    The tags sequence should be of the form:
    [
        "namespace1/tag1",
        "namespace2/tag2",
        ... etc...
    ]
    """


def delete_tags_from_object(user: User, object_id: str, tags: Sequence):
    """
    Delete referenced tag-values from the referenced object.

    The tags sequence should be of the form:
    [
        "namespace1/tag1",
        "namespace2/tag2",
        ... etc...
    ]
    """


def delete_object_tag_values_by_query(user: User, query: str, tags: Sequence):
    """
    Delete referenced tag-values from objects that match the BFQL query.

    The tags sequence should be of the form:
    [
        "namespace1/tag1",
        "namespace2/tag2",
        ... etc...
    ]
    """
