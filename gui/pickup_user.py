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
    send_data = pyqtSignal(dict)

    def __init__(self):
        super(Client, self).__init__()

        self.errorOccurred.connect(self.on_errorOccurred)
        self.connected.connect(self.on_connected)
        self.readyRead.connect(self.receiveData)
        self.send_data.connect(self.sendData)

    def receiveData(self):
        while self.bytesAvailable() > 0:
            data = self.readAll().data().decode('utf-8')

            self.receive_data.emit(json.loads(data))

    def sendData(self, message):
        if self.state() == QTcpSocket.ConnectedState:
            data = json.dumps(message, default=str)
            self.write(data.encode('utf-8'))

    def on_connected(self):
        self.receive_data.emit({"CON"})

    def on_errorOccurred(self):
        self.receive_data.emit({"FAIL"})


class WindowClass(QMainWindow, from_class):

    login_id = ""
    name = ""
    user_id = 0
    
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.setWindowTitle("User")

        self.socket = Client()
        self.socket.connectToHost(QHostAddress("192.168.2.26"), 8889)
        self.socket.receive_data.connect(self.receiveData)

        self.editPW.setEchoMode(QLineEdit.Password)
        self.editPW.returnPressed.connect(self.loginClicked)
        self.tbOrder.verticalHeader().setVisible(False)
        self.tbOrder.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbOrder.itemClicked.connect(self.selectProduct)
        self.tabWidget.setCurrentIndex(0)

        self.btnLogin.clicked.connect(self.loginClicked)
        self.btnOrder.clicked.connect(self.requestOrder)

        self.setHeaderSisze()

    def receiveData(self, data):
        command = data["command"]

        if command == "LIOK":
            state = data["state"]
            
            if state == -1:
                QMessageBox.warning(self, "Login Failed...", "이미 로그인중인 계정입니다.")
            elif state == 0:
                QMessageBox.warning(self, "Login Failed...", "아이디, 패스워드를 다시 입력해주세요.")
                self.editID.clear()
                self.editPW.clear()
                self.editID.setFocus()
            elif state == 1:
                QMessageBox.warning(self, "Login Success", "로그인 성공")
                self.groupBox.setEnabled(False)

                self.login_id = self.editID.text()
                self.name = data["name"]
                self.id = data["id"]

                self.socket.sendData({"command":"IN"})
        elif command == "INOK":
            print(data["data"])

            for items in data["data"]:
                row = self.tbOrder.rowCount()
                self.tbOrder.insertRow(row)
                for idx, item in enumerate(items):
                #item = item.split(",")
                    print(idx, item)
                    
                    self.tbOrder.setItem(row, idx, QTableWidgetItem(str(item)))
                
        elif command == "ODOK":
            self.socket.sendData("IN+0")

    def requestOrder(self):
        name = self.lblProductName.text()
        quantity = self.lblQuantity.text()
        requestQuantity = self.editOrderQuantity.text()
        try:
            product_id = self.tbOrder.item(self.tbOrder.currentRow(), 0).text()
        except AttributeError:
            QMessageBox.warning(self, "Order Failed...", "주문할 물품을 선택해주세요.")
            return

        if requestQuantity > quantity:
            QMessageBox.warning(self, "Order Failed...", "재고량보다 많이 주문할 수 없습니다.")
        elif requestQuantity == "0" or requestQuantity == "":
            QMessageBox.warning(self, "Order Failed...", "주문수량을 입력해주세요.")
        else:
            data = {
                "command" : "OD",
                "name" : self.name,
                "product_id" : product_id,
                "quantity" : requestQuantity
            }

            self.socket.sendData(data)

            QMessageBox.information(self, "Success...", name + " " + requestQuantity + "개를 주문했습니다.")
        

    def selectProduct(self):
        row = self.tbOrder.currentRow()
        name = self.tbOrder.item(row, 2).text()
        quantity = self.tbOrder.item(row, 3).text()

        self.lblProductName.setText(name)
        self.lblQuantity.setText(quantity)
        self.spinQuantity.setMaximum(int(quantity))

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
        self.tbOrder.setColumnWidth(0, 50)
        self.tbOrder.setColumnWidth(1, 103)
        self.tbOrder.setColumnWidth(2, 103)
        self.tbOrder.setColumnWidth(3, 50)

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