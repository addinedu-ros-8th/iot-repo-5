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

        self.connected.connect(self.on_connected)
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

    def on_connected(self):
        print("connected server")


class WindowClass(QMainWindow, from_class):
    conn = None
    login = ""
    name = ""
    user_id = 0

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.setWindowTitle("Administrator")

        self.setHeaderSisze()
        
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
        self.test.clicked.connect(self.testLog)
        self.tbOrder.itemClicked.connect(self.clickOrderProduct)
        self.btnOrder.clicked.connect(self.order)
        self.tbInventory.itemDoubleClicked.connect(self.inventoryStore)
        self.tbOrderList.itemDoubleClicked.connect(self.deleteOrderList)
        self.tabWidget.currentChanged.connect(self.tabChanged)
        self.tabWidget.setCurrentIndex(0)

        self.socket = Client()
        self.socket.connectToHost(QHostAddress("192.168.0.41"), 8889)
        self.socket.receive_data.connect(self.receiveData)

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
            if self.orderQuery(self.user_id, product_id, quantity):
                QMessageBox.information(self, "Order Success...", self.lblProductName.text() + " " + str(quantity) + "개를 주문하였습니다.")
                self.updateProductList()
                #self.lblQuantity.setText(str(updateQuantity))

    def clickOrderProduct(self):
        row = self.tbOrder.currentRow()
        name = self.tbOrder.item(row, 2).text()
        quantity = self.tbOrder.item(row, 3).text()

        self.lblProductName.setText(name)
        self.lblQuantity.setText(quantity)
        self.spinQuantity.setMaximum(int(quantity))

    def updateOrderList(self):
        self.tbOrderList.clearContents()
        self.tbOrderList.setRowCount(0)
        
        result = self.orderListQuery()

        for i in result:
            row = self.tbOrderList.rowCount()
            self.tbOrderList.insertRow(row)
            for idx, item in enumerate(i):
                self.tbOrderList.setItem(row, idx, QTableWidgetItem(str(item)))

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
            "id" : id,
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
