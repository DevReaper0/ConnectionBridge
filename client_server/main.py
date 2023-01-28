import asyncio
import websockets
import socket


class ClientServer:
    def __init__(
        self,
        intermediary_ip="intermediaryserver.darubyminer360.repl.co",
        path="",
        client_server_ip="0.0.0.0",
        client_server_port=1234,
        use_wss=True,
        use_uvloop=True,
    ):
        self.intermediary_ip = intermediary_ip
        self.path = path
        self.client_server_ip = client_server_ip
        self.client_server_port = client_server_port
        self.use_wss = use_wss
        self.use_uvloop = use_uvloop

        self.client_socket = None
        self.intermediary_server_websocket = None

    async def forward_to_client(self):
        while True:
            if self.client_socket is None:
                if self.intermediary_server_websocket is not None:
                    await self.intermediary_server_websocket.close()
                    self.intermediary_server_websocket = None
                break
            if self.intermediary_server_websocket is None:
                if self.client_socket is not None:
                    self.client_socket.close()
                    self.client_socket = None
                break
            try:
                data = await self.intermediary_server_websocket.recv()
            except (
                websockets.exceptions.ConnectionClosedError,
                websockets.exceptions.ConnectionClosedOK,
            ):
                self.intermediary_server_websocket = None
                self.client_socket.close()
                self.client_socket = None
                break
            if not data:
                break
            self.client_socket.sendall(data)
            # print("Intermediary Server -> SSH Client")
            await asyncio.sleep(0)
        await asyncio.sleep(0)

    async def forward_to_intermediary_server(self):
        def _forward_to_intermediary_server():
            return self.client_socket.recv(4096)

        while True:
            if self.client_socket is None:
                if self.intermediary_server_websocket is not None:
                    await self.intermediary_server_websocket.close()
                    self.intermediary_server_websocket = None
                break
            if self.intermediary_server_websocket is None:
                if self.client_socket is not None:
                    self.client_socket.close()
                    self.client_socket = None
                break
            data = await asyncio.get_running_loop().run_in_executor(
                None, _forward_to_intermediary_server
            )
            if not data:
                if self.intermediary_server_websocket is not None:
                    await self.intermediary_server_websocket.close()
                self.intermediary_server_websocket = None
                self.client_socket = None
                break
            try:
                await self.intermediary_server_websocket.send(data)
            except (
                websockets.exceptions.ConnectionClosedError,
                websockets.exceptions.ConnectionClosedOK,
            ):
                self.intermediary_server_websocket = None
                self.client_socket.close()
                self.client_socket = None
                break
            # print("SSH Client -> Intermediary Server")
            await asyncio.sleep(0)
        await asyncio.sleep(0)

    async def main(self):
        # Create socket for the client server
        self.client_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Bind the socket to the IP and port
        self.client_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client_server_socket.bind((self.client_server_ip, self.client_server_port))

        # Listen for incoming connections
        self.client_server_socket.listen()

        print("Ready!\n")

        # Wait for SSH to connect
        self.client_socket, client_address = self.client_server_socket.accept()

        print(f"SSH connected from {client_address}")

        # Connect to the Intermediary Server
        async with websockets.connect(
            "ws"
            + ("s" if self.use_wss else "")
            + "://"
            + self.intermediary_ip
            + "/"
            + self.path.replace("/", "")
        ) as _intermediary_server_websocket:
            self.intermediary_server_websocket = _intermediary_server_websocket

            await asyncio.gather(
                self.forward_to_client(), self.forward_to_intermediary_server()
            )

        print("SSH disconnected")

    def run(self):
        if self.use_uvloop:
            import uvloop

            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

        asyncio.run(self.main())


if __name__ == "__main__":
    import sys

    client_server = ClientServer()
    if len(sys.argv) > 1:
        client_server.intermediary_ip = sys.argv[1]
    if len(sys.argv) > 2:
        client_server.path = sys.argv[2]
    if len(sys.argv) > 3:
        client_server.client_server_ip = sys.argv[3]
    if len(sys.argv) > 4:
        client_server.client_server_port = sys.argv[4]
    if len(sys.argv) > 5:
        client_server.use_wss = bool(sys.argv[5])
    if len(sys.argv) > 6:
        client_server.use_uvloop = bool(sys.argv[6])
    client_server.run()
