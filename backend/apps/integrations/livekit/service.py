import json
import logging
from datetime import timedelta

from asgiref.sync import async_to_sync
from django.conf import settings
from livekit import api as lk_api

from apps.core.exceptions import ExternalServiceError

logger = logging.getLogger("apps.integrations.livekit")


class LiveKitService:
    """Thin wrapper around the LiveKit server SDK.

    Methods prefixed with `a` are native coroutines meant to be awaited
    directly from async code (Django Channels consumers). Their sync
    counterparts (no prefix) wrap them with `async_to_sync` for use from
    regular DRF views, which run in a plain synchronous thread.
    """

    def __init__(self):
        self.http_url = settings.LIVEKIT_HTTP_URL
        self.api_key = settings.LIVEKIT_API_KEY
        self.api_secret = settings.LIVEKIT_API_SECRET

    def _client(self) -> lk_api.LiveKitAPI:
        return lk_api.LiveKitAPI(self.http_url, self.api_key, self.api_secret)

    # ------------------------------------------------------------------
    # Access tokens (pure local JWT signing, no network call)
    # ------------------------------------------------------------------

    def generate_access_token(
        self,
        *,
        room_name: str,
        identity: str,
        display_name: str,
        is_host: bool = False,
        can_publish: bool = True,
        can_subscribe: bool = True,
        metadata: dict | None = None,
        ttl: timedelta = timedelta(hours=6),
    ) -> str:
        grants = lk_api.VideoGrants(
            room_join=True,
            room=room_name,
            room_admin=is_host,
            can_publish=can_publish,
            can_subscribe=can_subscribe,
            can_publish_data=True,
        )
        token = (
            lk_api.AccessToken(self.api_key, self.api_secret)
            .with_identity(identity)
            .with_name(display_name)
            .with_grants(grants)
            .with_ttl(ttl)
        )
        if metadata:
            token = token.with_metadata(json.dumps(metadata))
        return token.to_jwt()

    # ------------------------------------------------------------------
    # Room management
    # ------------------------------------------------------------------

    async def aensure_room(self, *, room_name: str, max_participants: int = 0, empty_timeout: int = 300):
        async with self._client() as client:
            try:
                return await client.room.create_room(
                    lk_api.CreateRoomRequest(
                        name=room_name,
                        max_participants=max_participants,
                        empty_timeout=empty_timeout,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                logger.exception("LiveKit create_room failed for %s", room_name)
                raise ExternalServiceError(detail="Could not create the video room.") from exc

    def ensure_room(self, **kwargs):
        return async_to_sync(self.aensure_room)(**kwargs)

    async def adelete_room(self, *, room_name: str):
        async with self._client() as client:
            try:
                return await client.room.delete_room(lk_api.DeleteRoomRequest(room=room_name))
            except Exception as exc:  # noqa: BLE001
                logger.exception("LiveKit delete_room failed for %s", room_name)
                raise ExternalServiceError(detail="Could not delete the video room.") from exc

    def delete_room(self, **kwargs):
        return async_to_sync(self.adelete_room)(**kwargs)

    async def alist_participants(self, *, room_name: str) -> list:
        async with self._client() as client:
            response = await client.room.list_participants(lk_api.ListParticipantsRequest(room=room_name))
            return list(response.participants)

    def list_participants(self, **kwargs) -> list:
        return async_to_sync(self.alist_participants)(**kwargs)

    # ------------------------------------------------------------------
    # Host controls
    # ------------------------------------------------------------------

    async def aremove_participant(self, *, room_name: str, identity: str):
        async with self._client() as client:
            try:
                return await client.room.remove_participant(
                    lk_api.RoomParticipantIdentity(room=room_name, identity=identity)
                )
            except Exception as exc:  # noqa: BLE001
                logger.exception("LiveKit remove_participant failed for %s/%s", room_name, identity)
                raise ExternalServiceError(detail="Could not remove the participant.") from exc

    def remove_participant(self, **kwargs):
        return async_to_sync(self.aremove_participant)(**kwargs)

    async def amute_published_track(self, *, room_name: str, identity: str, track_sid: str, muted: bool = True):
        async with self._client() as client:
            return await client.room.mute_published_track(
                lk_api.MuteRoomTrackRequest(room=room_name, identity=identity, track_sid=track_sid, muted=muted)
            )

    def mute_published_track(self, **kwargs):
        return async_to_sync(self.amute_published_track)(**kwargs)

    async def amute_all_participants(self, *, room_name: str, exclude_identity: str | None = None):
        """Mutes every published microphone track in the room except `exclude_identity`
        (typically the host triggering the action)."""
        participants = await self.alist_participants(room_name=room_name)
        muted_identities = []
        async with self._client() as client:
            for participant in participants:
                if participant.identity == exclude_identity:
                    continue
                for track in participant.tracks:
                    if track.type == lk_api.TrackType.AUDIO and not track.muted:
                        await client.room.mute_published_track(
                            lk_api.MuteRoomTrackRequest(
                                room=room_name,
                                identity=participant.identity,
                                track_sid=track.sid,
                                muted=True,
                            )
                        )
                        muted_identities.append(participant.identity)
        return muted_identities

    def mute_all_participants(self, **kwargs) -> list:
        return async_to_sync(self.amute_all_participants)(**kwargs)

    # ------------------------------------------------------------------
    # Realtime signaling via LiveKit's data channel
    # ------------------------------------------------------------------

    async def asend_data(self, *, room_name: str, payload: dict, topic: str | None = None):
        async with self._client() as client:
            return await client.room.send_data(
                lk_api.SendDataRequest(
                    room=room_name,
                    data=json.dumps(payload).encode("utf-8"),
                    kind=lk_api.DataPacket.RELIABLE,
                    topic=topic,
                )
            )

    def send_data(self, **kwargs):
        return async_to_sync(self.asend_data)(**kwargs)

    # ------------------------------------------------------------------
    # Egress (cloud recording)
    # ------------------------------------------------------------------

    def _build_file_output(self, *, filepath: str) -> lk_api.EncodedFileOutput:
        if settings.AWS_STORAGE_BUCKET_NAME:
            return lk_api.EncodedFileOutput(
                filepath=filepath,
                s3=lk_api.S3Upload(
                    access_key=settings.AWS_ACCESS_KEY_ID,
                    secret=settings.AWS_SECRET_ACCESS_KEY,
                    region=settings.AWS_S3_REGION_NAME,
                    bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    endpoint=settings.AWS_S3_ENDPOINT_URL or "",
                ),
            )
        return lk_api.EncodedFileOutput(filepath=filepath)

    async def astart_room_composite_egress(self, *, room_name: str, filepath: str) -> lk_api.EgressInfo:
        async with self._client() as client:
            try:
                return await client.egress.start_room_composite_egress(
                    lk_api.RoomCompositeEgressRequest(
                        room_name=room_name,
                        layout="grid",
                        file_outputs=[self._build_file_output(filepath=filepath)],
                    )
                )
            except Exception as exc:  # noqa: BLE001
                logger.exception("LiveKit start_room_composite_egress failed for %s", room_name)
                raise ExternalServiceError(detail="Could not start recording for this meeting.") from exc

    def start_room_composite_egress(self, **kwargs) -> lk_api.EgressInfo:
        return async_to_sync(self.astart_room_composite_egress)(**kwargs)

    async def astop_egress(self, *, egress_id: str) -> lk_api.EgressInfo:
        async with self._client() as client:
            try:
                return await client.egress.stop_egress(lk_api.StopEgressRequest(egress_id=egress_id))
            except Exception as exc:  # noqa: BLE001
                logger.exception("LiveKit stop_egress failed for %s", egress_id)
                raise ExternalServiceError(detail="Could not stop the recording.") from exc

    def stop_egress(self, **kwargs) -> lk_api.EgressInfo:
        return async_to_sync(self.astop_egress)(**kwargs)

    def verify_webhook(self, *, body: str, auth_token: str) -> lk_api.WebhookEvent:
        verifier = lk_api.TokenVerifier(self.api_key, self.api_secret)
        receiver = lk_api.WebhookReceiver(verifier)
        return receiver.receive(body, auth_token)


livekit_service = LiveKitService()
