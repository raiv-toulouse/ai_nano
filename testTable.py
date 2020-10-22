from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

class MyTableWidget(QTableWidget):

    def __init__(self):
        super().__init__(None)
        button = QPushButton('Click me', self)
        button.clicked.connect(self.buttonClicked)
        self.setCellWidget(1, 1, button)


    def buttonClicked(self):
        button = self.sender()
        print(button.parent() is self)


app = QApplication([])
table = MyTableWidget()
table.show()
app.exec_()