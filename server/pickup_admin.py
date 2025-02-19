import sys
import os
import database
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal
import json
from PyQt5.QtNetwork import QTcpServer, QHostAddress, QAbstractSocket, QTcpSocket

path = os.path.join(os.path.dirname(__file__), 'pickup_admin.ui') 
from_class = uic.loadUiType(path)[0]

class Server(QTcpServer):    
    def __init__(self, main):
        super(Server, self).__init__()

        self.client_list = {}
        self.main = main

    def incomingConnection(self, handle):
        client_socket = QTcpSocket(self)
        client_socket.setSocketDescriptor(handle)
        client_socket.readyRead.connect(lambda: self.receive_data(client_socket))
        client_socket.disconnected.connect(lambda: self.disconnected(client_socket))
        client_socket.errorOccurred.connect(lambda err: self.socketError(client_socket, err))
            
        print(f"client connected : {client_socket}")

    def socketError(self, client_socket, err):
        print("error", err)
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

class OrderServer(QTcpServer):
    receive_order_data = pyqtSignal(QTcpSocket, str)

    def __init__(self, main):
        super(OrderServer, self).__init__()

        self.main = main
        self.client_list = {}

    def incomingConnection(self, handle):
        client_socket = QTcpSocket(self)
        client_socket.setSocketDescriptor(handle)
        client_socket.readyRead.connect(lambda: self.receiveData(client_socket))
        client_socket.disconnected.connect(lambda: self.disconnected(client_socket))

        print("client connected :", client_socket)

    def receiveData(self, client_socket):
        while client_socket.bytesAvailable():
            receiveData = client_socket.readAll().data().decode("utf-8").split("$")
            print(f"Received data : {receiveData}")

            for realData in receiveData:
                if realData != "":
                        command, body = realData.split("+")
                        
                        if command == "LI":
                            body = body.split("/")
                            id, pw = body[0], body[1]
                            state = self.main.loginQuery(id, pw)
                            
                            if state[0] == -1:
                                data = "$LIOK+-1"
                            elif state[0] == 0:
                                data = "$LIOK+0"
                            elif state[0] == 1:
                                data = "$LIOK+"
                                
                                for item in state:
                                    data += str(item) + "/"
                                data = data[:-1]

                            self.sendData(client_socket, data)
                        elif command == "IN":
                            list = self.main.productListQuery()
                            
                            for items in list:
                                data = "$INOK+"
                                for item in items:
                                    data += str(item) + ","
                                data = data[:-1]
                                self.sendData(client_socket, data)
                        elif command == "LO":
                            self.main.logout(body)
                        elif command == "OD":
                            body = body.split("/")

                            print(body)
            

    def disconnected(self, client_socket):
        print(f"client disconnected : {client_socket}")
        client_socket.deleteLater()

    def sendData(self, client_socket, message):
        client_socket.write(message.encode("utf-8"))

class WindowClass(QMainWindow, from_class):
    conn = None
    login = ""
    name = ""
    user_id = 0

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.conn = database.pickup_database(
            "addinedu.synology.me",
            "pickup",
            "Addinedu5!",
            "pickup"
        )

        self.setWindowTitle("Administrator")

        self.setHeaderSisze()
        
        self.editOrderQuantity.setValidator(QIntValidator())
        self.editPW.setEchoMode(QLineEdit.Password)

        self.tbInventory.verticalHeader().setVisible(False)
        self.tbOrderList.verticalHeader().setVisible(False)
        self.tbOrder.verticalHeader().setVisible(False)
        self.tbLog.verticalHeader().setVisible(False)

        self.tbInventory.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbOrderList.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbOrder.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbLog.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbInventory.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbOrderList.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbOrder.setSelectionBehavior(QTableWidget.SelectRows)

        self.btnLogin.clicked.connect(self.loginOK)
        self.editPW.returnPressed.connect(self.loginOK)
        self.test.clicked.connect(self.testLog)
        self.tbOrder.itemClicked.connect(self.clickOrderProduct)
        self.btnOrder.clicked.connect(self.order)
        self.tbInventory.itemDoubleClicked.connect(self.inventoryStore)
        self.tbOrderList.itemDoubleClicked.connect(self.deleteOrderList)
        self.tabWidget.currentChanged.connect(self.tabChanged)
        self.tabWidget.setCurrentIndex(0)

        self.btnTest.clicked.connect(self.sendTest)

        self.server = Server(self)
        if self.server.listen(QHostAddress.Any, 8888):
            print("Server listen on port 8888")
        else:
            print("Failed listen on port 8888")

        self.orderServer = OrderServer(self)
        if self.orderServer.listen(QHostAddress.Any, 8889):
            print("OrderServer listen on port 8889")

    def sendTest(self):
        print(self.server.client_list)
        self.server.sendData(self.server.client_list["2"], "$SV+0+1/5")

    def testLog(self):
        sql = "update user set status = 0 where login_id = 'admin'"
        self.conn.execute_query(sql)

        self.tabWidget.setEnabled(True)

    def tabChanged(self):
        current_tab = self.tabWidget.currentWidget().objectName()
        if current_tab in ("tab_4", "tab"):     # 물품재고, 물품주문 탭
            self.updateOrderList()
        elif current_tab == "tab_2":            # 주문목록 탭
            self.lblProductName.setText("")
            self.lblQuantity.setText("")
            self.editOrderQuantity.clear()
        elif current_tab == "tab_3":            # 로그 탭
            self.updateLog()

    def updateLog(self):
        sql = "select * from log"
        result = self.conn.fetch_all(sql)

        for i in result:
            row = self.tbLog.rowCount()
            self.tbLog.insertRow(0)
            for idx, item in enumerate(i):
                self.tbLog.setItem(row, idx, QTableWidgetItem(str(item)))

    def writeLog(self, type, message):
        sql = "insert into log(event_type, message) values(%s, %s)"
        self.conn.execute_query(sql, (type, message))

        self.updateLog()

    def deleteOrderList(self):
        row = self.tbOrderList.currentRow()
        order_id = self.tbOrderList.item(row, 0).text()
        name = self.tbOrderList.item(row, 1).text()

        ret = QMessageBox.question(self, "Delete Order...", name + "님의 " + order_id + "번 주문을 삭제하시겠습니까?",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if ret == QMessageBox.Yes:
            sql = "delete from `order` where id = %s"
            self.conn.execute_query(sql, (order_id,))

            self.updateOrderList()

            QMessageBox.information(self, "Success", "주문을 삭제하였습니다.")

    def inventoryStore(self):
        row = self.tbInventory.currentRow()
        product = self.tbInventory.item(row, 1).text()
        quantity = self.tbInventory.item(row, 3).text()
        inputQuantity, ok = QInputDialog.getInt(self, "Product Store...", product + " 몇개를 입고하시겠습니까?", int(quantity))

        if ok and inputQuantity:
            sql = "update products set quantity = %s where name = %s"
            storeQuantity = int(quantity) + int(inputQuantity)
            self.conn.execute_query(sql, (storeQuantity, product))

            QMessageBox.information(self, "Success...", product + " " + str(storeQuantity) + "개를 입고했습니다.")

            self.updateProductList()

    def order(self):
        inventoryQuantity = int(self.lblQuantity.text())
        if inventoryQuantity == 0:
            QMessageBox.warning(self, "Order Failed...", "해당 물품은 품절입니다.")
            return

        quantity = int(self.editOrderQuantity.text())

        if inventoryQuantity < quantity:
            QMessageBox.warning(self, "Order Failed...", "재고량보다 많이 주문할 수 없습니다.")
            self.editOrderQuantity.setFocus()
        else:
            product_id = self.tbOrder.item(self.tbOrder.currentRow(), 0).text()
            if self.orderQuery(user_id, product_id, quantity):
                QMessageBox.information(self, "Order Success...", self.lblProductName.text() + " " + str(quantity) + "개를 주문하였습니다.")
                self.updateProductList()
                #self.lblQuantity.setText(str(updateQuantity))

    def orderQuery(self, user_id, product_id, quantity):
        success = False

        try:
            sql = "insert into `order`(user_id, product_id, quantity) values(%s, %s, %s)"
            self.conn.execute_query(sql, (user_id, product_id, quantity))

            sql = """
            update products set quantity = ((select quantity from products where id = %s) - %s)
            where id = %s
            """
            self.conn.execute_query(sql, (product_id, quantity, product_id))

            success = True
        except Exception:
            success = False

        return success

    def clickOrderProduct(self):
        row = self.tbOrder.currentRow()
        name = self.tbOrder.item(row, 2).text()
        quantity = self.tbOrder.item(row, 3).text()

        self.lblProductName.setText(name)
        self.lblQuantity.setText(quantity)
        self.editOrderQuantity.setText(quantity)

    def updateOrderList(self):
        self.tbOrderList.clearContents()
        self.tbOrderList.setRowCount(0)
        
        result = self.orderListQuery()

        for i in result:
            row = self.tbOrderList.rowCount()
            self.tbOrderList.insertRow(row)
            for idx, item in enumerate(i):
                self.tbOrderList.setItem(row, idx, QTableWidgetItem(str(item)))

    def orderListQuery(self):
        sql = """
        select `order`.id, user.name, products.name, `order`.quantity, `order`.status, `order`.date
        from `order`, user, products 
        where user.id = `order`.user_id and products.id = `order`.product_id
        """

        result = self.conn.fetch_all(sql)

        return result

    def productListQuery(self):
        sql = "select * from products"

        result = self.conn.fetch_all(sql)

        return result

    def updateProductList(self):
        self.tbInventory.clearContents()
        self.tbInventory.setRowCount(0)
        self.tbOrder.clearContents()
        self.tbOrder.setRowCount(0)


        list = self.productListQuery()
        
        for i in list:
            row = self.tbInventory.rowCount()
            self.tbInventory.insertRow(row)
            self.tbOrder.insertRow(row)
            for idx, j in enumerate(i):
                self.tbInventory.setItem(row, idx, QTableWidgetItem(str(j)))
                if idx == 5:
                    text = self.tbInventory.item(row, 5).text().split(" ")[0]
                    self.tbInventory.setItem(row, 5, QTableWidgetItem(text))

            self.tbOrder.setItem(row, 0, QTableWidgetItem(str(i[0])))
            self.tbOrder.setItem(row, 1, QTableWidgetItem(str(i[2])))
            self.tbOrder.setItem(row, 2, QTableWidgetItem(str(i[1])))
            self.tbOrder.setItem(row, 3, QTableWidgetItem(str(i[3])))

    def loginOK(self):
        id = self.editID.text()
        pw = self.editPW.text()

        if id == "":
            QMessageBox.warning(self, "Login Failed...", "아이디를 입력해주세요.")
            self.editID.setFocus()
            return
        elif pw == "":
            QMessageBox.warning(self, "Login Failed...", "패스워드를 입력해주세요.")
            self.editPW.setFocus()
            return
        
        state = self.loginQuery(id, pw)
        if state[0] == 1:                
            self.tabWidget.setEnabled(True)
            self.editID.setEnabled(False)
            self.editPW.setEnabled(False)

            self.updateProductList()
            global login, name, user_id
            login = self.editID.text()
            name = state[2]
            user_id = state[1]
        elif state[0] == -1:
            QMessageBox.warning(self, "Login Failed...", "이미 로그인중인 계정입니다.")
            return
        elif state[0] == 0:
            QMessageBox.warning(self, "Login Failed...", "아이디, 패스워드를 다시 확인해주세요.")
            self.editID.clear()
            self.editPW.clear()
            self.editID.setFocus()

    def loginQuery(self, id, pw):
        sql = "select status, id, name from user where login_id = '" + id + "' and password = '" + pw + "'"
        result = self.conn.fetch_one(sql)
        if result:
            status = result[0]
            if status == 1:
                return {"state":-1}
                        
            sql = "update user set status = 1 where login_id = '" + id + "'"
            self.conn.execute_query(sql)

            return {"state":1, "id":result[1], "name":result[2]}
        else:
            return {"state":0}

    def setHeaderSisze(self):
        # 물품재고 탭
        self.tbInventory.setColumnWidth(0, 50)
        self.tbInventory.setColumnWidth(1, 130)
        self.tbInventory.setColumnWidth(2, 90)
        self.tbInventory.setColumnWidth(3, 55)
        self.tbInventory.setColumnWidth(4, 80)
        self.tbInventory.setColumnWidth(5, 124)

        # 주문목록 탭
        self.tbOrderList.setColumnWidth(0, 65)
        self.tbOrderList.setColumnWidth(1, 70)
        self.tbOrderList.setColumnWidth(2, 125)
        self.tbOrderList.setColumnWidth(3, 55)
        self.tbOrderList.setColumnWidth(4, 55)
        self.tbOrderList.setColumnWidth(5, 153)

        # 물품주문 탭
        self.tbOrder.setColumnWidth(0, 50)
        self.tbOrder.setColumnWidth(1, 100)
        self.tbOrder.setColumnWidth(2, 100)
        self.tbOrder.setColumnWidth(3, 50)

        # 로그 탭
        self.tbLog.setColumnWidth(0, 50)
        self.tbLog.setColumnWidth(1, 70)
        self.tbLog.setColumnWidth(2, 250)
        self.tbLog.setColumnWidth(3, 150)

    def logout(self, id):
        sql = "update user set status = 0 where login_id = '" + id + "'"
        self.conn.execute_query(sql)

    def closeEvent(self, a0):
        if self.login != "":
            self.logout(self.login)
        self.conn.dispose()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindows = WindowClass()
    myWindows.show()

    sys.exit(app.exec_())
