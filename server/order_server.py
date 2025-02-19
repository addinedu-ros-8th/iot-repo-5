import sys
import os
import database
import json
from PyQt5.QtCore import pyqtSignal, QCoreApplication
from PyQt5.QtNetwork import QTcpServer, QHostAddress, QTcpSocket

class Server(QTcpServer):
    client_list = {}
    port = 8889
    receive_data = pyqtSignal(QTcpSocket, dict)

    def __init__(self):
        super(Server, self).__init__()

    def incomingConnection(self, handle):
        client_socket = QTcpSocket(self)
        client_socket.setSocketDescriptor(handle)
        client_socket.readyRead.connect(lambda: self.receiveData(client_socket))
        client_socket.disconnected.connect(lambda: self.disconnected(client_socket))
        client_socket.errorOccurred.connect(lambda err: self.socketError(client_socket, err))

        print(f"Client Connected : {client_socket}")

    def socketError(self, client_socket, err):
        if client_socket.state() == QTcpSocket.UnconnectedState:
            self.clientDisconnected(client_socket)

    def receiveData(self, client_socket):
        while client_socket.bytesAvailable():
            receiveData = client_socket.readAll().data().decode("utf-8")
            print(f"Received data : {receiveData}")

            self.receive_data.emit(client_socket, json.loads(receiveData))

    def disconnected(self, client_socket):
        print(f"client disconnected : {client_socket}")
        client_socket.deleteLater()
    
    def sendData(self, client_socket, message):
        data = json.dumps(message, default=str)
        client_socket.write(data.encode("utf-8"))


def processInput():
    while True:
        command = input()
        
        if command.strip().lower() == "exit":
            print("Server Close.")
            break

def processCommand(socket, data):
    command = data["command"]
    
    if command == "LI":
        result = loginQuery(data["id"], data["pw"])
        
        data = {"command":"LIOK"}
        data.update(result)
        
        server.sendData(socket, data)
    elif command == "LO":
        logoutQuery(data['id'])
    elif command == "IN":
        result = productListQuery()

        data = {"command":"INOK"}
        data.update(result)

        server.sendData(socket, data)
    elif command == "OD":
        print()

def logoutQuery(id):
        sql = "update user set status = 0 where login_id = '" + id + "'"
        conn.execute_query(sql)

def productListQuery():
    sql = "select * from products"

    result = conn.fetch_all(sql)

    return {"data":result}

def loginQuery(id, pw):
    sql = "select status, id, name from user where login_id = '" + id + "' and password = '" + pw + "'"
    result = conn.fetch_one(sql)
    print(result)
    if result:
        status = result[0]
        if status == 1:
            return {"state":-1}
                    
        sql = "update user set status = 1 where login_id = '" + id + "'"
        conn.execute_query(sql)

        return {"state":1, "id":result[1], "name":result[2]}
    else:
        return {"state":0}

conn = None

if __name__ == "__main__":
    app = QCoreApplication(sys.argv)
    server = Server()

    conn = database.pickup_database(
        "addinedu.synology.me",
        "pickup",
        "Addinedu5!",
        "pickup"
    )

    if server.listen(QHostAddress.Any, server.port):
        print("Server listen on port", server.port)
    else:
        print("Failed listen on port", server.port)

    server.receive_data.connect(processCommand)

    processInput()

    server.close()
    app.quit()
    #sys.exit(app.exec_())