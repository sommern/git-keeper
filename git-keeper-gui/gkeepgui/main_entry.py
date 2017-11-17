import sys

import os
from PyQt5.QtWidgets import QApplication

from gkeepclient.client_configuration import config
from gkeepclient.server_interface import server_interface
from gkeepgui.main_window import MainWindow

def main():
    path = os.path.expanduser(
        '~/.config/git-keeper/client.cfg')
    config.set_config_path(path)
    config.parse()
    server_interface.connect()


    app = QApplication(sys.argv)

    main_application = MainWindow()
    main_application.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
