import sys
import struct
import database
import json
from PyQt5.QtCore import pyqtSignal, QCoreApplication
from PyQt5.QtNetwork import QTcpServer, QHostAddress, QTcpSocket

class Client(QTcpSocket):
    receive_data = pyqtSignal(dict)

    def __init__(self):
        super(Client, self).__init__()

        self.connected.connect(self.on_connected)
        self.readyRead.connect(self.receiveData)

    def on_connected(self):
        #data = struct.pack("<2sBc", "AT".encode(), 0x03, b'\n')
        data = {
            "command" : "AT",
            "status" : 0x03
        }
        self.sendData(data)

    def receiveData(self):
        while self.bytesAvailable() > 0:
            data = self.readAll().data().decode('utf-8')

            self.receive_data.emit(json.loads(data))

    def sendData(self, message):
        if self.state() == QTcpSocket.ConnectedState:
            data = json.dumps(message, default=str)
            self.write(data.encode('utf-8'))
            #self.write(message)
            self.flush()

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

def processCommand(socket, data):
    command = data["command"]
    
    if command == "LI":
        status = 0
        login_id = data["login_id"]
        pw = data["pw"]
        try:
            result = loginQuery(login_id, pw)
        except:
            # 로그 작성 로직 추가해야됨
            pass
        
        data = {"command" : "LI"}
        data.update(result)
        
        server.sendData(socket, data)
    elif command == "LO":
        logoutQuery(data['id'])
        client.sendData({"command":"AC"})
    elif command == "IN":
        status = 0
        try:
            result = productListQuery()

            status = 1
        except:
            # 로그 작성 로직 추가해야됨
            pass

        data = {
            "command" : "IN",
            "status" : status,
            "data" : result
        }

        server.sendData(socket, data)
    elif command == "SC":
        status = data["status"]

        if status == 0:
            user_id = data["user_id"]
            product_id = data["product_id"]
            quantity = data["quantity"]

            status = 7

            try:
                result = addShoppingCartQuery(user_id, product_id, quantity)
                status = 1
            except:
                # 로그 작성 로직 추가해야됨
                pass

            data = {
                "command" : "SC",
                "status" : status,
                "data" : result
            }
            server.sendData(socket, data)
        elif status == 3: # 장바구니 목록 요청
            user_id = data["user_id"]
            status = 7

            try:
                result = getShoppingCartQuery(user_id)
                status = 4
            except:
                # 로그 작성 로직
                pass
            
            data = {
                "command" : "SC",
                "status" : status,
            }
            if status == 4:
                data.update(result)

            server.sendData(socket, data)
        elif status == 5: # 장바구니 상품 수량 수정
            user_id = data["user_id"]
            cart_id = data["cart_id"]

            try:
                status = modifyShoppingCartQuery(user_id, cart_id)
            except:
                status = 7

            data = {
                "command" : "SC",
                "status" : status
            }

            server.sendData(socket, data)
        elif status == 6: # 장바구니 상품 삭제
            user_id = data["user_id"]
            cart_id = data["cart_id"]

            try:
                status = delShoppingCartQuery(user_id, cart_id)
            except:
                status = 7

            data = {
                "command" : "SC",
                "status" : status
            }
            server.sendData(socket, data)

def modifyShoppingCartQuery(user_id, cart_id, quantity):
    sql = "update shopping_cart set quantity = %s where id = %s and user_id = %s"
    conn.execute_query(sql, (quantity, cart_id, user_id))

    return 5

def delShoppingCartQuery(user_id, cart_id):
    sql = "delete from shopping_cart where id = %s and user_id = %s"
    conn.execute_query(sql, (cart_id, user_id))

    return 6

def getShoppingCartQuery(user_id):
    sql = """
    select s.id, p.name, s.quantity, (p.price * s.quantity) from 
    shopping_cart s, user u, products p
    where p.id = s.product_id and
    u.id = %s
    """
    result = conn.fetch_all(sql, (user_id, ))

    return {"data":result}

def addShoppingCartQuery(user_id, product_id, quantity):

    sql = "insert into shopping_cart(user_id, product_id, quantity) values (%s, %s, %s)"
    conn.execute_query(sql, (user_id, product_id, quantity))

def logoutQuery(id=None):
        sql = "update user set status = 0"

        if id is not None:
            sql += " where login_id = '" + id + "'"
        
        conn.execute_query(sql)

def productListQuery():
    sql = "select * from products"

    result = conn.fetch_all(sql)

    return result

def loginQuery(id, pw):
    sql = "select status, id, name from user where login_id = '" + id + "' and password = '" + pw + "'"
    result = conn.fetch_one(sql)
    
    if result:
        status = result[0]
        if status == 1:
            return {"status":2}
                    
        sql = "update user set status = 1 where login_id = '" + id + "'"
        conn.execute_query(sql)

        return {"status":1, "user_id":result[1], "name":result[2]}
    else:
        return {"status":0}
    
def updateLog(self):
    sql = "select * from log"
    result = self.conn.fetch_all(sql)

def writeLog(self, type, message):
    sql = "insert into log(event_type, message) values(%s, %s)"
    self.conn.execute_query(sql, (type, message))

    self.updateLog()

def processInput():
    while True:
        command = input()
        
        if command.strip().lower() == "q":
            print("Server Close.")
            break

def robotServerReceive(data):
    command = data["command"]

    if command == "AT":
        if data["status"] == 0x02:
            print("Connect Robot Server")

conn = None

if __name__ == "__main__":
    app = QCoreApplication(sys.argv)
    server = Server()

    client = Client()
    client.connectToHost(QHostAddress("192.168.0.41"), 8888)
    client.receive_data.connect(robotServerReceive)

    conn = database.pickup_database(
        "addinedu.synology.me",
        "pickup",
        "Addinedu5!",
        "pickup"
    )

    if server.listen(QHostAddress.Any, server.port):
        print("Order Server listen on port", server.port)
    else:
        print("Failed listen on port", server.port)

    server.receive_data.connect(processCommand)

    logoutQuery()

    processInput()

    server.close()
    app.quit()
    #sys.exit(app.exec_())