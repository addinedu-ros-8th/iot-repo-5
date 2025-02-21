import sys
import os
import json
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtNetwork import QTcpSocket, QHostAddress

path = os.path.join(os.path.dirname(__file__), 'pickup_user.ui') 
from_class = uic.loadUiType(path)[0]

class Client(QTcpSocket):
    receive_data = pyqtSignal(dict)

    def __init__(self):
        super(Client, self).__init__()

        self.errorOccurred.connect(self.on_errorOccurred)
        self.connected.connect(self.on_connected)
        self.readyRead.connect(self.receiveData)

    def receiveData(self):
        while self.bytesAvailable() > 0:
            data = self.readAll().data().decode('utf-8')

            self.receive_data.emit(json.loads(data))

    def sendData(self, message):
        if self.state() == QTcpSocket.ConnectedState:
            data = json.dumps(message, default=str)
            self.write(data.encode('utf-8'))

    def on_connected(self):
        self.receive_data.emit({"command":"CON"})

    def on_errorOccurred(self):
        self.receive_data.emit({"command":"FAIL"})


class WindowClass(QMainWindow, from_class):

    login_id = ""
    name = ""
    user_id = 0
    
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.setWindowTitle("User")

        self.socket = Client()
        self.socket.connectToHost(QHostAddress("192.168.0.41"), 8889)
        self.socket.receive_data.connect(self.receiveData)

        self.groupBox.setEnabled(False)
        self.tabWidget.setEnabled(False)

        self.editPW.setEchoMode(QLineEdit.Password)
        self.editPW.returnPressed.connect(self.loginClicked)
        self.tbOrder.verticalHeader().setVisible(False)
        self.tbShoppingCart.verticalHeader().setVisible(False)
        self.tbOrderList.verticalHeader().setVisible(False)
        self.tbOrder.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbShoppingCart.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbOrderList.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbOrder.itemClicked.connect(self.selectProduct)
        self.tabWidget.setCurrentIndex(0)
        self.tabWidget.currentChanged.connect(self.tabChanged)

        self.btnLogin.clicked.connect(self.loginClicked)
        self.btnOrder.clicked.connect(self.addShoppingCart)
        self.btnDelete.clicked.connect(self.delShoppingCart)
        self.btnModify.clicked.connect(self.modifyShoppingCart)

        self.setHeaderSisze()

    def receiveData(self, data):
        command = data["command"]

        if command == "CON":
            self.groupBox.setEnabled(True)
        elif command == "FAIL":
            QMessageBox.warning(self, "Error...", "서버 연결 실패")
        if command == "LI":
            status = data["status"]
            
            if status == 2:
                QMessageBox.warning(self, "Login Failed...", "이미 로그인중인 계정입니다.")
            elif status == 0:
                QMessageBox.warning(self, "Login Failed...", "아이디, 패스워드를 다시 입력해주세요.")
                self.editID.clear()
                self.editPW.clear()
                self.editID.setFocus()
            elif status == 1:
                QMessageBox.warning(self, "Login Success", "로그인 성공")
                self.groupBox.setEnabled(False)
                self.tabWidget.setEnabled(True)

                self.login_id = self.editID.text()
                self.name = data["name"]
                self.user_id = data["user_id"]

                self.socket.sendData({"command":"IN"})
        elif command == "IN":
            for items in data["data"]:
                row = self.tbOrder.rowCount()
                self.tbOrder.insertRow(row)
                for idx, item in enumerate(items):                    
                    self.tbOrder.setItem(row, idx, QTableWidgetItem(str(item)))

                price = int(self.tbOrder.item(row, 4).text())
                self.tbOrder.setItem(row, 4, QTableWidgetItem(format(price, ",d")))
                
        elif command == "SC":
            status = data["status"]

            if status == 1:
                QMessageBox.information(self, "Success...", "장바구니 담기 성공")
            elif status == 2:
                QMessageBox.warning(self, "Failed...", "장바구니 담기 실패")
            elif status == 4:
                self.tbShoppingCart.clearContents()
                self.tbShoppingCart.setRowCount(0)
                totalPrice = 0
                for items in data["data"]:
                    row = self.tbShoppingCart.rowCount()
                    self.tbShoppingCart.insertRow(row)

                    self.tbShoppingCart.setItem(row, 0, QTableWidgetItem(str(items[0])))
                    self.tbShoppingCart.setItem(row, 1, QTableWidgetItem(items[1]))
                    spinBox = QSpinBox()
                    spinBox.setValue(int(items[2]))
                    currentQuantity = spinBox.value()
                    spinBox.valueChanged.connect(lambda value: self.modifySpinQuantity(value))
                    self.tbShoppingCart.setCellWidget(row, 2, spinBox)

                    price = int(items[3])
                    self.tbShoppingCart.setItem(row, 3, QTableWidgetItem(format(price, ",d")))
                    totalPrice += price
                
                self.lblTotalPrice.setText(format(totalPrice, ",d"))
            elif status == 5:
                QMessageBox.information(self, "Success...", "수량 수정 완료")
            elif status == 6:
                QMessageBox.information(self, "Success...", "상품 삭제 완료")

                data = {"command":"SC", "status":3, "user_id":self.user_id}
                self.socket.sendData(data)

    def modifySpinQuantity(self, row):
        row = self.tbShoppingCart.currentRow()

        quantity = int(self.tbShoppingCart.cellWidget(row, 2).value())
        price = int(self.tbShoppingCart.item(row, 3).text()) / quantity

        self.tbShoppingCart.setItem(row, 3, QTableWidgetItem(price * quantity))


    def modifyShoppingCart(self):
        row = self.tbShoppingCart.currentRow()

        if row < 0:
            QMessageBox.warning(self, "Failed...", "수정할 상품을 선택해주세요.")
        else:
            cart_id = self.tbShoppingCart.item(row, 0).text()
            quantity = self.tbShoppingCart.cellWidget(row, 2).value()

            data = {
                "command" : "SC",
                "status" : 5,
                "cart_id" : cart_id,
                "quantity" : quantity
            }
            self.socket.sendData(data)

    def delShoppingCart(self):
        row = self.tbShoppingCart.currentRow()

        if row < 0:
            QMessageBox.warning(self, "Failed...", "삭제할 상품을 선택해주세요.")
        else:
            cart_id = self.tbShoppingCart.item(row, 0).text()

            data = {
                "command" : "SC",
                "status" : 6,
                "user_id" : self.user_id,
                "cart_id" : cart_id
            }
            self.socket.sendData(data)

    def addShoppingCart(self):
        quantity = int(self.lblQuantity.text())
        requestQuantity = int(self.spinQuantity.value())

        row = self.tbOrder.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Failed...", "장바구니에 담을 상품을 선택해주세요.")
        product_id = self.tbOrder.item(self.tbOrder.currentRow(), 0).text()

        if requestQuantity > quantity:
            QMessageBox.warning(self, "Failed...", "재고량보다 많이 담을 수 없습니다.")
        elif requestQuantity == 0:
            QMessageBox.warning(self, "Failed...", "주문수량을 입력해주세요.")
        else:
            data = {
                "command" : "SC",
                "status" : 0,
                "user_id" : self.user_id,
                "product_id" : product_id,
                "quantity" : requestQuantity
            }

            self.socket.sendData(data)        

    def selectProduct(self):
        row = self.tbOrder.currentRow()
        name = self.tbOrder.item(row, 2).text()
        quantity = self.tbOrder.item(row, 3).text()
        price = self.tbOrder.item(row, 4).text()

        self.lblProductName.setText(name)
        self.lblQuantity.setText(quantity)
        self.spinQuantity.setMaximum(int(quantity))
        self.lblPrice.setText(price)

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

    def tabChanged(self):
        current_tab = self.tabWidget.currentWidget().objectName()
        if current_tab in ("tab_2"):
            data = {
                "command" : "SC",
                "status" : 3,
                "user_id" : self.user_id
            }
            self.socket.sendData(data)

    def setHeaderSisze(self):
        self.tbOrder.setColumnWidth(0, 50)
        self.tbOrder.setColumnWidth(1, 100)
        self.tbOrder.setColumnWidth(2, 100)
        self.tbOrder.setColumnWidth(3, 50)
        self.tbOrder.setColumnWidth(4, 50)

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