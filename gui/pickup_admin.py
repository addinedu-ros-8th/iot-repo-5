import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal
import json
from PyQt5.QtNetwork import QTcpSocket, QHostAddress

path = os.path.join(os.path.dirname(__file__), 'pickup_admin.ui') 
from_class = uic.loadUiType(path)[0]

class Client(QTcpSocket):
    receive_data = pyqtSignal(dict)

    def __init__(self):
        super(Client, self).__init__()

        #self.connected.connect(self.on_connected)
        self.readyRead.connect(self.receiveData)
        #self.send_data.connect(self.sendData)

    def receiveData(self):
        while self.bytesAvailable() > 0:
            data = self.readAll().data().decode('utf-8')

            self.receive_data.emit(json.loads(data))

    def sendData(self, message):
        if self.state() == QTcpSocket.ConnectedState:
            data = json.dumps(message, default=str)
            self.write(data.encode('utf-8'))

class AddProductWindow(QDialog):
    def __init__(self, socket):
        super().__init__()

        a = os.path.join(os.path.dirname(__file__), 'add_product.ui') 
        self.ui = uic.loadUi(a, self)
        self.setWindowTitle("상품 등록")
        self.socket = socket

        self.cbCategory.addItem("과자")
        self.cbCategory.addItem("아이스크림")
        self.cbCategory.addItem("사탕")

        self.btnAddProduct.clicked.connect(self.addProduct)

    def addProduct(self):
        data = {
            "command" : "AP",
            "status" : 0x00,
            "name" : self.editProductName.text(),
            "price" : int(self.editPrice.text()),
            "category" : self.cbCategory.currentText(),
            "quantity" : int(self.editQuantity.text()),
            "uid" : self.editSection.text()
        }
        self.socket.sendData(data)

class WindowClass(QMainWindow, from_class):
    login_id = ""
    name = ""
    user_id = 0

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.setWindowTitle("Administrator")

        self.setHeaderSisze()

        self.socket = Client()
        self.socket.connectToHost(QHostAddress("192.168.0.2"), 8889)
        self.socket.receive_data.connect(self.receiveData)
        
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

        self.btnLogin.clicked.connect(self.loginClicked)
        self.editPW.returnPressed.connect(self.loginClicked)
        self.tbOrder.itemClicked.connect(self.clickOrderProduct)
        self.btnOrder.clicked.connect(self.order)
        self.tbInventory.itemDoubleClicked.connect(self.inventoryStore)
        self.tbOrderList.itemDoubleClicked.connect(self.deleteOrderList)
        self.tabWidget.currentChanged.connect(self.tabChanged)
        self.tabWidget.setCurrentIndex(0)
        self.btnAddSection.clicked.connect(self.addSection)

    def receiveData(self, data):
        command = data["command"]

        if command == "LI":
            status = data["status"]

            if status == 0x02:
                QMessageBox.warning(self, "Login Failed...", "이미 로그인중인 계정입니다.")
            elif status == 0x00:
                QMessageBox.warning(self, "Login Failed...", "아이디, 패스워드를 다시 입력해주세요.")
                self.editID.clear()
                self.editPW.clear()
                self.editID.setFocus()
            elif status == 0x01:
                QMessageBox.warning(self, "Login Success", "로그인 성공")
                self.groupBox.setEnabled(False)
                self.tabWidget.setEnabled(True)

                self.login_id = self.editID.text()
                self.name = data["name"]
                self.user_id = data["user_id"]

                self.socket.sendData({"command":"IN"})
        elif command == "AP":
            if data["status"] == 0x01:
                QMessageBox.information(self, "Success...", "물품 등록 성공")
        elif command == "IN":
            self.tbInventory.clearContents()
            self.tbInventory.setRowCount(0)
            self.tbOrder.clearContents()
            self.tbOrder.setRowCount(0)
            self.lblProductName.setText("")
            self.lblQuantity.setText("")
            self.spinQuantity.setValue(0)
            
            for items in data["data"]:
                row = self.tbInventory.rowCount()
                self.tbInventory.insertRow(row)
                self.tbOrder.insertRow(row)
                for idx, item in enumerate(items):                    
                    self.tbInventory.setItem(row, idx, QTableWidgetItem(str(item)))

                price = int(self.tbInventory.item(row, 4).text())
                self.tbInventory.setItem(row, 4, QTableWidgetItem(format(price, ",d")))

                self.tbOrder.setItem(row, 0, QTableWidgetItem(str(items[0])))
                self.tbOrder.setItem(row, 1, QTableWidgetItem(items[1]))
                self.tbOrder.setItem(row, 2, QTableWidgetItem(items[2]))
                self.tbOrder.setItem(row, 3, QTableWidgetItem(str(items[3])))
        elif command == "OL":
            for items in data["data"]:
                row = self.tbOrderList.rowCount()
                self.tbOrderList.insertRow(row)

                order_id = items[6]
                user_name = items[5]
                product_name = items[0]
                quantity = items[1]
                status = items[3]
                date = items[4]

                self.tbOrderList.setItem(row, 0, QTableWidgetItem(str(order_id)))
                self.tbOrderList.setItem(row, 1, QTableWidgetItem(user_name))
                self.tbOrderList.setItem(row, 2, QTableWidgetItem(product_name))
                self.tbOrderList.setItem(row, 3, QTableWidgetItem(str(quantity)))
                if status == 0:
                    text = "주문접수"
                elif status == 1:
                    text = "상품적재중"
                elif status ==2 :
                    text = "픽업요청"
                self.tbOrderList.setItem(row, 4, QTableWidgetItem(str(text)))
                self.tbOrderList.setItem(row, 5, QTableWidgetItem(str(date).split(" ")[0]))

    def addSection(self):
        product_windows = AddProductWindow(self.socket)
        product_windows.show()

    def tabChanged(self):
        current_tab = self.tabWidget.currentWidget().objectName()
        if current_tab in ("tab", "tab_2"):     # 물품재고, 물품주문 탭
            if self.socket is not None:
                self.socket.sendData({"command":"IN"})
        elif current_tab == "tab_4":            # 주문목록 탭
            self.socket.sendData({"command":"OL", "status":0x00, "user_id":None})
        elif current_tab == "tab_3":            # 로그 탭
            pass

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
        quantity = int(self.spinQuantity.value())

        if inventoryQuantity < quantity:
            QMessageBox.warning(self, "Order Failed...", "재고량보다 많이 주문할 수 없습니다.")
        else:
            product_id = self.tbOrder.item(self.tbOrder.currentRow(), 0).text()
            
            data = {
                "command" : "CH",
                "status" : 0x03,
                "user_id" : self.user_id,
                "data" : [product_id, quantity]
            }
            self.socket.sendData(data)

    def clickOrderProduct(self):
        row = self.tbOrder.currentRow()
        name = self.tbOrder.item(row, 2).text()
        quantity = self.tbOrder.item(row, 3).text()

        self.lblProductName.setText(name)
        self.lblQuantity.setText(quantity)
        self.spinQuantity.setMinimum(1)
        self.spinQuantity.setMaximum(int(quantity))

    def updateProductList(self):
        self.tbInventory.clearContents()
        self.tbInventory.setRowCount(0)
        self.tbOrder.clearContents()
        self.tbOrder.setRowCount(0)
        
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

    def loginClicked(self):
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
        
        data = {
            "command" : "LI",
            "login_id" : id,
            "pw" : pw
        }
        
        self.socket.sendData(data)


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

    def closeEvent(self, a0):
        if self.login_id != "":
            data = {
                "command" : "LO",
                "id" : self.login_id
            }
            self.socket.sendData(data)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindows = WindowClass()
    myWindows.show()

    sys.exit(app.exec_())
