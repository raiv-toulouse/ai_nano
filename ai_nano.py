# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.uic import loadUi
import cv2
from threadLectureCamera import *

#
# Goal :
#
class GUI_ai_nano(QWidget):
    '''
    GUI
    '''
    def __init__(self, parent=None):
        super().__init__()
        loadUi('ai_nano.ui', self)
        self.thread = ThreadLectureCamera()
        self.thread.signalAfficherImage.connect(self.display_image_from_camera)
        self.thread.start()
        # Event handlers
        self.btn_working_space.clicked.connect(self.select_ws)
        self.sb_camera_id.valueChanged.connect(self.camera_changed)
        self.btn_project_ok.clicked.connect(self.create_project)

    def select_ws(self):
        self.ws = str(QFileDialog.getExistingDirectory(self, "Select Directory"))

    def camera_changed(self):
        self.thread.changeCamera(self.sb_camera_id.value())

    def display_image_from_camera(self,img):
        """
        Affichage d'une image dans le QLabel nommé video_frame
        """
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        (height, width, _) = img.shape
        mQImage = QImage(img, width, height, QImage.Format_RGB888)
        pix = QPixmap.fromImage(mQImage)
        self.lbl_image.setPixmap(pix)

    def create_project(self):
        self.table_recording.setRowCount(self.sb_nb_categories.value())
        button = QPushButton('Click me', self)
        self.table_recording.setCellWidget(1,1,button)

#
# Main program
#
if __name__ == '__main__':
    # GUI
    app = QApplication([])
    gui = GUI_ai_nano()
    gui.show()
    app.exec_()