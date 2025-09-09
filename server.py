import os
import threading
import socket
import argparse
import sys

class Server(threading.Thread):

    def __init__(self, host, port):
        super().__init__(daemon=True)
        self.connections = []
        self.host = host
        self.port = port

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))

        sock.listen()
        print("Listening at:", sock.getsockname())

        while True:
            # accpet new connection
            sc, sockname = sock.accept()
            print(f"accepting connection from {sc.getpeername()} to {sc.getsockname()}")

            # create a new thread
            server_socket = ServerSocket(sc, sockname, self)
            server_socket.start()

            # add thread to connection list
            self.connections.append(server_socket)
            print("established connection from:", sc.getpeername())


    def broadcast(self, message, source):
        # send to all except source
        for connection in self.connections:
            if connection != source:
                connection.send(message)

    def remove_connection(self, connection):
        self.connections.remove(connection)


class ServerSocket(threading.Thread):
    def __init__(self, sc, sockname, server):
        super().__init__(daemon=True)
        self.sc = sc
        self.sockname = sockname
        self.server = server

    def send(self, message):   # ✅ add this
        self.sc.sendall(message.encode('ascii'))

    def run(self):
        while True:
            message = self.sc.recv(1024).decode('ascii')

            if message:
                print(f"{self.sockname} says: {message}")
                self.server.broadcast(message, self)

            else:
                print(f"{self.sockname} has closed the connection")
                self.sc.close()
                self.server.connections.remove(self)
                return


def exit(server):
    while True:
        ipt = input("")
        if ipt == "close":
            print("closing all connections")
            for connection in server.connections:
                connection.sc.close()

            print("shutting down the server")
            sys.exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Chatroom Server")
    parser.add_argument('host', help="Server listening INtreface")
    parser.add_argument('-p', metavar='PORT', type=int, default=1060, help="TCP port default(1060)")

    args = parser.parse_args()

    # create server
    server = Server("0.0.0.0", 5000)
    server.start()

    exit = threading.Thread(target=exit, args=(server,))
    exit.start()