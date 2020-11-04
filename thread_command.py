# -*- coding: utf-8 -*-

from PyQt5.QtCore import *
import paramiko
import time


class Thread_Command(QThread):

    display_msg_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super(Thread_Command, self).__init__(parent)

    def exec_command(self,computer,cmd,end_msg):
        self.computer = computer
        self.cmd = cmd
        self.end_msg = end_msg
        self.start()

    def run(self):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.computer.ip, username=self.computer.login, password=self.computer.pwd)
        stdin, stdout, stderr = client.exec_command(self.cmd, get_pty=True)
        for line in stdout:
            txt = line.rstrip()
            self.display_msg_signal.emit(txt)
        for line in stderr:
            txt = line.rstrip()
            self.display_msg_signal.emit(txt)
        client.close()
        self.display_msg_signal.emit(self.end_msg)

