import asyncio
import websockets
import socket


class Host:
    def __init__(
        self,
        intermediary_ip="intermediaryserver.darubyminer360.repl.co",
        path="",
        host_ip="localhost",
        host_port=23,
        use_wss=True,
        use_uvloop=True,
    ):
        self.intermediary_ip = intermediary_ip
        self.path = path
        self.host_ip = host_ip
        self.host_port = host_port
        self.use_wss = use_wss
        self.use_uvloop = use_uvloop

        self.host_websocket = None
        self.intermediary_server_websocket = None

    async def forward_to_host(self):
        while True:
            if self.host_websocket is None:
                if self.intermediary_server_websocket is not None:
                    await self.intermediary_server_websocket.close()
                    self.intermediary_server_websocket = None
                break
            if self.intermediary_server_websocket is None:
                if self.host_websocket is not None:
                    self.host_websocket.close()
                    self.host_websocket = None
                break
            try:
                data = await self.intermediary_server_websocket.recv()
            except (
                websockets.exceptions.ConnectionClosedError,
                websockets.exceptions.ConnectionClosedOK,
            ):
                self.intermediary_server_websocket = None
                self.host_websocket.close()
                self.host_websocket = None
                break
            if not data:
                break
            self.host_websocket.sendall(data)
            # print("Intermediary Server -> SSH Host")
            await asyncio.sleep(0)
        await asyncio.sleep(0)

    async def forward_to_intermediary_server(self):
        def _forward_to_intermediary_server():
            return self.host_websocket.recv(4096)

        while True:
            if self.host_websocket is None:
                if self.intermediary_server_websocket is not None:
                    await self.intermediary_server_websocket.close()
                    self.intermediary_server_websocket = None
                break
            if self.intermediary_server_websocket is None:
                if self.host_websocket is not None:
                    self.host_websocket.close()
                    self.host_websocket = None
                break
            data = await asyncio.get_running_loop().run_in_executor(
                None, _forward_to_intermediary_server
            )
            if not data:
                if self.intermediary_server_websocket is not None:
                    await self.intermediary_server_websocket.close()
                self.intermediary_server_websocket = None
                self.host_websocket = None
                break
            try:
                await self.intermediary_server_websocket.send(data)
            except (
                websockets.exceptions.ConnectionClosedError,
                websockets.exceptions.ConnectionClosedOK,
            ):
                self.intermediary_server_websocket = None
                self.host_websocket.close()
                self.host_websocket = None
                break
            # print("SSH Host -> Intermediary Server")
            await asyncio.sleep(0)
        await asyncio.sleep(0)

    async def main(self):
        print("Ready!\n")

        # Connect to the Host (ex. SSH Server)
        self.host_websocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host_websocket.connect((self.host_ip, self.host_port))

        print("Connected to SSH Server")

        # Connect to the Intermediary Server
        url = "ws"
        if self.use_wss:
            self.url += "s"
        url += "://" + self.intermediary_ip
        if not url.endswith("/"):
            url += "/"
        if self.path.startswith("/"):
            url += self.path[1:]
        else:
            url += self.path
        async with websockets.connect(url) as _intermediary_server_websocket:
            self.intermediary_server_websocket = _intermediary_server_websocket

            await asyncio.gather(
                self.forward_to_host(), self.forward_to_intermediary_server()
            )

        print("SSH Server disconnected")

    def run(self):
        if self.use_uvloop:
            import uvloop

            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

        asyncio.run(self.main())


if __name__ == "__main__":
    import sys

    host = Host()
    if len(sys.argv) > 1:
        host.intermediary_server_ip = sys.argv[1]
    if len(sys.argv) > 2:
        host.path = sys.argv[2]
    if len(sys.argv) > 3:
        host.host_ip = sys.argv[3]
    if len(sys.argv) > 4:
        host.host_port = sys.argv[4]
    if len(sys.argv) > 5:
        host.use_wss = bool(sys.argv[5])
    if len(sys.argv) > 6:
        host.use_uvloop = bool(sys.argv[6])
    host.run()
