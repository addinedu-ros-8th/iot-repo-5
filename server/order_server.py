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

            try:
                data = json.loads(data, )
                print("Received Robot Data : ", data)
                self.receive_data.emit(data)
            except:
                # json 데이터가 아닐경우 패스
                pass

    def sendData(self, message):
        if self.state() == QTcpSocket.ConnectedState:
            data = json.dumps(message, default=str)
            self.write(data.encode('utf-8'))
            self.flush()

class Server(QTcpServer):
    port = 8889
    receive_data = pyqtSignal(QTcpSocket, dict)

    def __init__(self):
        self.client_list = {}
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

class RobotControlThread(QThread):
    thread_data = pyqtSignal(dict)

    def __init__(self, conn, socket):
        super().__init__()
        self.conn = conn
        self.socket = socket
        self.isMoving = False
        self.section_list = []
        self.product_list = []
        self.quantity_list = []

    def run(self):
        print("Robot Control Thread Start")
        self.running = True
        while self.running and not self.isMoving:
            self.check_order_status()
            self.msleep(5000)  # 5초마다 체크

    def check_order_status(self):
        try:
            sql = "select id from order_group where status = 0 limit 1"
            group_id = self.conn.fetch_one(sql)

            sql = """
            select o.user_id, o.order_group_id, o.product_id, s.id, o.quantity
            from `order` o, order_group g, products p, section s
            where o.order_group_id = %s and g.id = o.order_group_id and o.product_id = p.id and p.id = s.product_id
            """
            result = self.conn.fetch_all(sql, (group_id[0],))
            
            print(result)
            if result is not None:
                section_list = []
                product_list = []
                quantity_list = []
                for item in result:
                    product_list.append(item[2])
                    section_list.append(int(item[3]) - 1)
                    quantity_list.append(item[4])

                data = {
                    "user_id" : result[0][0],
                    "group_id" : result[0][1],
                    "section_list" : section_list,
                    "product_list" : product_list,
                    "quantity_list" : quantity_list
                }
                self.thread_data.emit(data)
                self.stop()
        except Exception as e:
            print(f"Error checking order status: {e}")

    def stop(self):
        print("Robot Control Thread Stop")
        self.running = False

def sendOrderList(data):
    user_id = data["user_id"]
    group_id = data["group_id"]
    section_list = data["section_list"]
    product_list = data["product_list"]
    quantity_list = data["quantity_list"]

    data = {
        "command" : "OD",
        "status" : 0x00,
        "group_id" : group_id,
        "section_list" : section_list,
        "quantity_list" : quantity_list
    }
    client.sendData(data)

    updateOrderStatus(group_id, 1)

    login_id = fetchUserID(group_id)
    for socket in server.client_list:
        if server.client_list[socket] == login_id[0]:
            if socket.state() == QTcpSocket.ConnectedState:
                result = orderListQuery(user_id)

                data = {"command" : "OL"}
                data.update(result)
                server.sendData(socket, data)
                break

def processCommand(socket, data):
    command = data["command"]
    
    if command == "LI":
        status = 0x00
        login_id = data["login_id"]
        pw = data["pw"]
        result = loginQuery(login_id, pw)

        if result["status"] == 1:
            server.client_list[socket] = login_id
        
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
            writeLog("상품", "새 상품 추가 : [" + name + "(" + category + "), " + str(quantity) + "개, " + str(price) + "원, " + uid + "]")
    elif command == "MP":
        status = data["status"]
        if status == 0x00:
            result = fetchProductName()
            data = {
                "command" : "MP",
                "status" : 0x00,
                "data" : result
            }
            server.sendData(socket, data)
        elif status == 0x01:
            uid = data["uid"]

            result = fetchProductInfo(uid)
            data = {
                "command" : "MP",
                "status" : 0x01,
                "data" : result
            }
            server.sendData(socket, data)
        elif status == 0x02:
            product_name = data["product_name"]
            product_id = data["product_id"]
            category = data["category"]
            price = data["price"]

            status = updateProductInfo(product_id, category, price)

            data = {
                "command" : "MP",
                "status" : status,
            }
            server.sendData(socket, data)
            writeLog("상품", "상품 수정 : [" + product_name + "(" + category + "), " + str(price) + "원]")
        elif status == 0x03:
            sql = "update products set quantity = %s where id = %s"
            conn.execute_query(sql, (data["quantity"], data["product_id"]))
            conn.commit()
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
            writeLog("회원", name + "(" + str(id) + ")님 신규 회원 가입")
    elif command == "IN":
        result = productListQuery()
        data = {
            "command" : "IN",
            "status" : 0x01,
            "data" : result
        }

        server.sendData(socket, data)
        return
    elif command == "SC":
        status = data["status"]

        if status == 0x00:
            # 장바구니 담기
            user_id = data["user_id"]
            product_id = data["product_id"]
            quantity = data["quantity"]

            status = addShoppingCartQuery(user_id, product_id, quantity)

            data = {
                "command" : "SC",
                "status" : status,
            }
            server.sendData(socket, data)
            writeLog("장바구니", "장바구니 추가(유저ID : " + str(user_id) + ", 상품ID : " + str(product_id) + ", 수량 : " + str(quantity) + ")")
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
            user_id = data["user_id"]
            cart_id = data["cart_id"]
            quantity = data["quantity"]

            status = modifyShoppingCartQuery(cart_id, quantity)

            data = {
                "command" : "SC",
                "status" : status
            }

            server.sendData(socket, data)
            writeLog("장바구니", "장바구니 수정(유저ID : " + str(user_id) + ", 카트ID : " + str(cart_id) + ", 수량 : " + str(quantity) + ")")
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
            writeLog("장바구니", "장바구니 상품 삭제(유저ID : + " + str(user_id) + ", 카트ID : " + str(cart_id)  + ")")
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

            writeLog("장바구니", "장바구니 결제(유저ID : " + str(user_id) + ", 카트ID : " + str(cart_id) + ")")
            
            if not robotThread.isRunning():
                robotThread.start()
            
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
        elif status == 0x01:
            flag = data["flag"]

            sql = """
            select p.name, o.quantity, p.price, g.status, g.date, g.id
                    from  `order` o, products p, order_group g, user u
                    where p.id = o.product_id
                    and g.id = o.order_group_id and u.id = o.user_id
                    order by g.id
            """
            if flag == 0:
                sql += " where g.status = 0"
            elif flag == 1:
                sql += " where g.status = 1"
            elif flag == 2:
                sql += " where g.status = 2"

            result = conn.fetch_all(sql)
            data = {"command":"OL", "status":0x00, "data":result}
            server.sendData(socket, data)
    elif command == "LOG":
        status = data["status"]
        if status == 0x00:
            result = fetchLog()

            data = {"command":"LOG","status":status,"data":result}
            server.sendData(socket, data)
        elif status == 0x01:
            log_type = data["type"]
            message = data["message"]

            writeLog(log_type, message)
    elif command == "PU":
        status = data["status"]

        if status == 0x01:
            group_id = data["group_id"]
            
            updateOrderStatus(group_id, 3)
            result = fetchUserID(group_id)

            server.sendData(socket, {"command":"PU", "status":0x01})
            writeLog("상품", str(result[0]) + "님 주문번호 " + str(result[1]) + "번 픽업 완료")
            client.sendData({"command":"PU", "status":0x01})
    elif command == "RS":
        status = data["status"]
        if status == 0x00:
            result = fetchRobot(1)

            print(result)
        elif status == 0x01:
            section = data["section"]
            status = data["status"]

            updateRobot(1, section, status)

def fetchRobot(id):
    sql = "select section, status from robot where id = %s"
    result = conn.fetch_one(sql, (id,))

    return result[0]

def updateRobot(id, section, status):
    try:
        sql = "update robot set section = %s, status = %s where id = %s"
        conn.execute_query(sql, section, status)

        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Error Update Robot Status :", e)

        return 0x07
    
    return 0x01
        
def updateProductInfo(product_id, category, price):
    try:
        sql = "update products set price = %s, category = %s where id = %s"
        conn.execute_query(sql, (price, category, product_id))

        conn.commit()
    except:
        return 0x03
    
    return 0x02
        
def fetchProductInfo(uid):
    sql = "select p.id, p.name, p.category, p.price from products p, section s where s.uid = %s and p.id = s.product_id"
    result = conn.fetch_one(sql, (uid,))

    return result

def fetchProductName():
    sql = "select uid from section"
    result = conn.fetch_all(sql)

    return result
        
def registAccount(name, id, pw):
    try:
        sql = "select * from user where login_id = %s"
        result = conn.fetch_one(sql, (id,))

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

def orderListQuery(user_id):
    try:
        sql = """
        select p.name, o.quantity, p.price, g.status, g.date, u.name, o.id, g.id
        from  `order` o, products p, order_group g, user u
        where p.id = o.product_id
        and g.id = o.order_group_id and u.id = o.user_id
        order by g.id
        """
        if user_id != 1:
            sql += " and u.id = %s"
            result = conn.fetch_all(sql, (user_id, ))
        else:
            sql += " and u.id = g.user_id"
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
            row = conn.execute_query(sql, (group_id, i))

            sql = """
            update products 
            set quantity = (select (p.quantity - o.quantity) 
                            from `order` o, products p
                            where o.product_id = p.id 
                            and o.id = %s) 
            where id = (select product_id from `order` where id = %s);
            """
            conn.execute_query(sql, (row, row))

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
        writeLog("로그인", id + " 로그아웃")
        
    conn.execute_query(sql)
    conn.commit()

def productListQuery():
    sql = "select * from products"

    result = conn.fetch_all(sql)

    return result

def loginQuery(id, pw):
    try:
        sql = "select status, id, name from user where login_id = %s and password = sha2(%s, 256)"
        result = conn.fetch_one(sql, (id, pw))
        
        if result:
            status = result[0]
            if status == 1:
                writeLog("로그인", id + " 이중 로그인 시도")
                return {"status":2}
                        
            sql = "update user set status = 1 where login_id = '" + id + "'"
            conn.execute_query(sql)
            conn.commit()

            writeLog("로그인", id + " 로그인 성공")
            return {"status":1, "user_id":result[1], "name":result[2]}
        else:
            writeLog("로그인", id + " 로그인 실패")
            return {"status":0}
    except Exception as e:
        conn.rollback()
        writeLog("로그인", "로그인 에러 : " + e)

    
def fetchLog():
    sql = "select * from log order by id desc limit 500"
    result = conn.fetch_all(sql)

    return result

def writeLog(type, message):
    try:
        sql = "insert into log(event_type, message) values(%s, %s)"
        conn.execute_query(sql, (type, message))

        conn.commit()
    except Exception as e:
        conn.rollback()
        print("write log failed...", e)

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
    elif command == "PU":
        status = data["status"]

        if status == 0x00:
            group_id = data["group_id"]
            result = fetchUserID(group_id)

            updateOrderStatus(group_id, 2)
            try:
                sendPickupRequest(result[0])

                writeLog("상품", str(result[0]) + "님 주문번호 " + str(result[1]) + "번  픽업 요청청")
            except Exception as ex:
                pass
    elif command == "MV":
        if data["status"] == 0x03:
            if not robotThread.isRunning():
                #robotThread.isRunning = True
                robotThread.start()

    elif command == "LOG":
        status = data["status"]
        if status == 0x01:
            log_type = data["type"]
            message = data["message"]

            writeLog(log_type, message)

def sendPickupRequest(login_id):
    for socket in server.client_list:
        if server.client_list[socket] == login_id:
            if socket.state() == QTcpSocket.ConnectedState:
                server.sendData(socket, {"command":"PU", "status":0x00})
                break

def fetchUserID(group_id): 
    try:
        sql = """
        select u.login_id, o.id
        from order_group g, `order` o, user u 
        where g.id = %s 
        and g.user_id = u.id 
        and g.id = o.order_group_id
        """
        result = conn.fetch_one(sql, (group_id,))
    except Exception as e:
        print("Error Fetch User ID :", e)

    return result

def updateOrderStatus(group_id, status):
    try:
        sql = "update order_group set status = %s where id = %s"
        conn.execute_query(sql, (status, group_id))

        conn.commit()
    except:
        conn.rollback()

def fetchSection():
    sql = "select uid from section"
    result = conn.fetch_all(sql)

    data = []
    for uid in result:
        hex = str(uid[0]).split("-")
        hex_value = [int(value, 16) for value in hex]

        data.append(hex_value)

    return data

def test():
    sql = "delete from `order`"
    conn.execute_query(sql)

    sql = "delete from order_group"
    conn.execute_query(sql)

    conn.commit()
        
process_group_id = -1

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

    robotThread = RobotControlThread(conn, client)
    robotThread.thread_data.connect(sendOrderList)

    if server.listen(QHostAddress.Any, server.port):
        print("Order Server listen on port", server.port)
    else:
        print("Failed listen on port", server.port)

    server.receive_data.connect(processCommand)

    logoutQuery()

    processInput()

    test()

    server.close()
    app.quit()
    #sys.exit(app.exec_())