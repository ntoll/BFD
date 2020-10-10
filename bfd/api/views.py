"""
Class based views for the API.

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
