import asyncio
import websockets
import socket

# Constants
INTERMEDIARY_IP = "intermediaryserver.darubyminer360.repl.co"
CLIENT_SERVER_IP = "0.0.0.0"
CLIENT_SERVER_PORT = 1234

client_socket = None
intermediary_server_websocket = None


async def forward_to_client():
    global client_socket, intermediary_server_websocket

    while True:
        if client_socket is None:
            if intermediary_server_websocket is not None:
                await intermediary_server_websocket.close()
                intermediary_server_websocket = None
            await asyncio.sleep(0)
            break
        if intermediary_server_websocket is None:
            if client_socket is not None:
                client_socket.close()
                client_socket = None
            await asyncio.sleep(0)
            break
        try:
            data = await intermediary_server_websocket.recv()
            await asyncio.sleep(0)
        except (
            websockets.exceptions.ConnectionClosedError,
            websockets.exceptions.ConnectionClosedOK,
        ):
            intermediary_server_websocket = None
            client_socket.close()
            client_socket = None
            break
        if not data:
            await asyncio.sleep(0)
            break
        client_socket.sendall(data)
        # print("Intermediary Server -> SSH Client")
        await asyncio.sleep(0)
    await asyncio.sleep(0)


async def forward_to_intermediary_server():
    global client_socket, intermediary_server_websocket

    def _forward_to_intermediary_server():
        return client_socket.recv(4096)

    while True:
        if client_socket is None:
            if intermediary_server_websocket is not None:
                await intermediary_server_websocket.close()
                intermediary_server_websocket = None
            await asyncio.sleep(0)
            break
        if intermediary_server_websocket is None:
            if client_socket is not None:
                client_socket.close()
                client_socket = None
            await asyncio.sleep(0)
            break
        data = await asyncio.get_running_loop().run_in_executor(
            None, _forward_to_intermediary_server
        )
        if not data:
            await intermediary_server_websocket.close()
            intermediary_server_websocket = None
            client_socket = None
            await asyncio.sleep(0)
            break
        try:
            await intermediary_server_websocket.send(data)
            await asyncio.sleep(0)
        except (
            websockets.exceptions.ConnectionClosedError,
            websockets.exceptions.ConnectionClosedOK,
        ):
            intermediary_server_websocket = None
            client_socket.close()
            client_socket = None
            break
        # print("SSH Client -> Intermediary Server")
        await asyncio.sleep(0)
    await asyncio.sleep(0)


async def main():
    global client_socket, intermediary_server_websocket

    # Create socket for the client server
    client_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the IP and port
    client_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client_server_socket.bind((CLIENT_SERVER_IP, CLIENT_SERVER_PORT))

    # Listen for incoming connections
    client_server_socket.listen()

    print("Ready!\n")

    # Wait for SSH to connect
    client_socket, client_address = client_server_socket.accept()

    print(f"SSH connected from {client_address}")

    # Connect to the Intermediary Server
    async with websockets.connect(
        "wss://" + INTERMEDIARY_IP
    ) as _intermediary_server_websocket:
        intermediary_server_websocket = _intermediary_server_websocket

        await asyncio.gather(forward_to_client(), forward_to_intermediary_server())

    print("SSH disconnected")


asyncio.run(main())
