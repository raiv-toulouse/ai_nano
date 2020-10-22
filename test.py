import sys
import argparse
from PyQt5.QtWidgets import *
from PyQt5.QtCore import  *

# class SelectNameAndColor(QWidget):
#     def __init__(self):


# creation de la class, on precise qu'on derive la class QPushButton entre parentheses
class PushButtonRight(QPushButton):
    # creation du signal emetteur (emet rien pour le moment)
    rightClick = pyqtSignal()
    doubleClicked = pyqtSignal()
    clicked = pyqtSignal()

    # creation de notre fontion __init__ avec un arg string pour le nom du futur bouton
    def __init__(self, string):
        # on integre la classe QPushButton a notre class PushRightButton
        QPushButton.__init__(self, string)
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.clicked.emit)
        super().clicked.connect(self.checkDoubleClick)

    # modification de la fontion mousePressEvent
    def mousePressEvent(self, event):
        # on integre la fonction QPushButton.mousePressEvent(self, event) a notre fonction PushRightButton.mousePressEvent(self, event)
        QPushButton.mousePressEvent(self, event)
        # condition du click droit
        if event.button() == Qt.RightButton:
            # emission du signal rightClick
            self.rightClick.emit()

    @pyqtSlot()
    def checkDoubleClick(self):
        if self.timer.isActive():
            self.doubleClicked.emit()
            self.timer.stop()
        else:
            self.timer.start(250)

class ButtonBlock(QWidget):

    def __init__(self, args):
        super(QWidget, self).__init__()
        layout = QVBoxLayout()
        nbClass = int(args["nbClass"])
        print(nbClass)
        self.lesBoutons = []
        for i in range(nbClass):
            button = PushButtonRight(str(i))
            self.lesBoutons.append(button)
            button.setStyleSheet("background-color: rgb(255,255,0)")
            button.clicked.connect(self.make_calluser(button))
            layout.addWidget(button)
        self.setLayout(layout)

    def make_calluser(self, button):
        def calluser():
            print(button.text())
        return calluser




# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-n", "--nbClass", required=True, help="number of class")
args = vars(ap.parse_args())

app = QApplication([])
tb = ButtonBlock(args)
tb.show()
app.exec_()