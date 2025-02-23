import sys
import json
import struct
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, QTimer
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

            try:
                data = json.loads(data)
                isOrder = True
            except:
                isOrder = False
            
            if not isOrder:
                command = data[:2].decode()
                status = data[2]
                if command == 'AT':
                    self.client_list[status] = client_socket
                    if status == 0:
                        print("Robot Connection")
                    elif status == 1:
                        print("Vending Machine")
                    elif status == 3:
                        print("Order Server")
                    
                    status = 0x02
                    self.sendData(client_socket, struct.pack("<2sBc", command.encode(), status, b'\n'))
                elif command == "TL":
                    if status == 0:
                        status = 0x01
                        uid = [(0xEB, 0xA0, 0xD8, 0x12), (0xC0, 0x11, 0x53, 0x0F)]
                        # UID를 반대로 저장해야됨
                        for item in uid:
                            self.sendData(client_socket, struct.pack("<2sBBBBBc", command.encode(), status, *item, b'\n'))
                        
                        data = struct.pack("<2sBc", command.encode(), 0x02, b'\n')
                        QTimer.singleShot(500, lambda:self.socketDelay(client_socket, data))
            else:
                print(data)
                command = data["command"]
                status = data["status"]

                if command == "AT":
                    self.client_list[status] = client_socket
                    
                    data = {
                        "command" : "AT",
                        "status" : 0x02
                    }
                    self.sendData(client_socket, data, 1)
                    

    def socketDelay(self, socket, data):
        self.sendData(socket, data)

    def disconnected(self, client_socket):
        print(f"client disconnected : {client_socket}")
        client_socket.deleteLater()
    
    def sendData(self, client_socket, message, isOrder=0):
        if isOrder == 0:
            if client_socket.state() == QTcpSocket.ConnectedState:
                client_socket.write(message)
                client_socket.flush()
        else:
            if client_socket.state() == QTcpSocket.ConnectedState:
                client_socket.write(json.dumps(message, default=str).encode('utf-8'))
                client_socket.flush()

def processCommand():
    while True:
        command = input()
        
        if command.strip().lower() == "q":
            print("Server Close.")
            break
        elif command[:2] == "pc":
            status = 0
            motor = int(command[2])
            quantity = int(command[3])
            data = struct.pack("<2sBBBc", "PC".encode(), status, motor, quantity, b'\n')
            server.sendData(server.client_list[1], data)
        elif command[:2] == "tl":
            status = 0x02
            data = struct.pack("<2sBc", "TL".encode(), status, b'\n')

            server.sendData(server.client_list[0], data)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    server = Server()

    if server.listen(QHostAddress.Any, server.port):
        print("Robot Server listen on port", server.port)
    else:
        print("Failed listen on port", server.port)

    processCommand()

    server.close()
    app.quit()
    #sys.exit(app.exec_())