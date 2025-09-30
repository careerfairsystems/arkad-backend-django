import hashlib
import json
import asyncio
import logging
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional, Callable, Awaitable

from channels.db import database_sync_to_async  # type: ignore[import-untyped]
from pydantic import BaseModel, Field, ValidationError

from person_counter.models import RoomModel, PersonCounter
from user_models.models import User
from arkad.consumers import AuthenticatedAsyncWebsocketConsumer

# =============================================================================
# Pydantic Models for WebSocket Message Payloads
# =============================================================================


class BaseWebsocketMessage(BaseModel):
    """Base model for all websocket messages with a timestamp."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        # Pydantic configuration for JSON serialization
        json_encoders = {datetime: lambda dt: dt.isoformat()}


# --- Outgoing Message Models (Server -> Client) ---


class ErrorMessage(BaseWebsocketMessage):
    type: Literal["error"] = "error"
    message: str


class ConnectionSuccessMessage(BaseWebsocketMessage):
    type: Literal["connection"] = "connection"
    message: str
    counter: int
    room: str
    all_rooms: Dict[str, int]


class CounterUpdateMessage(BaseWebsocketMessage):
    type: Literal["counter_update"] = "counter_update"
    action: str
    room: str
    counter: int
    delta: int
    user: str
    all_rooms: Dict[str, int]
    is_my_room: bool = False  # Will be set per-client


class CounterValueMessage(BaseWebsocketMessage):
    type: Literal["counter_value"] = "counter_value"
    counter: int
    room: str
    all_rooms: Dict[str, int]


class AllRoomsUpdateMessage(BaseWebsocketMessage):
    type: Literal["all_rooms_update"] = "all_rooms_update"
    all_rooms: Dict[str, int]


class UserEventMessage(BaseWebsocketMessage):
    type: Literal["user_joined", "user_left"]
    message: str
    room: str
    counter: int
    all_rooms: Dict[str, int]
    is_my_room: bool = False  # Will be set per-client


class PongMessage(BaseWebsocketMessage):
    type: Literal["pong"] = "pong"
    room: Optional[str]


# --- Incoming Message Models (Client -> Server) ---


class BaseIncomingMessage(BaseModel):
    type: str
    room: Optional[str] = None


# =============================================================================
# Room Counter Consumer
# =============================================================================


class RoomCounterConsumer(AuthenticatedAsyncWebsocketConsumer):
    # Global group for all connected users
    global_group_name: str = "global_counter_updates"

    # Attributes initialized at connect
    room_name: Optional[str] = None
    room_group_name: Optional[str] = None
    room: Optional[RoomModel] = None

    async def send_pydantic(self, message: BaseWebsocketMessage) -> None:
        """Serializes a Pydantic model and sends it to the client."""
        await self.send(text_data=message.model_dump_json())

    @staticmethod
    def _get_safe_channel_name(name: str) -> str:
        """Creates a safe channel group name from a room name."""
        return hashlib.sha256(name.encode()).hexdigest()

    async def connect(self) -> None:
        self.parse_query_params()
        if not await self.authenticate_from_query(expected_token_type="websocket"):
            return

        room_name_qp = self.get_query_param("room")
        if not room_name_qp:
            await self.accept()
            await self.send_pydantic(ErrorMessage(message="Room name is required."))
            await self.close(code=4000)
            return

        self.room_name = urllib.parse.unquote(room_name_qp)
        room = await self._get_room(self.room_name)

        if not room:
            await self.accept()
            await self.send_pydantic(
                ErrorMessage(message=f"Invalid room: {self.room_name}")
            )
            await self.close(code=4004)
            return

        self.room = room
        safe_name = self._get_safe_channel_name(self.room_name)
        self.room_group_name = f"counter_{safe_name}"

        # Join room-specific and global groups
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.channel_layer.group_add(self.global_group_name, self.channel_name)

        await self.accept()

        # Send connection success message
        current_counter = await self._get_current_counter(self.room_name)
        all_rooms = await self._get_all_room_counters()
        await self.send_pydantic(
            ConnectionSuccessMessage(
                message=f'Connected to room "{self.room_name}" as {self.user.email}',
                counter=current_counter,
                room=self.room_name,
                all_rooms=all_rooms,
            )
        )

        # Notify all users about the new user joining
        await self.channel_layer.group_send(
            self.global_group_name,
            {
                "type": "user_event",
                "event_type": "user_joined",
                "user": self.user.email,
                "room": self.room_name,
            },
        )

    async def disconnect(self, close_code: int) -> None:
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )
        await self.channel_layer.group_discard(
            self.global_group_name, self.channel_name
        )

        if hasattr(self, "user") and self.room_name:
            await self.channel_layer.group_send(
                self.global_group_name,
                {
                    "type": "user_event",
                    "event_type": "user_left",
                    "user": self.user.email,
                    "room": self.room_name,
                },
            )

    async def receive(
        self, text_data: Optional[str] = None, bytes_data: Optional[bytes] = None
    ) -> None:
        if not text_data:
            return

        try:
            data = json.loads(text_data)
            incoming_message = BaseIncomingMessage.model_validate(data)

            handler_map: Dict[str, Callable[[Dict[str, Any]], Awaitable[None]]] = {
                "increment": self.handle_increment,
                "decrement": self.handle_decrement,
                "reset": self.handle_reset,
                "get_counter": self.handle_get_counter,
                "get_all_rooms": self.handle_get_all_rooms,
                "ping": self.handle_ping,
            }

            handler = handler_map.get(incoming_message.type, self.handle_unknown_type)
            await handler(data)

        except (json.JSONDecodeError, ValidationError) as e:
            await self.send_pydantic(
                ErrorMessage(message=f"Invalid message format: {e}")
            )
        except Exception as e:
            logging.exception("Error processing message in RoomCounterConsumer")
            await self.send_pydantic(
                ErrorMessage(message=f"An internal error occurred: {e}")
            )

    # --- Incoming Message Handlers ---

    async def handle_increment(self, data: Dict[str, Any]) -> None:
        await self._broadcast_update(delta=1, action="increment")

    async def handle_decrement(self, data: Dict[str, Any]) -> None:
        await self._broadcast_update(delta=-1, action="decrement")

    async def handle_reset(self, data: Dict[str, Any]) -> None:
        assert self.room is not None
        new_counter = await self._reset_counter(self.room, self.user)
        all_rooms = await self._get_all_room_counters()
        await self.channel_layer.group_send(
            self.global_group_name,
            {
                "type": "counter_update_event",
                "action": "reset",
                "room": self.room_name,
                "counter": new_counter.count,
                "delta": new_counter.delta,
                "user": self.user.email,
                "all_rooms": all_rooms,
            },
        )

    async def handle_get_counter(self, data: Dict[str, Any]) -> None:
        assert self.room_name is not None
        current_counter = await self._get_current_counter(self.room_name)
        all_rooms = await self._get_all_room_counters()
        await self.send_pydantic(
            CounterValueMessage(
                counter=current_counter, room=self.room_name, all_rooms=all_rooms
            )
        )

    async def handle_get_all_rooms(self, data: Dict[str, Any]) -> None:
        all_rooms = await self._get_all_room_counters()
        await self.send_pydantic(AllRoomsUpdateMessage(all_rooms=all_rooms))

    async def handle_ping(self, data: Dict[str, Any]) -> None:
        await self.send_pydantic(PongMessage(room=self.room_name))

    async def handle_unknown_type(self, data: Dict[str, Any]) -> None:
        msg_type = data.get("type", "unknown")
        await self.send_pydantic(
            ErrorMessage(message=f"Unknown message type: {msg_type}")
        )

    # --- Group Event Handlers ---

    async def counter_update_event(self, event: Dict[str, Any]) -> None:
        """Handles counter_update events broadcast to the group."""
        is_my_room = event["room"] == self.room_name
        event["type"] = "counter_update"
        message = CounterUpdateMessage(**event, is_my_room=is_my_room)
        await self.send_pydantic(message)

    async def user_event(self, event: Dict[str, Any]) -> None:
        """Handles user_joined and user_left events."""
        if event["user"] == self.user.email and event["event_type"] == "user_joined":
            return  # Don't notify user about their own join event

        event_type = event["event_type"]
        user_email = event["user"]
        room_name = event["room"]
        message_text = (
            f"{user_email} joined room '{room_name}'"
            if event_type == "user_joined"
            else f"{user_email} left room '{room_name}'"
        )
        is_my_room = room_name == self.room_name
        all_rooms = await self._get_all_room_counters()
        current_counter = all_rooms.get(room_name, 0)

        message = UserEventMessage(
            type=event_type,
            message=message_text,
            room=room_name,
            counter=current_counter,
            all_rooms=all_rooms,
            is_my_room=is_my_room,
        )
        await self.send_pydantic(message)

    # --- Helper & Database Methods ---

    async def _broadcast_update(self, delta: int, action: str) -> None:
        """Applies a delta and broadcasts the update to all users."""
        assert self.room is not None and self.room_name is not None
        new_counter = await self._apply_delta(self.room, delta, self.user)
        all_rooms = await self._get_all_room_counters()
        await self.channel_layer.group_send(
            self.global_group_name,
            {
                "type": "counter_update_event",
                "action": action,
                "room": self.room_name,
                "counter": new_counter.count,
                "delta": delta,
                "user": self.user.email,
                "all_rooms": all_rooms,
            },
        )

    @database_sync_to_async  # type: ignore[misc]
    def _get_room(self, room_name: str) -> Optional[RoomModel]:
        return RoomModel.objects.filter(name=room_name).first()

    @database_sync_to_async  # type: ignore[misc]
    def _get_current_counter(self, room_name: str) -> int:
        counter = PersonCounter.get_last(room_name)
        return counter.count if counter else 0

    @database_sync_to_async  # type: ignore[misc]
    def _get_all_room_counters(self) -> Dict[str, int]:
        return {
            room.name: (
                c.count if (c := PersonCounter.get_last(room.name)) is not None else 0
            )
            for room in RoomModel.objects.all()
        }

    @database_sync_to_async  # type: ignore[misc]
    def _apply_delta(
        self, room: RoomModel, delta: int, updated_by: Optional[User] = None
    ) -> PersonCounter:
        return PersonCounter.add_delta(room, delta, updated_by=updated_by)

    @database_sync_to_async  # type: ignore[misc]
    def _reset_counter(
        self, room: RoomModel, updated_by: Optional[User] = None
    ) -> PersonCounter:
        return PersonCounter.reset_to_zero(room, updated_by=updated_by)


# =============================================================================
# Ping Consumer (Legacy/Utility)
# =============================================================================


class PingConsumer(AuthenticatedAsyncWebsocketConsumer):
    heartbeat_task: Optional[asyncio.Task[None]] = None

    async def connect(self) -> None:
        self.parse_query_params()
        if not await self.authenticate_from_query(expected_token_type="websocket"):
            return

        await self.accept()
        await self.send(
            text_data=json.dumps(
                {"type": "connection", "message": "Connection established"}
            )
        )

    async def disconnect(self, close_code: int) -> None:
        if self.heartbeat_task and not self.heartbeat_task.done():
            self.heartbeat_task.cancel()
            try:
                # Give the task a moment to process cancellation
                await asyncio.wait_for(self.heartbeat_task, timeout=1)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                logging.info("Heartbeat task successfully cancelled.")
        await super().disconnect(close_code)

    async def receive(
        self, text_data: Optional[str] = None, bytes_data: Optional[bytes] = None
    ) -> None:
        if not text_data:
            return

        try:
            data = json.loads(text_data)
            msg_type = data.get("type")

            if msg_type == "ping":
                await self.send(text_data=json.dumps({"type": "pong"}))
            elif msg_type == "heartbeat":
                if not self.heartbeat_task or self.heartbeat_task.done():
                    self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            else:
                await self.send(
                    text_data=json.dumps({"type": "error", "message": "Unknown type"})
                )

        except json.JSONDecodeError:
            await self.send(
                text_data=json.dumps({"type": "error", "message": "Invalid JSON"})
            )

    async def _heartbeat_loop(self) -> None:
        """Sends a heartbeat message every 10 seconds until cancelled."""
        while True:
            try:
                await asyncio.sleep(10)
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "heartbeat",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                )
            except asyncio.CancelledError:
                logging.info("Heartbeat loop is stopping.")
                break  # Exit the loop when cancelled
            except Exception:
                logging.warning("Heartbeat loop broke due to connection error.")
                break
