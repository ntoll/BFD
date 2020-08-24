"""
Tests for log configuration.

Copyright (C) 2020 Nicholas H.Tollervey
"""
import uuid
from django.conf import settings
from bfd.datastore import utils


def test_get_uuid():
    """
    Ensure the get_uuid method returns a UUID5 based upon the settings.BFD_UUID
    and the passed in namespace and tag name.
    """
    namespace = "my_namespace"
    tag = "my_tag"
    expected = uuid.uuid5(uuid.uuid5(settings.BFD_UUID, namespace), tag)
    assert utils.get_uuid(namespace, tag) == expected
