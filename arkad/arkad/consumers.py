import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from datetime import datetime


class PingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({
            'type': 'connection',
            'message': 'WebSocket connection established',
            'timestamp': datetime.now().isoformat()
        }))

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
