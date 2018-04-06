import sys
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, \
    QComboBox, QPushButton, QLabel, QTableWidget, QMessageBox, \
    QAbstractItemView, QTableWidgetItem, QToolButton, QFileDialog, QApplication

from gkeepclient.client_configuration import config
from gkeepclient.server_interface import ServerInterfaceError
from gkeepgui.gui_configuration import gui_config
from gkeepgui.window_info import ClassWindowInfo, AssignmentTable, \
    StudentWindowInfo, AssignmentWindowInfo


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(50, 50, 1000, 1000)
        self.class_window_info = None
        self.show_class_window()

    def show_class_window(self):
        try:
            self.class_window_info = ClassWindowInfo()
        except ServerInterfaceError as e:
            error = e.__repr__()
            self.network_error_message(error)

        if self.class_window_info is not None:
            self.setCentralWidget(ClassWindow(self.class_window_info))

    def show_student_window(self, class_name: str, username:str):
        try:
            student_window_info = StudentWindowInfo(class_name, username)
            self.setCentralWidget(StudentWindow(student_window_info))
        except ServerInterfaceError as e:
            self.network_error_message(e)

    def show_assignment_window(self, class_name: str, assignment: str):
        try:
            assignment_window_info = AssignmentWindowInfo(class_name, assignment)
            self.setCentralWidget(AssignmentWindow(assignment_window_info))
        except ServerInterfaceError as e:
            self.network_error_message(e)

    def network_error_message(self, error):
        message_box = QMessageBox(self)
        message_box.setText(error)
        retry_button = message_box.addButton('Retry', QMessageBox.AcceptRole)
        close_button = message_box.addButton(QMessageBox.Close)
        message_box.show()
        message_box.exec()

        if message_box.clickedButton() == retry_button:
            try:
                self.class_window_info = ClassWindowInfo()
                message_box.close()
                message_box.destroy()
            except ServerInterfaceError as e:
                message_box.close()
                self.network_error_message(e.__repr__())

        if message_box.clickedButton() == close_button:
            message_box.close()
            self.close()


class ClassWindow(QWidget):
    def __init__(self, window_info: ClassWindowInfo):
        super().__init__()
        self.window_info = window_info

        self.setWindowTitle(window_info.title)

        self.layout = QVBoxLayout()
        self.toolbar_layout = QHBoxLayout()
        self.table_layout = QHBoxLayout()
        self.class_menu = QComboBox(self)

        self.refresh_button = QPushButton('Refresh')
        self.refresh_button.setFixedSize(80, 30)
        self.refresh_button.setCheckable(True)

        self.fetch_button = QPushButton('Fetch')
        self.fetch_button.setFixedSize(80, 30)
        self.fetch_button.setCheckable(True)

        self.description_text = QLabel()
        self.assignments_table = QTableWidget()
        self.submissions_table = QTableWidget()

        self.toolbar_layout.addWidget(self.class_menu, Qt.AlignLeft)
        self.toolbar_layout.addWidget(self.refresh_button, Qt.AlignRight)
        self.toolbar_layout.addWidget(self.fetch_button, Qt.AlignRight)
        self.toolbar_layout.insertStretch(1, 10)

        self.layout.addLayout(self.toolbar_layout)
        self.layout.addWidget(self.description_text)
        self.layout.addLayout(self.table_layout)

        self.setLayout(self.layout)

        self.create_class_menu()
        self.refresh_button.clicked.connect(self.refresh_button_clicked)
        self.fetch_button.clicked.connect(self.fetch_button_clicked)

    @pyqtSlot(bool)
    def refresh_button_clicked(self, checked: bool):

        if checked:
            self.refresh_button.setChecked(False)
            try:
                self.window_info.refresh()
            except ServerInterfaceError as e:
                self.close()
                self.parentWidget().network_error_message(e)

    @pyqtSlot(bool)
    def fetch_button_clicked(self, checked: bool):

        if checked:
            self.fetch_button.setChecked(False)
            assignment = self.window_info.current_assignment_table.current_assignment.name
            if assignment is not None:
                path = self.window_info.current_assignment_table.current_assignment.get_path_from_json()

                if path is None:
                    path = config.submissions_path

                    if path is None:
                        file_dialog = QFileDialog(self, Qt.Popup)
                        path = file_dialog.getExistingDirectory()

                if path is not None:
                    self.window_info.set_submissions_path(assignment, path)
            else:
                for assignment in self.window_info.current_class.get_assignment_list():
                    path = assignment.get_path_from_json()

                    if path is None:
                        path = config.submissions_path

                        if path is None:
                            file_dialog = QFileDialog(self, Qt.Popup)
                            path = file_dialog.getExistingDirectory()

                    if path is not None:
                        self.window_info.set_submissions_path(assignment, path)

            self.window_info.fetch()
            self.show_submissions_state()

    @pyqtSlot()
    def assignments_table_selection_changed(self):
        self.window_info.select_assignment(self.assignments_table.currentRow())
        self.show_submissions_table()

    @pyqtSlot()
    def submissions_table_selection_changed(self):
        self.window_info.select_submission(self.submissions_table.currentRow())

    def create_class_menu(self):
        self.class_menu.setFixedSize(100, 30)

        for a_class in self.window_info.class_list:
            self.class_menu.addItem(a_class.name)

        self.class_menu.setCurrentIndex(0)

        self.class_changed(0)
        self.class_menu.currentIndexChanged.connect(self.class_changed)

    @pyqtSlot(int)
    def class_changed(self, index: int):
        self.window_info.change_class(index)
        self.set_label()
        self.show_assignments_table()

    def set_label(self):
        self.description_text.setText(self.window_info.set_description())

    def show_assignments_table(self):
        info = self.window_info.current_assignment_table
        # self.assignments_table.setSortingEnabled(False)
        self.assignments_table.setRowCount(info.row_count)
        self.assignments_table.setColumnCount(info.col_count)
        index = 0

        for header in info.col_headers:
            self.assignments_table.setHorizontalHeaderItem(index, QTableWidgetItem(header))
            index += 1

        row_index = 0
        col_index = 0

        for row in info.rows_content:
            for col in row:
                self.assignments_table.setItem(row_index, col_index, QTableWidgetItem(col))
                col_index += 1

            col_index = 0
            row_index += 1

        self.assignments_table.setCornerButtonEnabled(False)
        self.assignments_table.resizeColumnsToContents()
        self.assignments_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        for row in range(self.assignments_table.rowCount()):
            for col in range(self.assignments_table.columnCount()):
                self.assignments_table.item(row, col).setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        self.assignments_table.setSortingEnabled(True)
        self.assignments_table.sortByColumn(0, Qt.AscendingOrder)
        self.table_layout.addWidget(self.assignments_table)
        self.assignments_table.itemSelectionChanged.connect(self.assignments_table_selection_changed)
        self.assignments_table.doubleClicked.connect(self.assignments_table_double_clicked)

    def show_submissions_table(self):
        info = self.window_info.current_submission_table
        self.table_layout.addWidget(self.submissions_table)

        if info is not None:
            self.submissions_table.setRowCount(info.row_count)
            self.submissions_table.setColumnCount(info.col_count)
            index = 0

            for header in info.col_headers:
                self.submissions_table.setHorizontalHeaderItem(index, QTableWidgetItem(header))
                index += 1

            row_index = 0
            col_index = 0

            for row in info.rows_content:
                for col in row:
                    self.submissions_table.setItem(row_index, col_index, QTableWidgetItem(col))
                    col_index += 1

                col_index = 0
                row_index += 1

            self.submissions_table.setSortingEnabled(True)
            self.submissions_table.sortByColumn(0, Qt.AscendingOrder)
            self.submissions_table.setCornerButtonEnabled(False)
            self.submissions_table.resizeColumnsToContents()
            self.submissions_table.setSelectionBehavior(QAbstractItemView.SelectRows)

            for row in range(self.submissions_table.rowCount()):
                for col in range(self.submissions_table.columnCount()):
                    self.submissions_table.item(row, col).setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

            self.submissions_table.horizontalHeader().sectionClicked.connect(self.sort)

            self.show_submissions_state()

            self.submissions_table.itemSelectionChanged.connect(self.submissions_table_selection_changed)
            self.submissions_table.doubleClicked.connect(self.submissions_table_double_clicked)
        else:
            self.submissions_table.hide()

    @pyqtSlot(int)
    def sort(self, col: int):
        self.show_submissions_state()

    def show_submissions_state(self):
        info = self.window_info.current_submission_table

        if info is not None:

            for row in range(self.submissions_table.rowCount()):
                username = self.submissions_table.item(row, 0).text()
                color = QColor(*gui_config.submission_color[info.row_color[username]])
                brush = QBrush(color)

                for col in range(self.submissions_table.rowCount()):
                    cell = self.submissions_table.item(row, col)
                    cell.setBackground(brush)


    @pyqtSlot()
    def assignments_table_double_clicked(self):
        self.close()
        self.parentWidget().show_assignments_table()

    @pyqtSlot()
    def submissions_table_double_clicked(self):
        self.close()
        self.parentWidget().show_submissions_table()


class StudentWindow(QWidget):
    def __init__(self, info: StudentWindowInfo):
        super().__init__()
        self.student_window_info = info
        self.setWindowTitle(self.student_window_info.title)
        self.layout = QVBoxLayout()
        self.buttons_layout = QHBoxLayout()
        self.back_button = QToolButton()
        self.back_button.setArrowType(Qt.LeftArrow)
        self.back_button.setCheckable(True)
        self.back_button.setFixedSize(30, 30)
        self.buttons_layout.addWidget(self.back_button, alignment=Qt.AlignLeft)
        self.label = QLabel(self.student_window_info.set_description())
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
        self.back_button.clicked.connect(self.back_button_clicked)

    @pyqtSlot(bool)
    def back_button_clicked(self, checked: bool):
        if checked:
            self.close()
            self.parentWidget().show_class_window()


class AssignmentWindow(QWidget):
    def __init__(self, info: AssignmentWindowInfo):
        super().__init__()
        self.assignment_window_info = info
        self.setWindowTitle(self.assignment_window_info.title)
        self.layout = QVBoxLayout()
        self.back_button = QToolButton()
        self.back_button.setArrowType(Qt.LeftArrow)
        self.back_button.setCheckable(True)
        self.back_button.setFixedSize(30, 30)
        self.layout.addWidget(self.back_button)
        self.setLayout(self.layout)
        self.back_button.clicked.connect(self.back_button_clicked)

    @pyqtSlot(bool)
    def back_button_clicked(self, checked: bool):
        if checked:
            self.close()
            self.parentWidget().show_class_window()
