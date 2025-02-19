import sys
import os
import database
import threading
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal
import json
from PyQt5.QtNetwork import QTcpServer, QHostAddress, QTcpSocket

class Server(QTcpServer):
    client_list = {}
    port = 8888

    def __init__(self):
        super(Server, self).__init__()

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
            data = client_socket.readAll().data().decode("utf-8")
            print(f"Received data : {data}")
            if data[0] == "$":
                command, body = data[1:].split("+")
                if command == "AT":
                    self.client_list[body] = client_socket
                    #self.main.writeLog("연결", body + "번 기기 연결 성공")
                    print(body + "번 기기 연결 성공")
                    self.sendData(client_socket, "$ATOK+0")
                elif command == "":
                    pass

    def disconnected(self, client_socket):
        print(f"client disconnected : {client_socket}")
        client_socket.deleteLater()
    
    def sendData(self, client_socket, message):
        client_socket.write(message.encode("utf-8"))

def processCommand():
    while True:
        command = input()
        
        if command.strip().lower() == "exit":
            print("Server Close.")
            break

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