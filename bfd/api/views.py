"""
Class based views for the API.

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
from datastore import models, logic
from api import serializers
from django.http import Http404
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class UserDetail(APIView):
    """
    Retrieve basic information about the referenced user.
    """

    permission_classes = [IsAuthenticated]

    def get_object(self, username):
        try:
            return models.User.objects.get(username=username)
        except models.User.DoesNotExist:
            raise Http404

    def get(self, request, username, format=None):
        user = self.get_object(username)
        serializer = serializers.UserSerializer(user)
        return Response(serializer.data)


class NamespaceCreate(APIView):
    """
    Create core information about a new namespace.
    """

    permission_classes = [IsAdminUser]

    def post(self, request, format=None):
        serializer = serializers.NamespaceCreateSerializer(data=request.data)
        if serializer.is_valid():
            ns = logic.create_namespace(
                request.user,
                serializer["name"].value,
                serializer["description"].value,
                serializer["admins"].value,
            )
            out = serializers.NamespaceDetailSerializer(ns)
            return Response(out.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NamespaceDetail(APIView):
    """
    Retrieve and set basic information about the referenced namespace.
    """

    def get_object(self, namespace):
        try:
            return models.Namespace.objects.get(name=namespace)
        except models.Namespace.DoesNotExist:
            raise Http404

    def get(self, request, namespace, format=None):
        ns_object = self.get_object(namespace)
        serializer = serializers.NamespaceDetailSerializer(ns_object)
        return Response(serializer.data)

    def put(self, request, namespace, format=None):
        ns_object = self.get_object(namespace)
        serializer = serializers.NamespaceUpdateSerializer(
            ns_object, data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, namespace, format=None):
        ns_object = self.get_object(namespace)
        ns_object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagDetail(APIView):
    """
    Retrieve and set basic information about the referenced tag.
    """

    def get_object(self, namespace, tag):
        try:
            tag_path = f"{namespace}/{tag}"
            return models.Tag.objects.get(path=tag_path)
        except models.Tag.DoesNotExist:
            raise Http404

    def get(self, request, namespace, tag, format=None):
        tag_object = self.get_object(namespace, tag)
        serializer = serializers.TagSerializer(tag_object)
        return Response(serializer.data)
