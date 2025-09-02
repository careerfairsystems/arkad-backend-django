import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from datetime import datetime
from arkad.jwt_utils import jwt_decode
from user_models.models import User
from urllib.parse import parse_qs


class RoomCounterConsumer(AsyncWebsocketConsumer):
    # Class-level dictionary to store room counters
    room_counters = {}
    # Global group for all connected users
    global_group_name = 'global_counter_updates'

    async def connect(self):
        # Get token and room name from query parameters
        query_string = self.scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        self.room_name = query_params.get('room', ['default'])[0]
        self.room_group_name = f'counter_{self.room_name}'

        if not token:
            await self.close(code=4001)
            return

        try:
            # Validate WebSocket token
            jwt_data = jwt_decode(token)
            if jwt_data.get('token_type') != 'websocket':
                await self.close(code=4001)
                return

            user_id = jwt_data.get('user_id')
            if not user_id:
                await self.close(code=4001)
                return

            # Get user from database
            self.user = await self.get_user(user_id)
            if not self.user:
                await self.close(code=4001)
                return

        except Exception as e:
            await self.close(code=4001)
            return

        # Join both room-specific group and global group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.channel_layer.group_add(
            self.global_group_name,
            self.channel_name
        )

        await self.accept()

        # Initialize counter for room if it doesn't exist
        if self.room_name not in self.room_counters:
            self.room_counters[self.room_name] = 0

        # Send current counter value and connection message
        await self.send(text_data=json.dumps({
            'type': 'connection',
            'message': f'Connected to room "{self.room_name}" as {self.user.email}',
            'counter': self.room_counters[self.room_name],
            'room': self.room_name,
            'all_rooms': dict(self.room_counters),
            'timestamp': datetime.now().isoformat()
        }))

        # Notify all users about new user joining
        await self.channel_layer.group_send(
            self.global_group_name,
            {
                'type': 'user_joined',
                'user': self.user.email,
                'room': self.room_name,
                'counter': self.room_counters[self.room_name],
                'all_rooms': dict(self.room_counters)
            }
        )

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    async def disconnect(self, close_code):
        # Leave both room group and global group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        await self.channel_layer.group_discard(
            self.global_group_name,
            self.channel_name
        )

        # Notify all users about user leaving
        if hasattr(self, 'user') and hasattr(self, 'room_name'):
            await self.channel_layer.group_send(
                self.global_group_name,
                {
                    'type': 'user_left',
                    'user': self.user.email,
                    'room': self.room_name,
                    'counter': self.room_counters.get(self.room_name, 0),
                    'all_rooms': dict(self.room_counters)
                }
            )

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            try:
                text_data_json = json.loads(text_data)
                message_type = text_data_json.get('type', 'unknown')

                if message_type == 'increment':
                    # Increment counter
                    self.room_counters[self.room_name] += 1
                    await self.channel_layer.group_send(
                        self.global_group_name,
                        {
                            'type': 'counter_update',
                            'action': 'increment',
                            'room': self.room_name,
                            'counter': self.room_counters[self.room_name],
                            'user': self.user.email,
                            'all_rooms': dict(self.room_counters)
                        }
                    )

                elif message_type == 'decrement':
                    # Decrement counter
                    self.room_counters[self.room_name] -= 1
                    await self.channel_layer.group_send(
                        self.global_group_name,
                        {
                            'type': 'counter_update',
                            'action': 'decrement',
                            'room': self.room_name,
                            'counter': self.room_counters[self.room_name],
                            'user': self.user.email,
                            'all_rooms': dict(self.room_counters)
                        }
                    )

                elif message_type == 'reset':
                    # Reset counter
                    self.room_counters[self.room_name] = 0
                    await self.channel_layer.group_send(
                        self.global_group_name,
                        {
                            'type': 'counter_update',
                            'action': 'reset',
                            'room': self.room_name,
                            'counter': self.room_counters[self.room_name],
                            'user': self.user.email,
                            'all_rooms': dict(self.room_counters)
                        }
                    )

                elif message_type == 'get_counter':
                    # Get current counter value
                    await self.send(text_data=json.dumps({
                        'type': 'counter_value',
                        'counter': self.room_counters[self.room_name],
                        'room': self.room_name,
                        'all_rooms': dict(self.room_counters),
                        'timestamp': datetime.now().isoformat()
                    }))

                elif message_type == 'get_all_rooms':
                    # Get all room counters
                    await self.send(text_data=json.dumps({
                        'type': 'all_rooms_update',
                        'all_rooms': dict(self.room_counters),
                        'timestamp': datetime.now().isoformat()
                    }))

                else:
                    # Handle unknown message types
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': f'Unknown message type: {message_type}',
                        'timestamp': datetime.now().isoformat()
                    }))

            except json.JSONDecodeError:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Invalid JSON format',
                    'timestamp': datetime.now().isoformat()
                }))

    # Handler for counter updates - now sent to all users
    async def counter_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'counter_update',
            'action': event['action'],
            'room': event['room'],
            'counter': event['counter'],
            'user': event['user'],
            'all_rooms': event['all_rooms'],
            'is_my_room': event['room'] == self.room_name,
            'timestamp': datetime.now().isoformat()
        }))

    # Handler for user joined - now sent to all users
    async def user_joined(self, event):
        if event['user'] != self.user.email:  # Don't send to the user who just joined
            await self.send(text_data=json.dumps({
                'type': 'user_joined',
                'message': f"{event['user']} joined room '{event['room']}'",
                'room': event['room'],
                'counter': event['counter'],
                'all_rooms': event['all_rooms'],
                'is_my_room': event['room'] == self.room_name,
                'timestamp': datetime.now().isoformat()
            }))

    # Handler for user left - now sent to all users
    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'message': f"{event['user']} left room '{event['room']}'",
            'room': event['room'],
            'counter': event['counter'],
            'all_rooms': event['all_rooms'],
            'is_my_room': event['room'] == self.room_name,
            'timestamp': datetime.now().isoformat()
        }))


# Keep the old PingConsumer for backward compatibility
class PingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get token from query parameters
        query_string = self.scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]

        if not token:
            await self.close(code=4001)
            return

        try:
            # Validate WebSocket token
            jwt_data = jwt_decode(token)
            if jwt_data.get('token_type') != 'websocket':
                await self.close(code=4001)
                return

            user_id = jwt_data.get('user_id')
            if not user_id:
                await self.close(code=4001)
                return

            # Get user from database
            self.user = await self.get_user(user_id)
            if not self.user:
                await self.close(code=4001)
                return

        except Exception as e:
            await self.close(code=4001)
            return

        await self.accept()
        await self.send(text_data=json.dumps({
            'type': 'connection',
            'message': f'WebSocket connection established for {self.user.email}',
            'timestamp': datetime.now().isoformat()
        }))

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            try:
                text_data_json = json.loads(text_data)
                message_type = text_data_json.get('type', 'unknown')

                if message_type == 'ping':
                    # Respond to ping with pong
                    await self.send(text_data=json.dumps({
                        'type': 'pong',
                        'message': 'pong',
                        'timestamp': datetime.now().isoformat(),
                        'original_message': text_data_json.get('message', '')
                    }))

                elif message_type == 'echo':
                    # Echo back any message
                    await self.send(text_data=json.dumps({
                        'type': 'echo_response',
                        'message': text_data_json.get('message', ''),
                        'timestamp': datetime.now().isoformat()
                    }))

                elif message_type == 'heartbeat':
                    # Start a heartbeat every 10 seconds
                    await self.start_heartbeat()

                else:
                    # Handle unknown message types
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': f'Unknown message type: {message_type}',
                        'timestamp': datetime.now().isoformat()
                    }))

            except json.JSONDecodeError:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Invalid JSON format',
                    'timestamp': datetime.now().isoformat()
                }))

    async def start_heartbeat(self):
        """Send periodic heartbeat messages"""
        asyncio.create_task(self.heartbeat_loop())

    async def heartbeat_loop(self):
        """Send heartbeat every 10 seconds"""
        while True:
            try:
                await asyncio.sleep(10)
                await self.send(text_data=json.dumps({
                    'type': 'heartbeat',
                    'message': 'Server heartbeat',
                    'timestamp': datetime.now().isoformat()
                }))
            except Exception:
                # Connection closed, stop heartbeat
                break
