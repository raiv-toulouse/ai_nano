# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUi
import random
import os
import pysftp
from pathlib import Path
from thread_camera import *
from record_images import record_images
from zipfile import ZipFile
import paramiko
import json
import tempfile

class Computer:
    def __init__(self,dico):
        self.pwd = dico['pwd']
        self.login = dico['login']
        self.ip = dico['ip']
        self.name = dico['name']

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
        # Read the config file
        with open("config.json", "r") as read_file:
            self.config = json.load(read_file)
        self.DL_computer = Computer(self.config["DL_server"])
        self.nano_computers = []
        for dico in self.config["jetson_nano"]:
            self.nano_computers.append(Computer(dico))
        self.thread = Thread_Camera()
        self.thread.signalAfficherImage.connect(self.display_image_from_camera)
        self.thread.start()
        # Event handlers
        self.btn_working_space.clicked.connect(self.select_ws)
        self.sb_camera_id.valueChanged.connect(self.camera_changed)
        self.btn_project_ok.clicked.connect(self.create_project)
        self.btn_split_image.clicked.connect(self.split_images)
        self.btn_upload_to_dl.clicked.connect(self.upload_to_dl)
        self.btn_train_model.clicked.connect(self.train_model)

    def select_ws(self):
        self.ws = Path(QFileDialog.getExistingDirectory(self, "Select Directory"))

    def camera_changed(self):
        self.thread.changeCamera(self.sb_camera_id.value())

    def display_image_from_camera(self, img):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        (height, width, _) = img.shape
        mQImage = QImage(img, width, height, QImage.Format_RGB888)
        pix = QPixmap.fromImage(mQImage)
        self.lbl_image.setPixmap(pix)

    def create_project(self):
        self.gb_recording.setEnabled(True)
        self.btn_split_image.setEnabled(True)
        # Create working space directory
        image_dir = self.ws / "images"
        image_dir.mkdir(parents=True)
        train_dir = self.ws / "train"
        train_dir.mkdir(parents=True)
        val_dir = self.ws / "val"
        val_dir.mkdir(parents=True)
        test_dir = self.ws / "test"
        test_dir.mkdir(parents=True)
        nb_categories = self.sb_nb_categories.value()
        for i in range(nb_categories):
            ri = record_images(self.ws, self.thread)
            self.vl_record.addWidget(ri)

    def split_images(self):
        # Creation of the labels.txt file
        labels_file = open(str(self.ws / 'labels.txt'), 'w')
        for cat_dir in (self.ws / 'images').iterdir():
            category = cat_dir.name
            labels_file.write(category + '\n')
            files = [f for f in cat_dir.iterdir()]
            random.shuffle(files)
            ind_80 = int(len(files) * 0.8)  # 80 %
            ind_10 = int(len(files) * 0.1)  # 10 %
            self.split(files[:ind_80], 'train', category)
            self.split(files[ind_80:ind_80 + ind_10], 'val', category)
            self.split(files[ind_80 + ind_10:], 'test', category)
        labels_file.close()
        self.btn_upload_to_dl.setEnabled(True)

    def split(self, files, dir_name, category):
        path = self.ws / dir_name / category
        for f in files:
            f.replace(path / f.name)

    def upload_to_dl(self):
        os.chdir(str(self.ws))  # we work in the ws directory to zip relative (and not absolute) files
        with ZipFile('data.zip', 'w') as zip:
            # writing each file one by one
            self.zip_files_from_folder('train', zip)
            self.zip_files_from_folder('val', zip)
            self.zip_files_from_folder('test', zip)
            zip.write('labels.txt')  # and finally 'labels.txt'
        # Now, we can upload the ZIP file to DL machine
        cnopts = pysftp.CnOpts(knownhosts='')  # Suppress authentication, VERY BAD
        cnopts.hostkeys = None
        sftp = pysftp.Connection(self.DL_computer.ip, username=self.DL_computer.login, password=self.DL_computer.pwd, cnopts=cnopts)
        self.temp_name = next(tempfile._get_candidate_names())  # Generate a temporary name for the remote directory that we must create on DL machine
        sftp.mkdir(self.temp_name)
        with sftp.cd(self.temp_name):
            sftp.put('data.zip')
        sftp.close()
        # Unzip data on DL machine
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.DL_computer.ip, username=self.DL_computer.login, password=self.DL_computer.pwd)
        stdin, stdout, stderr = client.exec_command('cd '+self.temp_name + ';unzip data.zip')
        for line in stdout:
            print(line.strip('\n'))
        client.close()
        self.btn_train_model.setEnabled(True)

    def zip_files_from_folder(self, dir, zip):
        # zip each file one by one
        for dir in Path(dir).iterdir():
            for file in dir.iterdir():
                zip.write(file)

    def train_model(self):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.DL_computer.ip, username=self.DL_computer.login, password=self.DL_computer.pwd)
        stdin, stdout, stderr = client.exec_command('cd training; python3 train.py --model-dir=../'+self.temp_name+'/model ../'+self.temp_name)
        stdout.channel.recv_exit_status()
        lines = stdout.readlines()
        for line in lines:
            print(line)

#
# Main program
#
if __name__ == '__main__':
    # GUI
    app = QApplication([])
    gui = GUI_ai_nano()
    gui.show()
    app.exec_()
