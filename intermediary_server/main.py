import socket
import select

# Constants
INTERMEDIARY_SERVER_IP = "0.0.0.0"
INTERMEDIARY_SERVER_PORT = 1234

# Create socket for the intermediary server
intermediary_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the IP and port
intermediary_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
intermediary_server_socket.bind((INTERMEDIARY_SERVER_IP, INTERMEDIARY_SERVER_PORT))

# Listen for incoming connections
intermediary_server_socket.listen()

print("Ready!\n\n")
while True:
    # Wait for the SSH host to connect
    ssh_host_socket, ssh_host_address = intermediary_server_socket.accept()
    print(f"SSH host connected from {ssh_host_address}")

    # Wait for a client to connect
    client_socket, client_address = intermediary_server_socket.accept()
    print(f"Client connected from {client_address}")

    # Keep track of the sockets that have data to be read
    inputs = [ssh_host_socket, client_socket]

    while inputs:
        # Wait for data to be available on any of the sockets
        readable, writable, exceptional = select.select(inputs, [], [])

        for s in readable:
            # Receive data from the socket
            data = s.recv(4096)
            if not data:
                # If the socket has closed, remove it from the list of inputs
                inputs.remove(s)
            else:
                # Send the data to the other socket
                if s == ssh_host_socket:
                    target = client_socket
                else:
                    target = ssh_host_socket
                target.sendall(data)

    # Close the sockets
    ssh_host_socket.close()
    client_socket.close()
    print("Client disconnected")
