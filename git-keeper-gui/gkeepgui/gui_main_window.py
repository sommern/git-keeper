"""
Provides a graphical user interface for viewing classes, assignments,
submissions and fetching submissions from students.
"""

import os
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, \
    QComboBox, QPushButton, QLabel, QTableWidget, QMessageBox, \
    QAbstractItemView, QTableWidgetItem, QToolButton, QFileDialog

from gkeepclient.client_configuration import config
from gkeepclient.server_interface import ServerInterfaceError
from gkeepgui.gui_configuration import gui_config
from gkeepgui.gui_exception import GuiFileException

from gkeepgui.window_info import ClassWindowInfo, \
    StudentWindowInfo, AssignmentWindowInfo


class MainWindow(QMainWindow):
    """
    Draws the main window and provides three views for class, assignment, and
    student.

    Displays the popup error message if a ServerInterfaceError is raised.
    """

    def __init__(self):
        """
        Constructor.

        Set the geometry of the window. Set the class view as the central
        widget.
        """

        super().__init__()
        self.setGeometry(50, 50, 1000, 1000)
        self.class_window_info = None
        self.setAttribute(Qt.WA_QuitOnClose)
        self.show()
        self.show_class_window()

    def show_class_window(self):
        """
        Set the class view as the central widget. Store ClassWindowInfo as an
        attribute. Display the popup error message if a ServerInterfaceError
        is raised.

        :return: none
        """

        try:
            self.class_window_info = ClassWindowInfo()
        except ServerInterfaceError as e:
            error = e.__repr__()
            self.network_error_message(error)
        except GuiFileException as e:
            self.missing_dir_message(e.get_path())

        if self.class_window_info is not None:
            self.setCentralWidget(ClassWindow(self.class_window_info))

    def show_student_window(self, class_name: str, username: str):
        """
        Set the student view as the central widget.
        Display the popup error message if a ServerInterfaceError
        is raised.

        :param class_name: name of the class
        :param username: username of the student

        :return: none
        """

        try:
            student_window_info = StudentWindowInfo(class_name, username)
            self.setCentralWidget(StudentWindow(student_window_info))
        except ServerInterfaceError as e:
            self.network_error_message(e)

    def show_assignment_window(self, class_name: str, assignment: str):
        """
        Set the assignment view as the central widget.
        Display the popup error message if a ServerInterfaceError
        is raised.

        :param class_name: name of the class
        :param assignment: name of the assignment
        :return: none
        """
        try:
            assignment_window_info = AssignmentWindowInfo(class_name,
                                                          assignment)
            self.setCentralWidget(AssignmentWindow(assignment_window_info))
        except ServerInterfaceError as e:
            self.network_error_message(e)

    def network_error_message(self, error):
        """
        Display the popup error message.
        Try to connect if press Retry.
        Quit if press close.

        :param error: content of the error message
        :return: none
        """
        message_box = QMessageBox()
        message_box.setText(error)
        retry_button = message_box.addButton('Retry', QMessageBox.AcceptRole)
        close_button = message_box.addButton(QMessageBox.Close)
        message_box.show()
        message_box.exec()

        if message_box.clickedButton() == retry_button:
            try:
                self.class_window_info = ClassWindowInfo()
            except ServerInterfaceError as e:
                message_box.close()
                self.network_error_message(e.__repr__())

        if message_box.clickedButton() == close_button:
            self.hide()

    def missing_dir_message(self, path):
        message_box = QMessageBox(self)
        message_box.setText('Path from submissions_path.json does not '
                            'exist: {}'.format(path))
        # message_box.setDetailedText('Remove path from JSON file?')
        close_button = message_box.addButton(QMessageBox.Close)
        message_box.show()
        message_box.exec()

        if message_box.clickedButton() == close_button:
            self.hide()


class ClassWindow(QWidget):
    """
    Provides the widget and functionality for viewing classes, assignments,
    submissions.
    """

    def __init__(self, window_info: ClassWindowInfo):
        """
        Constructor.

        Set the attributes for the widget and creates layouts, labels, and
        buttons.

        :param window_info: ClassWindowInfo object storing information for
        making the window
        """

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
        """
        PyQT slot for the signal emitted when the refresh button is clicked.
        Refresh the window and update information.

        :param checked: True if refresh button is clicked, False otherwise
        :return: none
        """

        if checked:
            self.refresh_button.setChecked(False)
            try:
                self.window_info.refresh()
                self.show_assignments_table()
                self.show_submissions_table()
                self.show_submissions_state()
            except ServerInterfaceError as e:
                self.close()
                self.parentWidget().network_error_message(e)

    @pyqtSlot(bool)
    def fetch_button_clicked(self, checked: bool):
        """
        PyQT slot for the signal emitted when the fetch button is clicked.
        Grab the path from the json file. If the path is not in there, look
        for it in ClientConfiguration. Otherwise, display the popup file
        dialog for the user to choose which directory to fetch to.

        Fetch the selected assignment, or fetch all if no assignment is
        selected.

        Display the popup error message if the directory at the given path
        does not exist.

        Change the submissions table to reflect the new fetching state and
        information.

        :param checked: True if fetch button is clicked, False otherwise
        :return: none
        """

        if checked:
            self.fetch_button.setChecked(False)
            assignment = \
                self.window_info.current_assignments_table.current_assignment

            if assignment is not None:
                path = assignment.get_path_from_json()

                if path is None:
                    path = config.submissions_path

                    if path is None:
                        file_dialog = QFileDialog(self, Qt.Popup)
                        path = file_dialog.getExistingDirectory()

                        if path == '':
                            path = None

                if path is not None:
                    self.window_info.set_submissions_path(assignment.name,
                                                          path)
                    try:
                        self.window_info.fetch()
                    except GuiFileException as e:
                        self.no_dir_message(e.get_path())

            else:
                for assignment in \
                        self.window_info.current_class.get_assignment_list():
                    path = assignment.get_path_from_json()

                    if path is None:
                        path = config.submissions_path

                        if path is None:
                            file_dialog = QFileDialog(self, Qt.Popup)
                            path = file_dialog.getExistingDirectory()

                            if path == '':
                                path = None

                    if path is not None:
                        self.window_info.set_submissions_path(assignment, path)

                        try:
                            self.window_info.fetch()
                        except GuiFileException as e:
                            self.no_dir_message(e.get_path())

            self.refresh_button_clicked(True)

    def no_dir_message(self, path):
        """
        Display the popup message for directory not found. Ask to create the
        directory.

        :param path: path of directory
        :return: none
        """

        message_box = QMessageBox(self)
        message_box.setText(path + ' does not exist. Create it now?')
        yes_button = message_box.addButton('Yes', QMessageBox.YesRole)
        no_button = message_box.addButton('No', QMessageBox.NoRole)
        message_box.setDefaultButton(yes_button)
        message_box.exec()

        if message_box.clickedButton() == yes_button:
            os.makedirs(path)
            self.window_info.fetch()
        else:
            message_box.hide()
            message_box.close()
            self.refresh_button_clicked(True)


    @pyqtSlot()
    def assignments_table_selection_changed(self):
        """
        PyQT slot for the signal emitted when row selection in the assignments
        table changes. This includes the case where no row is selected.

        Show the corresponding submissions table or hide submissions table if
        no row is selected.

        :return: none
        """
        current_row = self.assignments_table.currentRow()

        if self.assignments_table.item(current_row, 0).isSelected():
            self.window_info.select_assignment(
                self.assignments_table.currentRow())

            self.show_submissions_table()
        else:
            self.window_info.select_submission(None)
            self.submissions_table.hide()
            self.table_layout.removeWidget(self.submissions_table)
            self.submissions_table.destroy()

    @pyqtSlot()
    def submissions_table_selection_changed(self):
        """
        PyQT slot for the signal emitted when row selection in the submissions
        table changes. This includes the case where no row is selected.

        :return: none
        """
        self.window_info.select_submission(self.submissions_table.currentRow())

    def create_class_menu(self):
        """
        Create the class menu and select the current class to the first class
        in the list.

        :return: none
        """
        self.class_menu.setFixedSize(100, 30)

        for a_class in self.window_info.class_list:
            self.class_menu.addItem(a_class.name)

        self.class_menu.setCurrentIndex(0)

        self.class_changed(0)
        self.class_menu.currentIndexChanged.connect(self.class_changed)

    @pyqtSlot(int)
    def class_changed(self, index: int):
        """
        PyQT slot for the signal emitted when the current class is changed in
        the class menu.

        Change the content of the assignments and submissions table and the
        description text accordingly.

        :param index: index of the new class
        :return: none
        """

        self.window_info.change_class(index)
        self.set_label()
        self.show_assignments_table()

    def set_label(self):
        """
        Set the description text for the current class.

        :return: none
        """

        self.description_text.setText(self.window_info.set_description())

    def show_assignments_table(self):
        """
        Draw the assignments table for the current class.

        :return: none
        """

        self.assignments_table.destroy()
        self.assignments_table.hide()
        self.table_layout.removeWidget(self.assignments_table)
        self.assignments_table = QTableWidget()
        info = self.window_info.current_assignments_table
        self.assignments_table.setRowCount(info.row_count)
        self.assignments_table.setColumnCount(info.col_count)
        index = 0

        for header in info.col_headers:
            header_item = QTableWidgetItem(header)
            self.assignments_table.setHorizontalHeaderItem(index, header_item)
            index += 1

        row_index = 0
        col_index = 0

        # set the contents of the table
        for row in info.rows_content:
            for col in row:
                self.assignments_table.setItem(row_index,
                                               col_index,
                                               QTableWidgetItem(col))
                col_index += 1

            col_index = 0
            row_index += 1

        self.assignments_table.setCornerButtonEnabled(False)
        self.assignments_table.resizeColumnsToContents()

        # set the selection mode to single row only
        self.submissions_table.setSelectionMode(
            QAbstractItemView.SingleSelection)
        self.assignments_table.setSelectionBehavior(
            QAbstractItemView.SelectRows)

        # set the flags of each cell so that they are selectable
        for row in range(self.assignments_table.rowCount()):
            for col in range(self.assignments_table.columnCount()):
                self.assignments_table.item(row, col).setFlags(
                    Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        # sort the table when the header is clicked
        self.assignments_table.horizontalHeader().sectionClicked.connect(
            self.sort_assignments_table)

        self.table_layout.addWidget(self.assignments_table)
        self.assignments_table.itemSelectionChanged.connect(
            self.assignments_table_selection_changed)

        # automatically select the first row
        self.assignments_table.selectRow(0)

        self.assignments_table.doubleClicked.connect(
            self.assignments_table_double_clicked)

    def show_submissions_table(self):
        """
        Draw the submissions table for the selected assignment.

        :return: none
        """
        self.submissions_table.destroy()
        self.submissions_table.hide()
        self.table_layout.removeWidget(self.submissions_table)
        self.submissions_table = QTableWidget()
        info = self.window_info.current_submissions_table
        self.table_layout.addWidget(self.submissions_table)

        if info is not None: # check if there is a current submissions table
            self.submissions_table.setRowCount(info.row_count)
            self.submissions_table.setColumnCount(info.col_count)
            index = 0

            for header in info.col_headers:
                self.submissions_table.setHorizontalHeaderItem(
                    index, QTableWidgetItem(header))
                index += 1

            current_order = info.sorting_order

            # ascending order
            if current_order[1] == 0:
                symbol = '▲'
            else:
                symbol = '▼'

            col_name = '{} {}'.format(
                self.submissions_table.horizontalHeaderItem(
                    current_order[0]).text(), symbol)
            self.submissions_table.setHorizontalHeaderItem(current_order[0],
                                          QTableWidgetItem(col_name))

            row_index = 0
            col_index = 0

            # set the contents of the table
            for row in info.rows_content:
                for col in row:
                    self.submissions_table.setItem(row_index, col_index,
                                                   QTableWidgetItem(col))
                    col_index += 1

                col_index = 0
                row_index += 1

            self.submissions_table.setCornerButtonEnabled(False)
            self.submissions_table.resizeColumnsToContents()

            # set the selection mode to single row only
            self.submissions_table.setSelectionMode(
                QAbstractItemView.SingleSelection)
            self.submissions_table.setSelectionBehavior(
                QAbstractItemView.SelectRows)

            # set each cell to be selectable
            for row in range(self.submissions_table.rowCount()):
                for col in range(self.submissions_table.columnCount()):
                    self.submissions_table.item(row, col).setFlags(
                        Qt.ItemIsSelectable | Qt.ItemIsEnabled)

            # sort the table when clicking on the header
            self.submissions_table.horizontalHeader().sectionClicked.connect(
                self.sort_submissions_table)

            self.show_submissions_state()

            self.submissions_table.itemSelectionChanged.connect(
                self.submissions_table_selection_changed)
            self.submissions_table.doubleClicked.connect(
                self.submissions_table_double_clicked)
        else:
            self.submissions_table.hide()

    @pyqtSlot(int)
    def sort_submissions_table(self, col: int):
        """
        PyQT slot for signal emitted when clicking on a column's header.
        Sort column.

        :param col: index of selected column
        :return: none
        """
        current_order = self.window_info.change_submissions_sorting_order(col)
        table = self.submissions_table

        self.show_submissions_table()

    @pyqtSlot(int)
    def sort_assignments_table(self, col: int):
        """


        :param col:
        :return:
        """
        self.window_info.change_assignments_sorting_order(col)
        self.show_assignments_table()

    def show_submissions_state(self):
        info = self.window_info.current_submissions_table

        if info is not None:

            for row in range(self.submissions_table.rowCount()):
                username = self.submissions_table.item(row, 0).text()
                color = QColor(*gui_config.submission_color[info.row_color[username]])
                brush = QBrush(color)

                for col in range(self.submissions_table.columnCount()):
                    cell = self.submissions_table.item(row, col)
                    cell.setBackground(brush)


    @pyqtSlot()
    def assignments_table_double_clicked(self):
        self.close()
        self.parentWidget().show_assignment_window(self.window_info.current_class.name,
                                                   self.window_info.current_assignments_table.current_assignment)

    @pyqtSlot()
    def submissions_table_double_clicked(self):
        self.close()
        self.parentWidget().show_student_window(self.window_info.current_class.name, self.window_info.current_submissions_table.current_student.username)


class StudentWindow(QWidget):
    def __init__(self, info: StudentWindowInfo):
        super().__init__()

        try:
            self.student_window_info = info
        except ServerInterfaceError as e:
            pass

        self.setWindowTitle(self.student_window_info.title)
        self.layout = QVBoxLayout()
        self.buttons_layout = QHBoxLayout()
        self.back_button = QToolButton()
        self.back_button.setArrowType(Qt.LeftArrow)
        self.back_button.setCheckable(True)
        self.back_button.setFixedSize(30, 30)
        self.buttons_layout.addWidget(self.back_button, alignment=Qt.AlignLeft)
        self.label = QLabel(self.student_window_info.set_description())
        self.layout.addLayout(self.buttons_layout)
        self.layout.addWidget(self.label, alignment=Qt.AlignTop)
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
        self.layout.addWidget(self.back_button, alignment=Qt.AlignTop)
        self.setLayout(self.layout)
        self.back_button.clicked.connect(self.back_button_clicked)

    @pyqtSlot(bool)
    def back_button_clicked(self, checked: bool):
        if checked:
            self.close()
            self.parentWidget().show_class_window()
