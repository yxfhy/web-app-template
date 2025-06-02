import asyncio
import json

import websockets


async def handle_websocket(websocket, path):
    try:
        async for message in websocket:
            data = json.loads(message)
            if data["type"] == "ai_response":
                print(f"AI Response: {data['content']}")
    except websockets.exceptions.ConnectionClosed:
        pass


async def main():
    server = await websockets.serve(handle_websocket, "localhost", 8765)
    print("WebSocket server started on ws://localhost:8765")
    await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
