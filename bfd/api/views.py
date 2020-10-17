"""
Class based views for the API.

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
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from datastore import models
from datastore import logic


@api_view(["GET"])
@permission_classes((IsAuthenticated,))
def user_detail(request, username, format=None):
    """
    Retrieve simple representation of the referenced user.
    """
    try:
        user = models.User.objects.get(username=username)
    except models.User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    return Response(
        {
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_superuser,
            "last_login": user.last_login,
        }
    )


class NamespaceDetail(APIView):
    """
    Represents the API view of a namespace.
    """


@api_view(
    ["POST",]
)
@permission_classes((IsAuthenticated,))
def new_namespace(request, format=None):
    """
    Create a new namespace from the given data.
    """
    try:
        namespace = logic.create_namespace(
            request.user,
            request.data["name"],
            request.data["description"],
            request.data.get("admins", list()),
        )
        data = logic.get_namespace(request.user, namespace.name)
        return Response(data)
    except PermissionError:
        return Response(status=status.HTTP_403_FORBIDDEN)


@api_view(
    ["GET", "PUT",]
)
@permission_classes((IsAuthenticated,))
def namespace_detail(request, namespace, format=None):
    """
    Get or update an existing namespace.
    """
    if request.method == "GET":
        try:
            data = logic.get_namespace(request.user, namespace)
            return Response(data)
        except models.Namespace.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except PermissionError:
            return Response(status=status.HTTP_403_FORBIDDEN)

    if request.method == "PUT":
        try:
            if "description" in request.data:
                ns = logic.update_namespace_description(
                    request.user, namespace, request.data["description"]
                )
                return Response({"description": ns.description,})
            elif "add_admins" in request.data:
                admin_names = request.data.get("add_admins", list())
                admin_users = models.User.objects.filter(
                    username__in=admin_names
                )
                if len(admin_users) > 0:
                    ns = logic.add_namespace_admins(
                        request.user, namespace, admin_users
                    )
                    return Response(
                        {
                            "admin_users": [
                                admin.username for admin in ns.admins
                            ]
                        }
                    )
                else:
                    return Response(status=status.HTTP_400_BAD_REQUEST)
            elif "remove_admins" in request.data:
                admin_names = request.data.get("add_admins", list())
                admin_users = models.User.objects.filter(
                    username__in=admin_names
                )
                if len(admin_users) > 0:
                    ns = logic.remove_namespace_admins(
                        request.user, namespace, admin_users
                    )
                    return Response(
                        {
                            "admin_users": [
                                admin.username for admin in ns.admins
                            ]
                        }
                    )
                else:
                    return Response(status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        except models.Namespace.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except PermissionError:
            return Response(status=status.HTTP_403_FORBIDDEN)


@api_view(
    ["POST",]
)
@permission_classes((IsAuthenticated,))
def new_tag(request, namespace, format=None):
    """
    Create a new tag in the referenced namespace from the given data.
    """
    try:
        namespace_object = models.Namespace.get(name=namespace)
        tag = logic.create_tag(
            request.user,
            request.data["name"],
            request.data["description"],
            request.data["type_of"],
            namespace_object,
            request.data.get("private", False),
            request.data.get("users", list()),
            request.data.get("readers", list()),
        )
        data = logic.get_tag(request.user, tag.name, namespace.name)
        return Response(data)
    except models.Namespace.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    except PermissionError:
        return Response(status=status.HTTP_403_FORBIDDEN)


@api_view(
    ["GET", "PUT",]
)
@permission_classes((IsAuthenticated,))
def tag_detail(request, namespace, tag, format=None):
    """
    Get or update an existing namespace.
    """
    if request.method == "GET":
        try:
            data = logic.get_tag(request.user, tag, namespace)
            return Response(data)
        except models.Tag.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except models.Namespace.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except PermissionError:
            return Response(status=status.HTTP_403_FORBIDDEN)

    if request.method == "PUT":
        try:
            if "description" in request.data:
                tag = logic.update_tag_description(
                    request.user, tag, namespace, request.data["description"]
                )
                return Response({"description": tag.description,})
            elif "add_admins" in request.data:
                admin_names = request.data.get("add_admins", list())
                admin_users = models.User.objects.filter(
                    username__in=admin_names
                )
                if len(admin_users) > 0:
                    ns = logic.add_namespace_admins(
                        request.user, namespace, admin_users
                    )
                    return Response(
                        {
                            "admin_users": [
                                admin.username for admin in ns.admins
                            ]
                        }
                    )
                else:
                    return Response(status=status.HTTP_400_BAD_REQUEST)
            elif "remove_admins" in request.data:
                admin_names = request.data.get("add_admins", list())
                admin_users = models.User.objects.filter(
                    username__in=admin_names
                )
                if len(admin_users) > 0:
                    ns = logic.remove_namespace_admins(
                        request.user, namespace, admin_users
                    )
                    return Response(
                        {
                            "admin_users": [
                                admin.username for admin in ns.admins
                            ]
                        }
                    )
                else:
                    return Response(status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        except models.Namespace.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except PermissionError:
            return Response(status=status.HTTP_403_FORBIDDEN)
