import sys

import os
from PyQt5.QtWidgets import QApplication

from gkeepclient.client_configuration import config
from gkeepclient.server_interface import server_interface
from gkeepgui.main_window import MainWindow

if __name__ == '__main__':

    path = os.path.expanduser(
        '~/git-keeper/tests/vagrant/faculty_gkeep_configs/faculty_one.cfg')
    config.set_config_path(path)
    config.parse()
    server_interface.connect()


    app = QApplication(sys.argv)

    main_application = MainWindow()
    main_application.show()

    sys.exit(app.exec_())