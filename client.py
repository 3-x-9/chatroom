import os
import threading
import socket
import argparse
import sys
import tkinter
from tkinter import *

class Send(threading.Thread):
    def __init__(self, sock, name):
        super().__init__()
        self.sock = sock
        self.name = name

    def run(self):
        # listening for input

        while True:
            print("{}: ".format(self.name), end="")
            sys.stdout.flush()
            message = sys.stdin.readline()[:-1]

            # QUIT to quit the chat room
            # TODO make a gui element

            if message == "QUIT":
                self.sock.sendall("Server: {} has left the server".format(self.name).encode('ascii'))
                break

            else:
                self.sock.sendall("{}: {}".format(self.name, message).encode('ascii'))

            print("\nQUITING")
            self.sock.close()
            os._exit(0)


class Recieve(threading.Thread):
    def __init__(self, sock, name):
        super().__init__()
        self.sock = sock
        self.name = name
        self.messages = None

    def run(self):
        while True:
            message = self.sock.recv(1024).decode('ascii')

            if message:
                if self.messages:
                    self.messages.insert(tkinter.END, message)
                    print("hi")
                    print("\r{}\n{}:".format(message, self.name), end="")

                else:
                    print("\r{}\n{}:".format(message, self.name), end="")
            else:
                print("\n NO. We have lost connection to the server!")
                print("\nQUITTING")
                self.sock.close()
                os._exit(0)


class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.name = None
        self.messages = None

    def start(self):
        print("Trying to connect to {}:{}".format(self.host, self.port))

        self.sock.connect((self.host, self.port))
        print("Succesfully conected to {}:{}".format(self.host, self.port))

        print()
        self.name = input("Your Name: ")
        print()
        print("Welcome, {} getting ready to send and recieve messages...".format(self.name))

        send = Send(self.sock, self.name)

        recieve = Recieve(self.sock, self.name)

        send.start()
        recieve.start()

        self.sock.sendall("Server: {} has joined the chat. Say HI!".format(self.name).encode('ascii'))
        print("\rReady! Leave anytime by typing: QUIT")
        print("{}: ".format(self.name), end="")

        return recieve

    def send(self, text_input):
        message = text_input.get()
        text_input.delete(0, tkinter.END)
        self.messages.insert(tkinter.END, "{}: {}".format(self.name, message))

        if message == "QUIT":
            self.sock.sendall("Server: {} has left the chat!".format(self.name).encode('ascii'))
            print("\nQUITTING")
            self.sock.close()
            os._exit(0)


        else:

            self.sock.sendall("{}: {}".format(self.name, message).encode('ascii'))


def main(host, port):
    # run gui
    client = Client(host, port)
    recieve = client.start()

    window = Tk()
    window.title("Chatroom prototype.1")

    from_message = Frame(master=window)
    scroll_bar = Scrollbar(master=from_message)
    messages = Listbox(master=from_message, yscrollcommand=scroll_bar.set)
    scroll_bar.pack(side=RIGHT, fill=Y, expand=False)
    from_message.pack(side=LEFT, fill=BOTH, expand=True)
    messages.pack(side=LEFT, fill=BOTH, expand=True)

    client.messages = messages
    recieve.messages = messages
    from_message.grid(row=0, column=0, columnspan=2, sticky="nsew")
    from_entry = Frame(master=window)
    text_input = Entry(master=from_entry)

    text_input.pack(fill=BOTH, expand=True)
    text_input.bind("<Return>", lambda x:client.send(text_input))
    text_input.insert(0, "Your message here: ")

    send_button = Button(master=window, text="SEND", command=lambda: client.send(text_input))

    from_entry.grid(row=1, column=0, padx=10, sticky="ew")
    send_button.grid(row=1, column=1, pady=10, sticky="ew")

    window.rowconfigure(0, minsize=500, weight=1)
    window.rowconfigure(1, minsize=50, weight=0)
    window.columnconfigure(0, minsize=500, weight=1)
    window.columnconfigure(1, minsize=200, weight=0)

    window.mainloop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Chatroom Server")
    parser.add_argument('host', help="Server listening INtreface")
    parser.add_argument('-p', metavar='PORT', type=int, default=1060, help="TCP port default(1060)")

    args = parser.parse_args()

    main(args.host, args.p)