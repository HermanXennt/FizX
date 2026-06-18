import json

from rest_framework.renderers import JSONRenderer


def to_json_safe(data):
    """Converts a DRF serializer's `.data` (which can contain raw UUID, Decimal,
    and datetime instances) into plain JSON-safe primitives.

    Needed before handing serialized data to the Channels layer: channels_redis
    encodes group_send payloads with msgpack, which - unlike DRF's own
    JSONRenderer - has no idea how to pack a UUID or Decimal.
    """
    return json.loads(JSONRenderer().render(data))
