import sys

import os

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QApplication, QMessageBox

from gkeepclient.client_configuration import config
from gkeepclient.server_interface import server_interface, ServerInterfaceError


class GlobalInfo:

    def __init__(self):
        if len(sys.argv) < 2:
            path = os.path.expanduser('~/.config/git-keeper/client.cfg')
        else:
            path = os.path.expanduser(sys.argv[1])

        config.set_config_path(path)
        config.parse()
        self.error_signal = pyqtSignal()
        self._connected = False

    def refresh(self):
        self.info = server_interface.get_info(freshness_threshold=0)

    def connect(self):
        server_interface.connect()
        self._connected = True
        self.refresh()

    def is_connected(self):
        return self._connected


global_info = GlobalInfo()