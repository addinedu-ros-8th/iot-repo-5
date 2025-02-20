import sys
import os
import database
import struct
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal
import json
from PyQt5.QtNetwork import QTcpServer, QHostAddress, QTcpSocket

class Server(QTcpServer):
    def __init__(self):
        super(Server, self).__init__()

        self.client_list = {}
        self.port = 8888

    def incomingConnection(self, handle):
        client_socket = QTcpSocket(self)
        client_socket.setSocketDescriptor(handle)
        client_socket.readyRead.connect(lambda: self.receive_data(client_socket))
        client_socket.disconnected.connect(lambda: self.disconnected(client_socket))
        client_socket.errorOccurred.connect(lambda err: self.socketError(client_socket, err))

    def socketError(self, client_socket, err):
        if client_socket.state() == QTcpSocket.UnconnectedState:
            self.clientDisconnected(client_socket)

    def receive_data(self, client_socket):
        while client_socket.bytesAvailable():
            data = client_socket.readAll()
            data = bytes(data)
            print(f"Received data : {data}")
            
            command = data[:2].decode()
            if command == 'AA':
                self.client_list[1] = client_socket
                self.sendData(client_socket, struct.pack("<2sc", command.encode(), b'\n'))

    def disconnected(self, client_socket):
        print(f"client disconnected : {client_socket}")
        client_socket.deleteLater()
    
    def sendData(self, client_socket, message):
        print(message)
        client_socket.write(message)

def processCommand():
    while True:
        command = input()
        
        if command.strip().lower() == "exit":
            print("Server Close.")
            break
        elif command.strip() == "at":
            data = struct.pack("<2sc", "AT".encode(), b'\n')
            server.sendData(server.client_list[1], "CCZ\n".encode("utf-8"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    server = Server()

    if server.listen(QHostAddress.Any, server.port):
        print("Server listen on port", server.port)
    else:
        print("Failed listen on port", server.port)

    processCommand()

    server.close()
    app.quit()
    #sys.exit(app.exec_())