import sys
from PyQt5.QtWidgets import QApplication

from gkeepgui.gui_main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    main_application = MainWindow()

    if main_application.isHidden():
        sys.exit(0)

    sys.exit(app.exec_())


def print1():
    print(1)

if __name__ == '__main__':
    main()