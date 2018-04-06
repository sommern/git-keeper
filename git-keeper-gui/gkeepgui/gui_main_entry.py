import sys
from PyQt5.QtWidgets import QApplication

from gkeepgui.gui_main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    main_application = MainWindow()
    main_application.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()