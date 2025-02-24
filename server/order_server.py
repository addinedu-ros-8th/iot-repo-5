import sys
import struct
import database
import json
from PyQt5.QtCore import pyqtSignal, QCoreApplication, QThread
from PyQt5.QtNetwork import QTcpServer, QHostAddress, QTcpSocket

class Client(QTcpSocket):
    receive_data = pyqtSignal(dict)

    def __init__(self):
        super(Client, self).__init__()

        self.connected.connect(self.on_connected)
        self.readyRead.connect(self.receiveData)

    def on_connected(self):
        data = {"command" : "AT", "status" : 0x03}
        self.sendData(data)

    def receiveData(self):
        while self.bytesAvailable() > 0:
            data = self.readAll().data().decode('utf-8')

            self.receive_data.emit(json.loads(data))

    def sendData(self, message):
        if self.state() == QTcpSocket.ConnectedState:
            data = json.dumps(message, default=str)
            self.write(data.encode('utf-8'))
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

            try:
                self.receive_data.emit(client_socket, json.loads(receiveData))
            except:
                self.sendData(client_socket, {"command":"ER"})

    def disconnected(self, client_socket):
        print(f"client disconnected : {client_socket}")
        client_socket.deleteLater()
    
    def sendData(self, client_socket, message):
        data = json.dumps(message, default=str)
        client_socket.write(data.encode("utf-8"))

class OrderStatusChecker(QThread):
    thread_data = pyqtSignal(dict)

    def __init__(self, db_conn):
        super().__init__()
        self.db_conn = db_conn
        self.running = True

    def run(self):
        while self.running:
            self.check_order_status()
            self.msleep(5000)  # 5초마다 체크

    def check_order_status(self):
        try:
            sql = """
            select o.user_id, o.order_group_id, g.status, o.product_id, p.section_id 
            from `order` o, order_group g, products p
            where o.order_group_id = g.id and g.status = 0 and p.id = o.product_id
            """
            result = conn.fetch_one(sql)
            if result is not None:
                data = {
                    "user_id" : result[0],
                    "group_id" : result[1],
                    "section_id" : result[4]
                }
                self.thread_data.emit(data)
                self.running = False
        except Exception as e:
            print(f"Error checking order status: {e}")

    def stop(self):
        self.running = False

def sendOrderList(data):
    user_id = data["user_id"]
    group_id = data["group_id"]
    section_id = data["section_id"]


def processCommand(socket, data):
    command = data["command"]
    
    if command == "LI":
        status = 0x00
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

        return
    elif command == "LO":
        logoutQuery(data['id'])

        return
    elif command == "AP":
        if data["status"] == 0x00:
            name = data["name"]
            price = data["price"]
            category = data["category"]
            quantity = data["quantity"]
            uid = data["uid"]

            status = addNewProduct(name, category, price, quantity, uid)

            data = {"command" : "AP", "status" : status}
            server.sendData(socket, data)
    elif command == "REG":
        if data["status"] == 0x00:
            name = data["name"]
            id = data["id"]
            pw = data["pw"]

            status = registAccount(name, id, pw)

            data = {
                "command" : "REG",
                "status" : status
            }
            server.sendData(socket, data)
    elif command == "IN":
        status = 0x00
        try:
            result = productListQuery()

            status = 0x01
        except:
            # 로그 작성 로직 추가해야됨
            pass

        data = {
            "command" : "IN",
            "status" : status,
            "data" : result
        }

        server.sendData(socket, data)

        return
    elif command == "SC":
        status = data["status"]

        if status == 0x00:
            # 장바구니 목록 요청청
            user_id = data["user_id"]
            product_id = data["product_id"]
            quantity = data["quantity"]

            status = addShoppingCartQuery(user_id, product_id, quantity)

            data = {
                "command" : "SC",
                "status" : status,
            }
            server.sendData(socket, data)

            return
        elif status == 0x03:
            # 장바구니 목록 요청
            user_id = data["user_id"]
            
            result = getShoppingCartQuery(user_id)
            
            data = {"command" : "SC"}
            data.update(result)

            server.sendData(socket, data)

            return
        elif status == 0x05:
            # 장바구니 상품 수량 수정
            #user_id = data["user_id"]
            cart_id = data["cart_id"]
            quantity = data["quantity"]

            status = modifyShoppingCartQuery(cart_id, quantity)

            data = {
                "command" : "SC",
                "status" : status
            }

            server.sendData(socket, data)

            return
        elif status == 0x06:
            # 장바구니 상품 삭제
            user_id = data["user_id"]
            cart_id = data["cart_id"]

            status = delShoppingCartQuery(user_id, cart_id)

            data = {
                "command" : "SC",
                "status" : status
            }
            server.sendData(socket, data)

            return
    elif command == "CO":
        status = data["status"]

        if status == 0x00:
            cart_id = data["cart_id"]
            user_id = data["user_id"]

            status = checkoutQuery(cart_id, user_id)

            data = {
                "command" : "CO",
                "status" : status
            }
            server.sendData(socket, data)
            
            
            if not order_status_checker.isRunning():
                order_status_checker.start()
                
            
            return
    elif command == "OL":
        status = data["status"]

        if status == 0x00:
            user_id = data["user_id"]

            result = orderListQuery(user_id)

            data = {"command" : "OL"}
            data.update(result)
            server.sendData(socket, data)

            return
        
def registAccount(name, id, pw):
    try:
        sql = "select * from user where login_id = %s"
        result = conn.fetch_one(sql, (id,))

        print(result)

        if result:
            return 0x02
        else:
            sql = "insert into user(name, login_id, password) values(%s, %s, sha2(%s, 256))"
            conn.execute_query(sql, (name, id, pw))

            conn.commit()
    except:
        conn.rollback()
        return 0x03
    
    return 0x01

def addNewProduct(name, category, price, quantity, uid):
    try:
        sql = "insert into products(name, category, quantity, price) values(%s, %s, %s, %s)"
        row_id = conn.execute_query(sql, (name, category, quantity, price))

        sql = "insert into section(product_id, uid) values(%s, %s)"
        conn.execute_query(sql,(row_id, uid))

        conn.commit()
    except:
        conn.rollback()
        return 0x02
    
    return 0x01

def orderListQuery(user_id=None):
    try:
        sql = """
        select p.name, o.quantity, p.price, g.status, g.date, u.name, o.id from 
        `order` o, products p, order_group g, user u
        where p.id = o.product_id
        and g.id = o.order_group_id and o.user_id and u.id
        """
        if user_id is not None:
            sql += " and g.user = %s"
            result = conn.fetch_all(sql, (user_id, ))
        else:
            result = conn.fetch_all(sql)

        status = 0x00
    except:
        return {"status":0x07}

    return {"data":result, "status":status}

def checkoutQuery(cart_id, user_id):
    try:
        sql = "insert into order_group(user_id) values(%s)"
        group_id = conn.execute_query(sql, (user_id, ))

        for i in cart_id:
            sql = """
            INSERT INTO `order`(user_id, order_group_id, product_id, quantity) 
            SELECT s.user_id, %s, s.product_id, s.quantity 
            FROM shopping_cart s
            WHERE s.id = %s
            """
            conn.execute_query(sql, (group_id, i))

        sql = "delete from shopping_cart where id in (%s)"
        placeholders = ', '.join(['%s'] * len(cart_id))  # 필요한 Placeholder를 준비
        sql = sql % placeholders  # 경로 맞춰 인자 삽입
        conn.execute_many(sql, (cart_id,))

        conn.commit()
    except Exception as e:
        print("SQL ERROR :", e)
        conn.rollback()
        return 0x04
    
    return 0x02

def modifyShoppingCartQuery(cart_id, quantity):
    try:
        sql = "update shopping_cart set quantity = %s where id = %s"
        conn.execute_query(sql, (quantity, cart_id))

        conn.commit()
    except:
        conn.rollback()
        return 0x07
    
    return 0x05

def delShoppingCartQuery(user_id, cart_id):
    try:
        sql = "delete from shopping_cart where id = %s and user_id = %s"
        conn.execute_query(sql, (cart_id, user_id))

        conn.commit()
    except:
        conn.rollback()
        return 0x07
    
    return 0x06

def getShoppingCartQuery(user_id):
    try:
        sql = """
        select s.id, p.name, s.quantity, p.price, p.quantity from 
        shopping_cart s, user u, products p
        where p.id = s.product_id and
        u.id = %s
        """
        result = conn.fetch_all(sql, (user_id, ))

        status = 0x03
    except:
        return {"status":0x07}

    return {"data":result, "status":status}

def addShoppingCartQuery(user_id, product_id, quantity):
    try:
        sql = "insert into shopping_cart(user_id, product_id, quantity) values (%s, %s, %s)"
        conn.execute_query(sql, (user_id, product_id, quantity))

        conn.commit()
    except:
        conn.rollback()
        return 0x07
    
    return 0x01

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
    sql = "select status, id, name from user where login_id = %s and password = sha2(%s, 256)"
    result = conn.fetch_one(sql, (id, pw))
    
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
    elif command == "TL":
        if data["status"] == 0x00:
            result = fetchSection()
            data = {"command":"TL", "status":0x01, "data":result}
            client.sendData(data)

def fetchSection():
    sql = "select uid from section"
    result = conn.fetch_all(sql)

    data = []
    for uid in result:
        hex = str(uid[0]).split("-")
        hex_value = [int(value, 16) for value in hex]

        data.append(hex_value)

    return data
        

if __name__ == "__main__":
    app = QCoreApplication(sys.argv)
    server = Server()

    client = Client()
    client.connectToHost(QHostAddress("192.168.0.2"), 8888)
    client.receive_data.connect(robotServerReceive)

    conn = database.pickup_database(
        "addinedu.synology.me",
        "pickup",
        "Addinedu5!",
        "pickup"
    )

    order_status_checker = OrderStatusChecker(conn)
    order_status_checker.thread_data.connect(sendOrderList)

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