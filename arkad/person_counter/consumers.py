import hashlib
import json
import asyncio
import logging
from typing import Any, Dict, Optional
import urllib.parse

from channels.db import database_sync_to_async  # type: ignore[import-untyped]
from datetime import datetime
from person_counter.models import RoomModel, PersonCounter
from user_models.models import User

from arkad.consumers import AuthenticatedAsyncWebsocketConsumer


class RoomCounterConsumer(AuthenticatedAsyncWebsocketConsumer):
    # Global group for all connected users
    global_group_name: str = "global_counter_updates"

    # Attributes initialized at connect
    room_name: str
    room_group_name: str
    room: RoomModel

    async def connect(self) -> None:
        # Parse query and authenticate (prefers cookie session via AuthMiddlewareStack)
        self.parse_query_params()
        authed: bool = await self.authenticate_from_query(
            expected_token_type="websocket"
        )
        if not authed:
            return

        # Get room name
        room_name_qp: Optional[str] = self.get_query_param("room", "default")
        self.room_name = urllib.parse.unquote(room_name_qp or "default")

        # Make sure that room is a valid room name
        try:
            room: Optional[RoomModel] = await self._get_room(self.room_name)
            if not room:
                await self.close(code=4004)
                return
            self.room = room
        except Exception as e:
            logging.exception(e)
            await self.close(code=4004)
            return

        def _safe_channel_name(name: str) -> str:
            # Create a safe channel name by hashing the room name
            hash_object = hashlib.sha256(name.encode())
            return hash_object.hexdigest()

        safe_name = _safe_channel_name(room_name_qp)
        self.room_group_name = (
            f"counter_{safe_name}"  # Room-specific group which is safe for channel
        )
        # Join both room-specific group and global group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.channel_layer.group_add(self.global_group_name, self.channel_name)

        await self.accept()

        # Send current counter value and connection message
        current_counter: int = await self._get_current_counter(self.room_name)
        all_rooms: Dict[str, int] = await self._get_all_room_counters()

        await self.send(
            text_data=json.dumps(
                {
                    "type": "connection",
                    "message": f'Connected to room "{self.room_name}" as {self.user.email}',
                    "counter": current_counter,
                    "room": self.room_name,
                    "all_rooms": all_rooms,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        )

        # Notify all users about new user joining
        await self.channel_layer.group_send(
            self.global_group_name,
            {
                "type": "user_joined",
                "user": self.user.email,
                "room": self.room_name,
                "counter": current_counter,
                "all_rooms": all_rooms,
            },
        )

    async def _get_user(self, user_id: int) -> Optional[User]:
        # Overrides base for proper typing import of decorator
        @database_sync_to_async  # type: ignore[misc]
        def _sync() -> Optional[User]:
            try:
                return User.objects.get(id=user_id)
            except User.DoesNotExist:
                return None

        return await _sync()  # type: ignore[no-any-return]

    async def _get_room(self, room_name: str) -> Optional[RoomModel]:
        @database_sync_to_async  # type: ignore[misc]
        def _sync() -> Optional[RoomModel]:
            try:
                return RoomModel.objects.get(name=room_name)
            except RoomModel.DoesNotExist:
                return None

        return await _sync()  # type: ignore[no-any-return]

    async def _get_current_counter(self, room_name: str) -> int:
        @database_sync_to_async  # type: ignore[misc]
        def _sync() -> int:
            counter = PersonCounter.get_last(room_name)
            return counter.count if counter else 0

        return await _sync()  # type: ignore[no-any-return]

    async def _get_all_room_counters(self) -> Dict[str, int]:
        """Get current counters for all rooms"""

        @database_sync_to_async  # type: ignore[misc]
        def _sync() -> Dict[str, int]:
            result: Dict[str, int] = {}
            for room in RoomModel.objects.all():
                counter = PersonCounter.get_last(room.name)
                result[room.name] = counter.count if counter else 0
            return result

        return await _sync()  # type: ignore[no-any-return]

    async def _apply_delta(
        self, room: RoomModel, delta: int, updated_by: Optional[User] = None
    ) -> PersonCounter:
        @database_sync_to_async  # type: ignore[misc]
        def _sync() -> PersonCounter:
            return PersonCounter.add_delta(room, delta, updated_by=updated_by)

        return await _sync()  # type: ignore[no-any-return]

    async def _reset_counter(
        self, room: RoomModel, updated_by: Optional[User] = None
    ) -> PersonCounter:
        @database_sync_to_async  # type: ignore[misc]
        def _sync() -> PersonCounter:
            return PersonCounter.reset_to_zero(room, updated_by=updated_by)

        return await _sync()  # type: ignore[no-any-return]

    async def disconnect(self, close_code: int) -> None:
        # Leave both room group and global group
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )
        await self.channel_layer.group_discard(
            self.global_group_name, self.channel_name
        )

        # Notify all users about user leaving
        if hasattr(self, "user") and hasattr(self, "room_name"):
            current_counter: int = await self._get_current_counter(self.room_name)
            all_rooms: Dict[str, int] = await self._get_all_room_counters()

            await self.channel_layer.group_send(
                self.global_group_name,
                {
                    "type": "user_left",
                    "user": self.user.email,
                    "room": self.room_name,
                    "counter": current_counter,
                    "all_rooms": all_rooms,
                },
            )

    async def receive(
        self, text_data: Optional[str] = None, bytes_data: Optional[bytes] = None
    ) -> None:
        if text_data:
            try:
                text_data_json: Dict[str, Any] = json.loads(text_data)
                message_type: str = text_data_json.get("type", "unknown")

                if message_type == "increment":
                    # Increment counter using database
                    new_counter: PersonCounter = await self._apply_delta(
                        self.room, 1, self.user
                    )
                    all_rooms: Dict[str, int] = await self._get_all_room_counters()

                    await self.channel_layer.group_send(
                        self.global_group_name,
                        {
                            "type": "counter_update",
                            "action": "increment",
                            "room": self.room_name,
                            "counter": new_counter.count,
                            "delta": 1,
                            "user": self.user.email,
                            "all_rooms": all_rooms,
                        },
                    )

                elif message_type == "decrement":
                    # Decrement counter using database
                    new_counter = await self._apply_delta(self.room, -1, self.user)
                    all_rooms = await self._get_all_room_counters()

                    await self.channel_layer.group_send(
                        self.global_group_name,
                        {
                            "type": "counter_update",
                            "action": "decrement",
                            "room": self.room_name,
                            "counter": new_counter.count,
                            "delta": -1,
                            "user": self.user.email,
                            "all_rooms": all_rooms,
                        },
                    )

                elif message_type == "reset":
                    # Reset counter using database in a race-safe manner
                    new_counter = await self._reset_counter(self.room, self.user)
                    all_rooms = await self._get_all_room_counters()

                    await self.channel_layer.group_send(
                        self.global_group_name,
                        {
                            "type": "counter_update",
                            "action": "reset",
                            "room": self.room_name,
                            "counter": new_counter.count,
                            "delta": new_counter.delta,
                            "user": self.user.email,
                            "all_rooms": all_rooms,
                        },
                    )

                elif message_type == "get_counter":
                    # Get current counter value
                    current_counter = await self._get_current_counter(self.room_name)
                    all_rooms = await self._get_all_room_counters()

                    await self.send(
                        text_data=json.dumps(
                            {
                                "type": "counter_value",
                                "counter": current_counter,
                                "room": self.room_name,
                                "all_rooms": all_rooms,
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                    )

                elif message_type == "get_all_rooms":
                    # Get all room counters
                    all_rooms = await self._get_all_room_counters()

                    await self.send(
                        text_data=json.dumps(
                            {
                                "type": "all_rooms_update",
                                "all_rooms": all_rooms,
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                    )

                elif message_type == "ping":
                    # Respond to client heartbeat
                    await self.send(
                        text_data=json.dumps(
                            {
                                "type": "pong",
                                "timestamp": datetime.now().isoformat(),
                                "room": getattr(self, "room_name", None),
                            }
                        )
                    )

                else:
                    # Handle unknown message types
                    await self.send(
                        text_data=json.dumps(
                            {
                                "type": "error",
                                "message": f"Unknown message type: {message_type}",
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                    )

            except json.JSONDecodeError:
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "error",
                            "message": "Invalid JSON format",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                )

    # Handler for counter updates - now sent to all users
    async def counter_update(self, event: Dict[str, Any]) -> None:
        await self.send(
            text_data=json.dumps(
                {
                    "type": "counter_update",
                    "action": event["action"],
                    "room": event["room"],
                    "counter": event["counter"],
                    "delta": event.get("delta", 0),
                    "user": event["user"],
                    "all_rooms": event["all_rooms"],
                    "is_my_room": event["room"] == self.room_name,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        )

    # Handler for user joined - now sent to all users
    async def user_joined(self, event: Dict[str, Any]) -> None:
        if event["user"] != self.user.email:  # Don't send to the user who just joined
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "user_joined",
                        "message": f"{event['user']} joined room '{event['room']}'",
                        "room": event["room"],
                        "counter": event["counter"],
                        "all_rooms": event["all_rooms"],
                        "is_my_room": event["room"] == self.room_name,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            )

    # Handler for user left - now sent to all users
    async def user_left(self, event: Dict[str, Any]) -> None:
        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_left",
                    "message": f"{event['user']} left room '{event['room']}'",
                    "room": event["room"],
                    "counter": event["counter"],
                    "all_rooms": event["all_rooms"],
                    "is_my_room": event["room"] == self.room_name,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        )


# Keep the old PingConsumer for backward compatibility
class PingConsumer(AuthenticatedAsyncWebsocketConsumer):
    async def connect(self) -> None:
        self.parse_query_params()
        authed: bool = await self.authenticate_from_query(
            expected_token_type="websocket"
        )
        if not authed:
            return
        await self.accept()
        await self.send(
            text_data=json.dumps(
                {
                    "type": "connection",
                    "message": f"WebSocket connection established for {self.user.email}",
                    "timestamp": datetime.now().isoformat(),
                }
            )
        )

    async def receive(
        self, text_data: Optional[str] = None, bytes_data: Optional[bytes] = None
    ) -> None:
        if text_data:
            try:
                text_data_json: Dict[str, Any] = json.loads(text_data)
                message_type: str = text_data_json.get("type", "unknown")

                if message_type == "ping":
                    # Respond to ping with pong
                    await self.send(
                        text_data=json.dumps(
                            {
                                "type": "pong",
                                "message": "pong",
                                "timestamp": datetime.now().isoformat(),
                                "original_message": text_data_json.get("message", ""),
                            }
                        )
                    )

                elif message_type == "echo":
                    # Echo back any message
                    await self.send(
                        text_data=json.dumps(
                            {
                                "type": "echo_response",
                                "message": text_data_json.get("message", ""),
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                    )

                elif message_type == "heartbeat":
                    # Start a heartbeat every 10 seconds
                    await self.start_heartbeat()

                else:
                    # Handle unknown message types
                    await self.send(
                        text_data=json.dumps(
                            {
                                "type": "error",
                                "message": f"Unknown message type: {message_type}",
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                    )

            except json.JSONDecodeError:
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "error",
                            "message": "Invalid JSON format",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                )

    async def start_heartbeat(self) -> None:
        """Send periodic heartbeat messages"""
        asyncio.create_task(self.heartbeat_loop())

    async def heartbeat_loop(self) -> None:
        """Send heartbeat every 10 seconds"""
        while True:
            try:
                await asyncio.sleep(10)
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "heartbeat",
                            "message": "Server heartbeat",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                )
            except Exception:
                # Connection closed, stop heartbeat
                break
