import sys
import os
import json
import time
from datetime import datetime, timedelta
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, QDate, QObject, QEvent, Qt
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
            self.flush()

    def on_connected(self):
        self.receive_data.emit({"command":"CON"})

    def on_errorOccurred(self):
        self.receive_data.emit({"command":"FAIL"})

class RegistWindow(QDialog):
    def __init__(self, socket):
        super().__init__()

        a = os.path.join(os.path.dirname(__file__), 'regist.ui') 
        self.ui = uic.loadUi(a, self)
        self.setWindowTitle("회원가입")
        self.socket = socket

        self.editNewPW.setEchoMode(QLineEdit.Password)
        self.editNewPW2.setEchoMode(QLineEdit.Password)

        self.btnRegister.clicked.connect(self.regist)

    def regist(self):
        name = self.editNewName.text()
        id = self.editNewID.text()
        pw = self.editNewPW.text()
        pw2 = self.editNewPW2.text()

        if pw != pw2:
            QMessageBox.warning(self, "Failed..", "패스워드가 서로 다릅니다.")
            self.editNewPW.clear()
            self.editNewPW2.clear()
            self.editNewPW.setFocus()
        else:
            data = {
                "command" : "REG",
                "status" : 0x00,
                "name" : name,
                "id" : id,
                "pw" : pw
            }
            self.socket.sendData(data)


class WindowClass(QMainWindow, from_class):

    login_id = ""
    name = ""
    user_id = 0
    
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.setWindowTitle("User")
        #self.resize(280, 140)
        self.setFixedSize(280, 140)

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
        self.tbOrder.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbShoppingCart.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbOrderList.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbOrder.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tbShoppingCart.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tbOrderList.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tbOrder.itemClicked.connect(self.selectProduct)
        self.tabWidget.setCurrentIndex(0)
        self.tabWidget.currentChanged.connect(self.tabChanged)

        self.btnLogin.clicked.connect(self.loginClicked)
        self.btnOrder.clicked.connect(self.addShoppingCart)
        self.btnDelete.clicked.connect(self.delShoppingCart)
        self.btnModify.clicked.connect(self.modifyShoppingCart)
        self.btnCheckout.clicked.connect(self.checkout)
        self.tbOrderList.itemDoubleClicked.connect(self.receiveProduct)
        self.pushButton.clicked.connect(self.fetchOrderList)
        diff_date = datetime.now() - timedelta(days=1825)
        self.dateEdit.setMinimumDate(diff_date)
        self.dateEdit.setMaximumDate(datetime.now())
        self.dateEdit_2.setMinimumDate(diff_date)
        self.dateEdit_2.setMaximumDate(datetime.now())
        self.dateEdit.setDate(diff_date)
        self.dateEdit_2.setDate(datetime.now())
        clickable(self.lblRegist).connect(self.showRegistWindow)

        self.setHeaderSisze()
        sys.excepthook = self.handle_exception

        self.socket.sendData({"command":"PU", "status":0x00})

        self.isPickup = False

    def fetchOrderList(self):
        flag = -1
        if self.rbAll.isChecked():
            flag = -1
        elif self.rbReady.isChecked():
            flag = 0
        elif self.rbCarray.isChecked():
            flag = 1
        elif self.rbPickup.isChecked():
            flag = 2
        data = {
            "command" : "OL",
            "status" : 0x01,
            "user_id" : self.user_id,
            "flag" : flag
        }
        self.socket.sendData(data)


    def receiveProduct(self):
        row = self.tbOrderList.currentRow()
        
        status = self.tbOrderList.item(row, 3).text()
        group_id = self.tbOrderList.item(row, 0).data(Qt.UserRole)
        if status == "픽업요청":
            ret = QMessageBox.information(self, "Pickup...", "상품을 픽업하시겠습니까?", QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                data = {
                    "command" : "PU",
                    "status" : 0x01,
                    "user_id" : self.user_id,
                    "group_id" : group_id
                }
                self.socket.sendData(data)


    def showRegistWindow(self):
        self.windows = RegistWindow(self.socket)
        self.windows.show()

    def handle_exception(self, exctype, value, traceback):
        self.closeEvent(None)
        sys.__excepthook__(exctype, value, traceback)

    def receiveData(self, data):
        command = data["command"]
        print(data)

        if command == "CON":
            self.groupBox.setEnabled(True)
            self.editID.setFocus()
        elif command == "FAIL":
            QMessageBox.warning(self, "Error...", "서버 연결 실패")
            self.groupBox.setEnabled(False)
        elif command == "ER":
            QMessageBox.warning(self, "Error...", "에러")
        elif command == "REG":
            if data["status"] == 0x01:
                QMessageBox.information(self.windows, "Success...", "회원가입이 완료되었습니다.")
                self.windows.close()
            elif data["status"] == 0x02:
                QMessageBox.warning(self.windows, "Failed...", "이미 존재하는 계정입니다.")
            elif data["status"] == 0x03:
                QMessageBox.warning(self.windows, "Error...", "에러")
        elif command == "LI":
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

                self.hide()
                self.groupBox.setVisible(False)
                #self.resize(580, 310)
                self.setFixedSize(580, 310)
                self.tabWidget.setGeometry(10, 10, 560, 290)
                self.show()

                self.socket.sendData({"command":"IN"})
        elif command == "IN":
            self.tbOrder.clearContents()
            self.tbOrder.setRowCount(0)
            
            for items in data["data"]:
                row = self.tbOrder.rowCount()
                self.tbOrder.insertRow(row)
                for idx, item in enumerate(items):                    
                    self.tbOrder.setItem(row, idx, QTableWidgetItem(str(item)))

                price = int(self.tbOrder.item(row, 4).text())
                self.tbOrder.setItem(row, 4, QTableWidgetItem(format(price, ",d")))
                
        elif command == "SC":
            status = data["status"]

            if status == 0x01:
                QMessageBox.information(self, "Success...", "장바구니 담기 성공")
            elif status == 0x02:
                QMessageBox.warning(self, "Failed...", "장바구니 담기 실패")
            elif status == 0x03:
                self.tbShoppingCart.clearContents()
                self.tbShoppingCart.setRowCount(0)
                totalPrice = 0
                for items in data["data"]:
                    row = self.tbShoppingCart.rowCount()
                    self.tbShoppingCart.insertRow(row)

                    self.tbShoppingCart.setItem(row, 0, QTableWidgetItem(str(items[0])))
                    self.tbShoppingCart.setItem(row, 1, QTableWidgetItem(items[1]))
                    quantity = int(items[2])
                    spinBox = QSpinBox()
                    spinBox.setMaximum(int(items[4]))
                    spinBox.setMinimum(1)
                    spinBox.setValue(quantity)
                    spinBox.valueChanged.connect(lambda value, row=row: self.changedSpin(value, row))
                    self.tbShoppingCart.setCellWidget(row, 2, spinBox)

                    unitPrice = int(items[3])
                    price = unitPrice * quantity
                    price_item = QTableWidgetItem(format(price, ",d"))
                    price_item.setData(Qt.UserRole, unitPrice)
                    self.tbShoppingCart.setItem(row, 3, price_item)
                    totalPrice += price
                
                self.lblTotalPrice.setText(format(totalPrice, ",d"))
            elif status == 0x05:
                QMessageBox.information(self, "Success...", "수량 수정 완료")
            elif status == 0x06:
                QMessageBox.information(self, "Success...", "상품 삭제 완료")

                data = {"command":"SC", "status":3, "user_id":self.user_id}
                self.socket.sendData(data)
        elif command == "CO":
            status = data["status"]

            if status == 0x02:
                QMessageBox.information(self, "Success...", "주문을 완료했습니다.")
                
                self.socket.sendData({"command":"SC", "status":0x03, "user_id":self.user_id})
            elif status == 0x04:
                QMessageBox.warning(self, "Failed...", "에러")
        elif command == "OL":
            status = data["status"]

            if status == 0x00:
                self.tbOrderList.clearContents()
                self.tbOrderList.setRowCount(0)
                for items in data["data"]:
                    row = self.tbOrderList.rowCount()
                    self.tbOrderList.insertRow(row)

                    quantity = items[1]
                    price = items[2]
                    status = items[3]
                    date = items[4]

                    product_name = QTableWidgetItem(items[0])
                    product_name.setData(Qt.UserRole, items[7])
                    self.tbOrderList.setItem(row, 0, product_name)
                    self.tbOrderList.setItem(row, 1, QTableWidgetItem(str(quantity)))
                    self.tbOrderList.setItem(row, 2, QTableWidgetItem(str(price)))
                    if status == 0:
                        text = "주문접수"
                    elif status == 1:
                        text = "상품적재중"
                    elif status == 2:
                        text = "픽업요청"
                        self.isPickup = True
                    elif status == 3:
                        text = "픽업완료"
                    self.tbOrderList.setItem(row, 3, QTableWidgetItem(text))
                    self.tbOrderList.setItem(row, 4, QTableWidgetItem(str(date).split(" ")[0]))
                    
                if self.isPickup:
                    QMessageBox.information(self, "Pickup...", "상품이 준비되었습니다. 픽업을 위해 매장에 방문 바랍니다.")

        elif command == "PU":
            if data["status"] == 0x00:
                QMessageBox.information(self, "Alaram...", "상품이 준비되었습니다. 픽업을 위해 매장에 방문 바랍니다.")
                data = {
                "command" : "OL",
                "status" : 0x00,
                "user_id" : self.user_id
                 }
                self.socket.sendData(data)
            elif data["status"] == 0x01:
                QMessageBox.warning(self, "Success", "상품 픽업이 완료되었습니다.")
                self.isPickup = False
                
                data = {
                "command" : "OL",
                "status" : 0x00,
                "user_id" : self.user_id
                 }
                self.socket.sendData(data)


    def checkout(self):
        row = self.tbShoppingCart.rowCount()

        if row == 0:
            QMessageBox.warning(self, "Faild...", "주문할 상품이 없습니다.")
        else:
            cart_id = [self.tbShoppingCart.item(idx, 0).text() for idx in range(row)]

            data = {
                "command" : "CO",
                "status" : 0x00,
                "cart_id" : cart_id,
                "user_id" : self.user_id
            }
            self.socket.sendData(data)

    def changedSpin(self, value, row):
        unitPrice = self.tbShoppingCart.item(row, 3).data(Qt.UserRole)
        price = unitPrice * value
        price_item = QTableWidgetItem(format(price, ",d"))
        price_item.setData(Qt.UserRole, unitPrice)
        self.tbShoppingCart.setItem(row, 3, price_item)

        totalPrice = 0
        for row in range(self.tbShoppingCart.rowCount()):
            price_text = self.tbShoppingCart.item(row, 3).text().replace(",", "")
            totalPrice += int(price_text)
        
        self.lblTotalPrice.setText(format(totalPrice, ",d"))
        

    def modifyShoppingCart(self):
        row = self.tbShoppingCart.currentRow()

        if row < 0:
            QMessageBox.warning(self, "Failed...", "수정할 상품을 선택해주세요.")
        elif self.lblQuantity.text() == "0":
            QMessageBox.warning(self, "Failed...", "해당 상품은 품절입니다.")
        else:
            cart_id = self.tbShoppingCart.item(row, 0).text()
            quantity = self.tbShoppingCart.cellWidget(row, 2).value()

            data = {
                "command" : "SC",
                "status" : 0x05,
                "cart_id" : cart_id,
                "quantity" : quantity,
                "user_id" : self.user_id
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
                "status" : 0x06,
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
                "status" : 0x00,
                "user_id" : self.user_id,
                "product_id" : product_id,
                "quantity" : requestQuantity
            }

            self.socket.sendData(data)        

    def selectProduct(self):
        row = self.tbOrder.currentRow()
        name = self.tbOrder.item(row, 1).text()
        quantity = self.tbOrder.item(row, 3).text()
        price = self.tbOrder.item(row, 4).text()

        self.lblProductName.setText(name)
        self.lblQuantity.setText(quantity)
        self.spinQuantity.setValue(1)
        self.spinQuantity.setMinimum(1)
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
        print(current_tab)
        if current_tab == "tab":
            data = {
                "command" : "IN"
            }
            self.socket.sendData(data)
        elif current_tab == "tab_2":
            data = {
                "command" : "SC",
                "status" : 0x03,
                "user_id" : self.user_id
            }
            self.socket.sendData(data)
        elif current_tab == "tab_3":
            data = {
                "command" : "OL",
                "status" : 0x00,
                "user_id" : self.user_id
            }
            self.socket.sendData(data)

    def setHeaderSisze(self):
        self.tbOrder.setColumnWidth(0, 50)
        self.tbOrder.setColumnWidth(1, 100)
        self.tbOrder.setColumnWidth(2, 100)
        self.tbOrder.setColumnWidth(3, 50)
        self.tbOrder.setColumnWidth(4, 50)

    def closeEvent(self, event):
        if self.login_id != "":
            data = {
                "command": "LO",
                "id": self.login_id
            }
            self.socket.sendData(data)

        if event:
            event.accept()

def clickable(widget):
    class Filter(QObject):
        clicked = pyqtSignal()	#pyside2 사용자는 pyqtSignal() -> Signal()로 변경

        def eventFilter(self, obj, event):
            if obj == widget:
                if event.type() == QEvent.MouseButtonRelease:
                    if obj.rect().contains(event.pos()):
                        self.clicked.emit()
                        # The developer can opt for .emit(obj) to get the object within the slot.
                        return True
            return False
    
    filter = Filter(widget)
    widget.installEventFilter(filter)
    return filter.clicked

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindows = WindowClass()
    myWindows.show()

    sys.exit(app.exec_())