"""
Contains utility functions used in all layers of the data store.
"""
import uuid
from django.conf import settings


def get_uuid(namespace_name: str, tag_name: str) -> uuid.UUID:
    """
    Given namespace and tag names, return a UUID generated from the SHA-1
    of these values and the unique-to-this-instance BFD_UUID which should be
    set in the environment variables.
    """
    seed_uuid = settings.BFD_UUID
    namespace_uuid = uuid.uuid5(seed_uuid, namespace_name)
    return uuid.uuid5(namespace_uuid, tag_name)
