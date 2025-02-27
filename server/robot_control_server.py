import sys
import json
import struct
import time
import traceback
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5.QtCore import QCoreApplication, QTimer
from PyQt5.QtNetwork import QTcpServer, QHostAddress, QTcpSocket
from enum import Enum

class Client(Enum):
    ROBOT = 0
    VENDING_MACHINE = 1
    ORDER_SERVER = 3

class Server(QTcpServer):
    def __init__(self):
        super(Server, self).__init__()

        self.client_list = {}
        self.order_list = {}
        self.port = 8888
        self.group_id = -1

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
                    if status in self.client_list:
                        print("already")
                        del self.client_list[status]

                    self.client_list[status] = client_socket
                    if status == Client.ROBOT.value:
                        print("Robot Connection")
                        data = {"command":"LOG", "status":0x01, "type":"로봇", "message":"카트 로봇 연결"}
                        self.sendData(self.client_list[Client.ORDER_SERVER.value], data, 1)
                    elif status == Client.VENDING_MACHINE.value:
                        print("Vending Machine")
                        data = {"command":"LOG", "status":0x01, "type":"로봇", "message":"자판기 로봇 연결"}
                        self.sendData(self.client_list[Client.ORDER_SERVER.value], data, 1)
                    
                    time.sleep(1)
                    self.sendData(client_socket, struct.pack("<2sBc", command.encode(), 0x02, b'\n'))
                    return
                elif command == "TL":
                    if status == 0x00:
                        data = {"command":"TL", "status":0x00}
                        self.sendData(self.client_list[Client.ORDER_SERVER.value], data, 1)

                        data = {"command":"LOG", "status":0x01, "type":"로봇", "message":"카트 로봇 SECTION LIST 요청"}
                        self.sendData(self.client_list[Client.ORDER_SERVER.value], data, 1)
                        return
                    elif status == 0x03:
                        data = {"command":"LOG", "status":0x01, "type":"로봇", "message":"카트 로봇 SECTION LIST 수신 완료"}
                        self.sendData(self.client_list[Client.ORDER_SERVER.value], data, 1)
                        return
                elif command == "PC":
                    if status == 0x00:
                        section_id = int(data[3])
                        quantity = self.order_list[section_id]
                        
                        data = struct.pack("<2sBBBc", command.encode(), status, section_id, quantity, b'\n')
                        self.sendData(self.client_list[Client.VENDING_MACHINE.value], data)

                        data = {"command":"LOG", "status":0x01, "type":"로봇", "message":"카트 로봇 상품 적재 요청"}
                        self.sendData(self.client_list[Client.ORDER_SERVER.value], data, 1)
                        return
                    elif status == 0x01:
                        struct.pack("<2sBc", command.encode(), status, b'\n')
                        self.sendData(self.client_list[Client.ROBOT.value], data)

                        data = {"command":"LOG", "status":0x01, "type":"로봇", "message":"자판기 로봇 상품 적재 완료"}
                        self.sendData(self.client_list[Client.ORDER_SERVER.value], data, 1)
                        return
                    elif status == 0x02:
                        data = struct.pack("<2sBc", "MV".encode(), 0x00, b'\n')
                        self.sendData(self.client_list[Client.ROBOT.value], data)

                        data = {"command":"LOG", "status":0x01, "type":"로봇", "message":"카트 로봇 모든 상품 적재 완료"}
                        self.sendData(self.client_list[Client.ORDER_SERVER.value], data, 1)
                        return
                elif command == "MV":
                    if status == 0x01:
                        print("픽업 스테이션 도착")

                        data = {"command":"LOG", "status":0x01, "type":"로봇", "message":"카트 로봇 픽업 스테이션 도착"}
                        self.sendData(self.client_list[Client.ORDER_SERVER.value], data, 1)

                        data = {"command":"PU", "status":0x00, "group_id":self.group_id}
                        self.sendData(self.client_list[Client.ORDER_SERVER.value], data, 1)
                    elif status == 0x03:
                        data = {"command":"LOG", "status":0x01, "type":"로봇", "message":"카트 로봇 홈 스테이션 도착"}
                        self.sendData(self.client_list[Client.ORDER_SERVER.value], data, 1)
                        self.group_id = 0
            else:
                command = data["command"]
                status = data["status"]

                if command == "AT":
                    self.client_list[status] = client_socket
                    
                    data = {
                        "command" : "AT",
                        "status" : 0x02
                    }
                    self.sendData(client_socket, data, 1)

                    time.sleep(0.5)
                    data = {"command":"LOG", "status":0x01, "type":"로봇", "message":"주문 서버 연결"}
                    self.sendData(client_socket, data, 1)
                    return
                if command == "TL":
                    robot_socket = self.client_list[Client.ROBOT.value]
                    uids = [tuple(item) for item in data["data"]]
                    
                    for uid in uids:
                        data = struct.pack("<2sBBBBBc", command.encode(), status, *uid, b'\n')
                        self.sendData(robot_socket, data)
                        time.sleep(0.5)

                    data = struct.pack("<2sBc", command.encode(), 0x02, b'\n')
                    self.sendData(robot_socket, data)
                    #QTimer.singleShot(500, lambda:self.socketDelay(robot_socket, data))

                    data = {"command":"LOG", "status":0x01, "type":"로봇", "message":"카트 로봇에 SECTION LIST 전송"}
                    self.sendData(self.client_list[Client.ORDER_SERVER.value], data, 1)
                elif command == "OD":
                    status = data["status"]
                    if status == 0x00:
                        self.group_id = data["group_id"]
                        self.order_list = {}
                        for i in range(len(data["section_list"])):
                            self.order_list[data["section_list"][i]] = data["quantity_list"][i]

                        for section_id, quantity in self.order_list.items():
                            data = struct.pack("<2sBBc", command.encode(), status, section_id, b'\n')
                            print(data)
                            self.sendData(self.client_list[Client.ROBOT.value], data)
                            time.sleep(1)

                        data = struct.pack("<2sBc", command.encode(), 0x01, b'\n')
                        self.sendData(self.client_list[Client.ROBOT.value], data)

                        data = {"command":"LOG", "status":0x01, "type":"로봇", "message":"카트 로봇에 주문정보 전송"}
                        self.sendData(self.client_list[Client.ORDER_SERVER.value], data, 1)

    def socketDelay(self, socket, data, isOrder=0):
        self.sendData(socket, data, isOrder)

    def disconnected(self, client_socket):
        print(f"client disconnected : {client_socket}")
        client_socket.deleteLater()
    
    def sendData(self, client_socket, message, isOrder=0):
        if isOrder == 0:
            if client_socket.state() == QTcpSocket.ConnectedState:
                client_socket.write(message)
                #client_socket.flush()
                client_socket.waitForBytesWritten()
        else:
            if client_socket.state() == QTcpSocket.ConnectedState:
                client_socket.write(json.dumps(message, default=str).encode('utf-8'))
                #client_socket.flush()
                client_socket.waitForBytesWritten()
        
    def sendLog(self, socket, data):
        self.sendData(socket, data)

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
            count = command[2]
            tl_list = {(44, 90, 50, 3), (3,44, 58, 190, 2), (3, 231, 52, 2), (167, 35, 180, 2)}
            for i in range(int(count)):
                data = struct.pack("<2sBBBBBc", "TL".encode(), status, *tl_list[i], b'\n')

                server.sendData(server.client_list[0], data)

            data = struct.pack("<2sBc", "TL".encode(), 0x02, b'\n')
            QTimer.singleShot(500, lambda:server.socketDelay(server.client_list[0], data))
        elif command[:2] == "od":
            status = 0x00

            index_list = [1, 2]
            server.order_list[1] = 1
            server.order_list[2] = 1

            for index in index_list:
                data = struct.pack("<2sBBc", "OD".encode(), status, index, b'\n')
                server.sendData(server.client_list[0], data)
                time.sleep(0.5)

            #time.sleep(1)
            data = struct.pack("<2sBc", "OD".encode(), 0x01, b'\n')
            server.sendData(server.client_list[0], data)
        elif command[:2] == "c1":
            data = struct.pack("<2sBc", "PC".encode(), 0x01, b'\n')
            server.sendData(server.client_list[0], data)
        elif command[:2] == "c2":
            data = struct.pack("<2sBc", "PC".encode(), 0x02, b'\n')
            server.sendData(server.client_list[0], data)
        elif command[:2] == "mv":
            data = struct.pack("<2sBc", "MV".encode(), 0x00, b'\n')
            server.sendData(server.client_list[0], data)

def handle_exception(exc_type, exc_value, exc_traceback):
    #if issubclass(exc_type, KeyboardInterrupt):
    #    print("\n프로그램을 종료합니다.")
    #    sys.exit(0)
    print("예외가 발생했습니다:")
    traceback.print_exception(exc_type, exc_value, exc_traceback)

sys.excepthook = handle_exception

if __name__ == "__main__":
    app = QCoreApplication(sys.argv)
    server = Server()

    if server.listen(QHostAddress.Any, server.port):
        print("Robot Server listen on port", server.port)
    else:
        print("Failed listen on port", server.port)

    processCommand()

    

    server.close()
    app.quit()
    #sys.exit(app.exec_())
