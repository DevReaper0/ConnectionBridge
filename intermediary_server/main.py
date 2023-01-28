import asyncio
import websockets


class IntermediaryServer:
    def __init__(
        self,
        intermediary_server_ip="0.0.0.0",
        intermediary_server_port=1234,
        use_uvloop=True,
    ):
        self.intermediary_server_ip = intermediary_server_ip
        self.intermediary_server_port = intermediary_server_port
        self.use_uvloop = use_uvloop

        self.sockets = {}

    async def forward_to_ssh_host(self, path):
        while True:
            data = await self.sockets[path][1].recv()
            if not data:
                self.sockets.pop(path, None)
                break
            await self.sockets[path][0].send(data)
            # print("Client -> SSH Host")
            await asyncio.sleep(0)
        await asyncio.sleep(0)

    async def forward_to_client(self, path):
        while True:
            data = await self.sockets[path][0].recv()
            if not data:
                self.sockets.pop(path, None)
                break
            await self.sockets[path][1].send(data)
            # print("SSH Host -> Client")
            await asyncio.sleep(0)
        await asyncio.sleep(0)

    async def handle_client(self, websocket, path):
        if path not in self.sockets:
            self.sockets[path] = [None, None]
        if self.sockets[path][0] is None:
            self.sockets[path][0] = websocket
            print(
                f"SSH Host connected from {websocket.remote_address[0] + ':' + str(websocket.remote_address[1])}"
            )
            try:
                await websocket.wait_closed()
            finally:
                if path in self.sockets:
                    if self.sockets[path][1] is not None:
                        await self.sockets[path][1].close()
                    self.sockets.pop(path, None)
                print(
                    f"SSH Host disconnected from {websocket.remote_address[0] + ':' + str(websocket.remote_address[1])}"
                )
        elif self.sockets[path][1] is None:
            self.sockets[path][1] = websocket
            ssh_host_forwarder = asyncio.ensure_future(self.forward_to_ssh_host(path))
            client_forwarder = asyncio.ensure_future(self.forward_to_client(path))
            print(
                f"Client connected from {websocket.remote_address[0] + ':' + str(websocket.remote_address[1])}"
            )
            try:
                await websocket.wait_closed()
            finally:
                ssh_host_forwarder.cancel()
                client_forwarder.cancel()
                if path in self.sockets:
                    if self.sockets[path][0] is not None:
                        await self.sockets[path][0].close()
                    self.sockets.pop(path, None)
                print(
                    f"Client disconnected from {websocket.remote_address[0] + ':' + str(websocket.remote_address[1])}"
                )

    async def main(self):
        print("Ready!\n")
        async with websockets.serve(
            self.handle_client,
            self.intermediary_server_ip,
            self.intermediary_server_port,
        ):
            await asyncio.Future()

    def run(self):
        if self.use_uvloop:
            import uvloop

            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

        asyncio.run(self.main())


if __name__ == "__main__":
    import sys

    intermediary_server = IntermediaryServer()
    if len(sys.argv) > 1:
        intermediary_server.intermediary_server_port = sys.argv[1]
    if len(sys.argv) > 2:
        intermediary_server.use_uvloop = bool(sys.argv[2])
    intermediary_server.run()
