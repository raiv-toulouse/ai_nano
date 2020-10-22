# -*- coding: utf-8 -*-

from PyQt5.QtCore import *
import cv2
from numpy import *

class ThreadLectureCamera(QThread):

    # Signaux de communication avec l'IHM (voir classe DialogChercheOeil)
    signalAfficherImage = pyqtSignal(ndarray) # Pour afficher une image dans le QLabel nommé video_frame

    def __init__(self, parent=None):
        super(ThreadLectureCamera, self).__init__(parent)
        self.sourceVideo = cv2.VideoCapture(0)

    def changeCamera(self,ind):
        try:
            self.sourceVideo = cv2.VideoCapture(ind)
        except:
            print('pb')

    def run(self):
        """
        Méthode principale du thread. Traite chaque image issue de la source d'images pour y cherche la présence d'un oeil.
        """
        while True:
            ret, img = self.sourceVideo.read()
            if ret:
                self.signalAfficherImage.emit(img)
