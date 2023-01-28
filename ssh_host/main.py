import asyncio
import websockets
import socket

# Constants
INTERMEDIARY_IP = "intermediaryserver.darubyminer360.repl.co"

ssh_host = None
intermediary_server = None


async def forward_to_ssh_host():
    global ssh_host, intermediary_server

    while True:
        if ssh_host is None:
            if intermediary_server is not None:
                await intermediary_server.close()
                intermediary_server = None
            await asyncio.sleep(0)
            break
        if intermediary_server is None:
            if ssh_host is not None:
                ssh_host.close()
                ssh_host = None
            await asyncio.sleep(0)
            break
        try:
            data = await intermediary_server.recv()
            await asyncio.sleep(0)
        except (
            websockets.exceptions.ConnectionClosedError,
            websockets.exceptions.ConnectionClosedOK,
        ):
            intermediary_server = None
            ssh_host.close()
            ssh_host = None
            break
        if not data:
            await asyncio.sleep(0)
            break
        ssh_host.sendall(data)
        # print("Intermediary Server -> SSH Host")
        await asyncio.sleep(0)
    await asyncio.sleep(0)


async def forward_to_intermediary_server():
    global ssh_host, intermediary_server

    def _forward_to_intermediary_server():
        return ssh_host.recv(4096)

    while True:
        if ssh_host is None:
            if intermediary_server is not None:
                await intermediary_server.close()
                intermediary_server = None
            await asyncio.sleep(0)
            break
        if intermediary_server is None:
            if ssh_host is not None:
                ssh_host.close()
                ssh_host = None
            await asyncio.sleep(0)
            break
        data = await asyncio.get_running_loop().run_in_executor(
            None, _forward_to_intermediary_server
        )
        if not data:
            await intermediary_server.close()
            intermediary_server = None
            ssh_host = None
            await asyncio.sleep(0)
            break
        try:
            await intermediary_server.send(data)
            await asyncio.sleep(0)
        except (
            websockets.exceptions.ConnectionClosedError,
            websockets.exceptions.ConnectionClosedOK,
        ):
            intermediary_server = None
            ssh_host.close()
            ssh_host = None
            break
        # print("SSH Host -> Intermediary Server")
        await asyncio.sleep(0)
    await asyncio.sleep(0)


async def main():
    global ssh_host, intermediary_server

    print("Ready!\n")

    # Connect to the SSH Server
    ssh_host = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ssh_host.connect(("localhost", 23))

    print("Connected to SSH Server")

    # Connect to the Intermediary Server
    async with websockets.connect("wss://" + INTERMEDIARY_IP) as _intermediary_server:
        intermediary_server = _intermediary_server

        await asyncio.gather(forward_to_ssh_host(), forward_to_intermediary_server())

    print("SSH Server disconnected")


asyncio.run(main())
