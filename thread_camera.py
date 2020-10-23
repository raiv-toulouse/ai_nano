# -*- coding: utf-8 -*-

from PyQt5.QtCore import *
import cv2
from numpy import *
from time import sleep

class Thread_Camera(QThread):

    # Signaux de communication avec l'IHM (voir classe DialogChercheOeil)
    signalAfficherImage = pyqtSignal(ndarray) # Pour afficher une image dans le QLabel nommé video_frame

    def __init__(self, parent=None):
        super(Thread_Camera, self).__init__(parent)
        self.sourceVideo = cv2.VideoCapture(0)
        self.ind_image = 0
        self.path_image = None
        self.record_images = False

    def start_recording(self,ind,path):
        self.ind_image = ind
        self.path_image = path
        self.record_images = True

    def stop_recording(self):
        self.record_images = False

    def changeCamera(self,ind_camera):
        try:
            self.sourceVideo = cv2.VideoCapture(ind_camera)
        except:
            print('pb when changing camera')

    def run(self):
        """
        Méthode principale du thread. Traite chaque image issue de la source d'images pour y cherche la présence d'un oeil.
        """
        while True:
            ret, img = self.sourceVideo.read()
            if ret:
                self.signalAfficherImage.emit(img)
                if self.record_images:
                    img_path = self.path_image/(str(self.ind_image)+'.jpg')
                    cv2.imwrite(str(img_path),img)
                    self.ind_image += 1
                    sleep(0.1)

