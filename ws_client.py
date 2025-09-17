import asyncio
import websockets
import sys

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def chat():
    uri = "ws://localhost:5000"  # change if needed
    async with websockets.connect(uri) as websocket:
        print(f"Connected to {uri}")

        # run send + receive in parallel
        async def send_messages():
            while True:
                msg = await asyncio.get_event_loop().run_in_executor(None, input, "> ")
                await websocket.send(msg)

        async def receive_messages():
            async for message in websocket:
                print(f"\n< {message}")

        await asyncio.gather(send_messages(), receive_messages())


if __name__ == "__main__":
    asyncio.run(chat())
