from ..intermediary_info import result as intermediary_ip
import socket
import select

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((intermediary_ip.split(":")[0], int(intermediary_ip.split(":")[1])))

ssh_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ssh_sock.connect(("localhost", 23))

while True:
    # Use select to multiplex the connections
    rlist, _, _ = select.select([s, ssh_sock], [], [])
    for sock in rlist:
        # If data is received from the Intermediary Server, forward it to the SSH server
        if sock == s:
            data = sock.recv(4096)
            if not data:
                print("Intermediary Server connection closed")
                s.close()
                ssh_sock.close()
                exit()
            ssh_sock.sendall(data)
        # If data is received from the SSH server, forward it to the Intermediary Server
        else:
            data = sock.recv(4096)
            if not data:
                print("SSH Server connection closed")
                s.close()
                ssh_sock.close()
                exit()
            s.sendall(data)

# Close the connection
s.close()
ssh_sock.close()
