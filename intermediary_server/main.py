import asyncio
import websockets

# Constants
INTERMEDIARY_SERVER_IP = "0.0.0.0"
INTERMEDIARY_SERVER_PORT = 1234

ssh_host_websocket = None
client_websocket = None


async def forward_to_ssh_host():
    global client_websocket

    while True:
        if ssh_host_websocket is None or client_websocket is None:
            await asyncio.sleep(0)
            continue
        try:
            data = await client_websocket.recv()
        except (
            websockets.exceptions.ConnectionClosedError,
            websockets.exceptions.ConnectionClosedOK,
        ):
            client_websocket = None
            await asyncio.sleep(0)
            break
        if not data:
            await asyncio.sleep(0)
            break
        await ssh_host_websocket.send(data)
        # print("Client -> SSH Host")
        await asyncio.sleep(0)


async def forward_to_client():
    global ssh_host_websocket

    while True:
        if ssh_host_websocket is None or client_websocket is None:
            await asyncio.sleep(0)
            continue
        try:
            data = await ssh_host_websocket.recv()
        except (
            websockets.exceptions.ConnectionClosedError,
            websockets.exceptions.ConnectionClosedOK,
        ):
            ssh_host_websocket = None
            await asyncio.sleep(0)
            break
        if not data:
            await asyncio.sleep(0)
            break
        await client_websocket.send(data)
        # print("SSH Host -> Client")
        await asyncio.sleep(0)


async def handle_client(websocket):
    global ssh_host_websocket, client_websocket

    if ssh_host_websocket is None:
        ssh_host_websocket = websocket
        print(
            f"SSH Host connected from {websocket.remote_address[0] + ':' + str(websocket.remote_address[1])}"
        )
        try:
            await websocket.wait_closed()
        finally:
            ssh_host_websocket = None
            if client_websocket is not None:
                await client_websocket.close()
                client_websocket = None
            print(
                f"SSH Host disconnected from {websocket.remote_address[0] + ':' + str(websocket.remote_address[1])}"
            )
    elif client_websocket is None:
        client_websocket = websocket
        print(
            f"Client connected from {websocket.remote_address[0] + ':' + str(websocket.remote_address[1])}"
        )
        try:
            await websocket.wait_closed()
        finally:
            client_websocket = None
            if ssh_host_websocket is not None:
                await ssh_host_websocket.close()
                ssh_host_websocket = None
            print(
                f"Client disconnected from {websocket.remote_address[0] + ':' + str(websocket.remote_address[1])}"
            )


async def main():
    print("Ready!\n")
    async with websockets.serve(
        handle_client, INTERMEDIARY_SERVER_IP, INTERMEDIARY_SERVER_PORT
    ):
        asyncio.ensure_future(forward_to_ssh_host())
        asyncio.ensure_future(forward_to_client())
        await asyncio.Future()


asyncio.run(main())
