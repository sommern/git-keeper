import sys

import os
from PyQt5.QtWidgets import QApplication

from gkeepclient.client_configuration import config
from gkeepclient.server_interface import server_interface
from gkeepgui.main_window import MainWindow


def main():

    app = QApplication(sys.argv)

    main_application = MainWindow()
    main_application.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
