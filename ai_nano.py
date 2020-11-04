# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUi
import random
import time, os
import pysftp
from pathlib import Path
from thread_camera import *
from thread_command import *
from record_images import record_images
from zipfile import ZipFile
import paramiko
import json
import tempfile


class Computer:
    def __init__(self, dico):
        self.pwd = dico['pwd']
        self.login = dico['login']
        self.ip = dico['ip']
        self.name = dico['name']

#
# Goal :
#
def zip_files_from_folder(dir, zip):
    # zip each file one by one
    for dir in Path(dir).iterdir():
        for file in dir.iterdir():
            zip.write(file)


class GUI_ai_nano(QWidget):
    """
    GUI
    """

    def __init__(self, parent=None):
        super().__init__()
        loadUi('ai_nano.ui', self)
        # Change font, colour of text entry box
        self.txt_log.setStyleSheet(
            """QPlainTextEdit {background-color: #333;
                               color: #00FF00;
                               font-size: 8;
                               font-family: Courier;}""")
        # Read the config file
        with open("config.json", "r") as read_file:
            self.config = json.load(read_file)
        self.DL_computer = Computer(self.config["DL_server"])
        self.nano_computers = []
        for dico in self.config["jetson_nano"]:
            self.nano_computers.append(Computer(dico))
            self.cb_nano_name.addItem(dico["name"])
        # Check if the models directory of the Nano is empty or not
        cnopts = pysftp.CnOpts(knownhosts='')  # Suppress authentication, VERY BAD
        cnopts.hostkeys = None
        nano_computer = self.nano_computers[0]
        sftp = pysftp.Connection(nano_computer.ip, username=nano_computer.login, password=nano_computer.pwd,cnopts=cnopts)
        models =  sftp.listdir('models')
        if models:  # There're some models on the Nano computer
            for m in models:
                self.cb_select_model.addItem(m)
            self.btn_inference.setEnabled(True)
            self.temp_name = models[0]  # we select the first one (but the user can replace it)
        sftp.close()
        # Definition of the threads
        self.thread_camera = Thread_Camera()
        self.thread_camera.signalAfficherImage.connect(self.display_image_from_camera)
        if self.thread_camera.sourceVideo and self.thread_camera.sourceVideo.isOpened():
            self.thread_camera.start()
        self.thread_command = Thread_Command()
        self.thread_command.display_msg_signal.connect(self.update_log)
        # Event handlers
        self.btn_working_space.clicked.connect(self.select_ws)
        self.sb_camera_id.valueChanged.connect(self.camera_changed)
        self.btn_project_ok.clicked.connect(self.create_project)
        self.btn_split_image.clicked.connect(self.split_images)
        self.btn_upload_to_dl.clicked.connect(self.upload_to_dl)
        self.btn_train_model.clicked.connect(self.train_model)
        self.btn_convert_onnx.clicked.connect(self.convert_to_onnx)
        self.btn_upload_to_nano.clicked.connect(self.upload_to_nano)
        self.btn_inference.clicked.connect(self.inference)
        self.cb_select_model.currentIndexChanged.connect(self.change_model)

    def change_model(self):
        self.temp_name = self.cb_select_model.currentText()

    def select_ws(self):
        self.ws = Path(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if len(os.listdir(self.ws)) > 0:  # Directory not empty
            self.btn_upload_to_dl.setEnabled(True)
        self.update_log('Selection of {} as working directory'.format(self.ws))

    def camera_changed(self):
        self.thread_camera.changeCamera(self.sb_camera_id.value())

    def display_image_from_camera(self, img):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        (height, width, _) = img.shape
        mQImage = QImage(img, width, height, QImage.Format_RGB888)
        pix = QPixmap.fromImage(mQImage)
        self.lbl_image.setPixmap(pix)

    def create_project(self):
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
            ri = record_images(self.ws, self.thread_camera)
            self.vl_record.addWidget(ri)
        self.update_log('Project creation')
        self.gb_recording.setEnabled(True)
        self.btn_split_image.setEnabled(True)

    def split_images(self):
        # Creation of the labels.txt file
        lst_labels = []
        for cat_dir in (self.ws / 'images').iterdir():
            category = cat_dir.name
            lst_labels.append(category)
            files = [f for f in cat_dir.iterdir()]
            random.shuffle(files)
            ind_80 = int(len(files) * 0.8)  # 80 %
            ind_10 = int(len(files) * 0.1)  # 10 %
            self.split(files[:ind_80], 'train', category)
            self.split(files[ind_80:ind_80 + ind_10], 'val', category)
            self.split(files[ind_80 + ind_10:], 'test', category)
        labels_file = open(str(self.ws / 'labels.txt'), 'w')
        lst_labels.sort()
        for l in lst_labels:
            labels_file.write(l + '\n')
        labels_file.close()
        self.update_log('Images split to train, val and test directories')
        self.btn_upload_to_dl.setEnabled(True)

    def split(self, files, dir_name, category):
        the_path = self.ws / dir_name / category
        for f in files:
            f.replace(the_path / f.name)

    def upload_to_dl(self):
        self.update_log('begin : upload to DL machine')
        os.chdir(str(self.ws))  # we work in the ws directory to zip relative (and not absolute) files
        with ZipFile('data.zip', 'w') as zip:
            # writing each file one by one
            zip_files_from_folder('train', zip)
            zip_files_from_folder('val', zip)
            zip_files_from_folder('test', zip)
            zip.write('labels.txt')  # and finally 'labels.txt'
        self.update_log('ZIP done')
        # Now, we can upload the ZIP file to DL machine
        cnopts = pysftp.CnOpts(knownhosts='')  # Suppress authentication, VERY BAD
        cnopts.hostkeys = None
        sftp = pysftp.Connection(self.DL_computer.ip, username=self.DL_computer.login, password=self.DL_computer.pwd,cnopts=cnopts)
        self.temp_name = next(tempfile._get_candidate_names())  # Generate a temporary name for the remote directory that we must create on DL machine
        self.cb_select_model.addItem(self.temp_name)  # Add this model to the list of models
        self.cb_select_model.setCurrentText(self.temp_name) # and select it
        self.update_log("On DL, creation of the {} directory".format(self.temp_name))
        sftp.mkdir('TP_IA_NANO/models/'+self.temp_name)
        with sftp.cd('TP_IA_NANO/models/'+self.temp_name):
            sftp.put('data.zip')
        sftp.close()
        # Unzip data on DL machine
        self.exec_cmd(self.DL_computer, 'cd TP_IA_NANO/models/' + self.temp_name + ';unzip data.zip','Unzip done on DL machine')
        self.update_log('End : ZIP file uploaded and extracted to DL machine')
        self.btn_train_model.setEnabled(True)

    def train_model(self):
        self.update_log("Begin training model")
        self.exec_cmd(self.DL_computer,'cd TP_IA_NANO; python3 train.py --model-dir=models/' + self.temp_name + '/model models/' + self.temp_name,'End training model')
        self.btn_convert_onnx.setEnabled(True)

    def convert_to_onnx(self):
        # Now convert the model to a ONNX model
        self.update_log("Begin conversion to ONNX.")
        self.exec_cmd(self.DL_computer,'cd TP_IA_NANO; python3 onnx_export.py --model-dir=models/' + self.temp_name + '/model','End conversion to ONNX file')
        self.btn_upload_to_nano.setEnabled(True)

    def upload_to_nano(self):
        self.update_log("Begin upload ONNX model to Jetson Nano.")
        # Get model from DL machine with SFTP
        cnopts = pysftp.CnOpts(knownhosts='')  # Suppress authentication, VERY BAD
        cnopts.hostkeys = None
        sftp = pysftp.Connection(self.DL_computer.ip, username=self.DL_computer.login, password=self.DL_computer.pwd,cnopts=cnopts)
        with sftp.cd('TP_IA_NANO/models/'+self.temp_name):
            sftp.get('model/resnet18.onnx')
        sftp.close()
        self.update_log('Getting ONNX file')
        # Put model on nano machine with SFTP
        nano_computer = self.nano_computers[self.cb_nano_name.currentIndex()]
        sftp = pysftp.Connection(nano_computer.ip, username=nano_computer.login, password=nano_computer.pwd,cnopts=cnopts)
        sftp.mkdir('models/'+self.temp_name)
        with sftp.cd('models/'+self.temp_name):
            sftp.put('resnet18.onnx')
            sftp.put('labels.txt')
        sftp.close()
        self.update_log('End upload ONNX model to Jetson Nano.')
        self.btn_inference.setEnabled(True)

    def inference(self):
        self.update_log("Begin inference. It may take a long time. Be patient.")
        nano_computer = self.nano_computers[self.cb_nano_name.currentIndex()]
        cmd = 'cd jetson-inference/python/examples; ./my-imagenet.py --log-level=info --headless --camera=/dev/video0 '
        cmd += '--model=/home/nano/models/' + self.temp_name + '/resnet18.onnx --input_blob=input_0 --output_blob=output_0 '
        cmd += '--labels=/home/nano/models/' + self.temp_name + '/labels.txt'
        self.exec_cmd(nano_computer, cmd, 'Starting inference')

    def exec_cmd(self, computer, cmd, msg):
        self.thread_command.exec_command(computer, cmd, msg)

    def update_log(self, txt):
        self.txt_log.appendPlainText(txt)


#
# Main program
#
if __name__ == '__main__':
    # GUI
    app = QApplication([])
    gui = GUI_ai_nano()
    gui.show()
    app.exec_()
