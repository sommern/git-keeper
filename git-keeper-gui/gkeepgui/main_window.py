import json
from json import load

import os
from PyQt5.QtCore import Qt, pyqtSlot, QModelIndex
from PyQt5.QtGui import QBrush, qGreen, qRed, QColor
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, \
    QPushButton, QTableWidgetItem, QTableWidget, QToolButton, QComboBox, \
    QLabel, QAbstractItemView, QFileDialog

from gkeepclient import fetch_submissions
from gkeepclient.client_configuration import config
from gkeepclient.fetch_submissions import FetchedHashCache
from gkeepclient.server_interface import server_interface
from gkeepcore.git_commands import git_head_hash
from gkeepgui.global_info import global_info


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()
        self.setGeometry(50, 50, 1000, 1000)
        self.show_class_window()

    def show_class_window(self):
        self.setCentralWidget(ClassWindow())

    def show_student_window(self, class_name: str, username: str):
        self.setCentralWidget(StudentWindow(class_name, username))

    def show_assignment_window(self, class_name: str, assignment: str):
        self.setCentralWidget(AssignmentWindow(class_name, assignment))


class ClassWindow(QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle('Classes')

        self.layout = QVBoxLayout()
        self.toolbarLayout = QHBoxLayout()
        self.tableLayout = QHBoxLayout()
        self.classDetails = QVBoxLayout()
        self.classMenu = QComboBox(self)

        self.refreshButton = QPushButton('Refresh', self)
        self.refreshButton.setFixedSize(80, 30)
        self.refreshButton.setCheckable(True)

        self.fetchButton = QPushButton('Fetch', self)
        self.fetchButton.setFixedSize(80, 30)
        self.fetchButton.setCheckable(True)

        self.studentText = QLabel(self)
        self.assignmentText = QLabel(self)
        self.studentTable = QTableWidget(self)
        self.assignmentTable = QTableWidget(self)

        self.toolbarLayout.addWidget(self.classMenu, Qt.AlignLeft)
        self.toolbarLayout.addWidget(self.refreshButton, Qt.AlignRight)
        self.toolbarLayout.addWidget(self.fetchButton,Qt.AlignRight)
        self.toolbarLayout.insertStretch(1, 10)

        self.layout.addLayout(self.toolbarLayout)
        self.layout.addLayout(self.classDetails)
        self.layout.addLayout(self.tableLayout)

        self.setLayout(self.layout)

        self.infoDict = global_info.info
        self.refreshButton.clicked.connect(self.refresh_button_clicked)
        self.fetchButton.clicked.connect(self.fetch_button_clicked)

        self.drop_down_class_menu()

    def class_details(self, class_name):

        self.studentText.destroy()
        self.assignmentText.destroy()
        student_count = self.infoDict.student_count(class_name)
        self.studentText.setText('Number of Students: {0}'.format(student_count))
        assignment_count = self.infoDict.assignment_count(class_name)
        self.assignmentText.setText('Number of Assignments: {0}'.format(assignment_count))
        self.classDetails.addWidget(self.studentText)
        self.classDetails.addWidget(self.assignmentText)


    def drop_down_class_menu(self):
        self.classMenu.setFixedSize(100, 30)
        for aClass in self.infoDict.class_list():
            self.classMenu.addItem(aClass)

        self.classMenu.setCurrentIndex(0)

        self.class_changed(self.classMenu.itemText(0))
        self.classMenu.currentTextChanged.connect(self.class_changed)

    @pyqtSlot(bool)
    def refresh_button_clicked(self, checked: bool):
        if checked:
            self.refreshButton.setChecked(False)
            global_info.refresh()
            self.infoDict = global_info.info
            self.student_table(self.classMenu.currentText())
            self.assignment_table(self.classMenu.currentText())
            self.show_submissions()

    @pyqtSlot(bool)
    def fetch_button_clicked(self, checked: bool):
        if checked:
            self.fetchButton.setChecked(False)
            selected_items = self.assignmentTable.selectedItems()

            if len(selected_items) is not None:
                class_name = self.classMenu.currentText()
                assignment = selected_items[0].text()
                json_path = os.path.expanduser('~/.config/submissions_path.json')

                if not os.path.isfile(json_path):
                    with open(json_path, 'w'):
                        pass

                if os.path.getsize(json_path) > 0:
                    with open(json_path, 'r') as f:
                        paths = json.load(f)
                else:
                    paths = {}

                if assignment in paths.keys():
                    submissions_path = paths[assignment]
                elif config.submissions_path is not None:
                    submissions_path = config.submissions_path
                    paths[assignment] = submissions_path
                else:
                    explorer = QFileDialog(self, Qt.Popup)
                    submissions_path = explorer.getExistingDirectory()
                    paths[assignment] = submissions_path

                with open(json_path, 'w') as f:
                    json.dump(paths, f)

                fetch_submissions.fetch_submissions(class_name, assignment, submissions_path)
                self.show_submissions()


    @pyqtSlot(str)
    def class_changed(self, class_name):
        self.class_details(class_name)
        self.student_table(class_name)
        self.assignment_table(class_name)

    def student_table(self, class_name: str):

        self.studentTable.destroy()
        self.studentTable.setSortingEnabled(False)
        self.studentTable.setRowCount(self.infoDict.student_count(class_name))
        self.studentTable.setColumnCount(4)
        self.studentTable.setHorizontalHeaderItem(0, QTableWidgetItem(
            'First name'))
        self.studentTable.setHorizontalHeaderItem(1, QTableWidgetItem(
            'Last name'))
        self.studentTable.setHorizontalHeaderItem(2,
                                                  QTableWidgetItem('Username'))
        self.studentTable.setHorizontalHeaderItem(3, QTableWidgetItem('Average Submission Count'))

        row = 0

        for username in self.infoDict.student_list(class_name):
            first = self.infoDict.student_first_name(class_name, username)
            last = self.infoDict.student_last_name(class_name, username)
            average_submission = self.infoDict.average_student_submission_count(class_name, username)
            self.studentTable.setItem(row, 0, QTableWidgetItem(first))
            self.studentTable.setItem(row, 1, QTableWidgetItem(last))
            self.studentTable.setItem(row, 2, QTableWidgetItem(username))
            self.studentTable.setItem(row, 3, QTableWidgetItem('%.2f' % average_submission))

            row += 1

        self.studentTable.setCornerButtonEnabled(False)
        self.studentTable.resizeColumnsToContents()
        self.studentTable.setSelectionBehavior(QAbstractItemView.SelectRows)

        for row in range(self.studentTable.rowCount()):
            for column in range(self.studentTable.columnCount()):
                cell = self.studentTable.item(row, column)
                cell.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                cell.setSelected(False)

        self.studentTable.setSortingEnabled(True)
        self.studentTable.sortByColumn(0, Qt.DescendingOrder)
        self.tableLayout.addWidget(self.studentTable)
        self.studentTable.doubleClicked.connect(self.student_double_clicked)

    def assignment_table(self, class_name: str):
        self.assignmentTable.destroy()
        self.assignmentTable.setSortingEnabled(False)
        self.assignmentTable.setRowCount(self.infoDict.assignment_count(class_name))
        self.assignmentTable.setColumnCount(2)
        self.assignmentTable.setHorizontalHeaderItem(0, QTableWidgetItem('Assignment Name'))
        self.assignmentTable.setHorizontalHeaderItem(1, QTableWidgetItem('Students Submitted'))

        row = 0

        for assignment in self.infoDict.assignment_list(class_name):
            self.assignmentTable.setItem(row, 0, QTableWidgetItem(assignment))
            self.assignmentTable.setItem(row, 1, QTableWidgetItem(str(
                self.infoDict.student_submitted_count(class_name,
                                                 assignment))))

            row += 1

        self.assignmentTable.setCornerButtonEnabled(False)
        self.assignmentTable.resizeColumnsToContents()
        self.assignmentTable.setSelectionBehavior(QAbstractItemView.SelectRows)

        for row in range(self.assignmentTable.rowCount()):
            for col in range (self.assignmentTable.columnCount()):
                self.assignmentTable.item(row, col).setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        self.assignmentTable.setSortingEnabled(True)
        self.assignmentTable.sortByColumn(0, Qt.DescendingOrder)
        self.tableLayout.addWidget(self.assignmentTable)
        self.assignmentTable.itemSelectionChanged.connect(self.show_submissions)
        self.assignmentTable.doubleClicked.connect(self.assignment_double_clicked)

    @pyqtSlot(QModelIndex)
    def student_double_clicked(self, index: QModelIndex):

        selected_cells = self.studentTable.selectedItems()
        parent_widget = self.parentWidget()
        self.destroy()
        parent_widget.show_student_window(self.classMenu.currentText(), selected_cells[2].text())

    @pyqtSlot(QModelIndex)
    def assignment_double_clicked(self, index: QModelIndex):
        
        selected_cells = self.assignmentTable.selectedItems()
        parent_widget = self.parentWidget()
        self.destroy()
        parent_widget.show_assignment_window(self.classMenu.currentText(), selected_cells[0].text())

    @pyqtSlot()
    def show_submissions(self):

        for row in range(self.studentTable.rowCount()):
            for col in range(self.studentTable.columnCount()):
                cell = self.studentTable.item(row, col)
                cell.setBackground(QBrush(Qt.white))
                cell.setSelected(False)

        if len(self.assignmentTable.selectedItems()) != 0:
            green = QColor(208, 240, 192)
            red = QColor(255, 192, 203)
            blue = QColor(240, 248, 255)
            red_brush = QBrush(red)
            green_brush = QBrush(green)
            blue_brush = QBrush(blue)
            selected_cells = self.assignmentTable.selectedItems()
            class_name = self.classMenu.currentText()
            assignment = selected_cells[0].text()


            for row in range(self.studentTable.rowCount()):
                username = self.studentTable.item(row, 2).text()
                submission = self.infoDict.student_submission_count(class_name, assignment, username)
                for col in range(self.studentTable.columnCount()):
                    current_cell = self.studentTable.item(row, col)
                    json_path = os.path.expanduser('~/.config/submissions_path.json')

                    if os.path.isfile(json_path):
                        with open(json_path, 'r') as f:
                            paths = json.load(f)

                        if assignment in paths.keys():
                            student_submission_path = os.path.join(paths[assignment], assignment, 'submissions', self.infoDict.student_last_first_username(class_name, username))
                            print(student_submission_path)
                            cache = FetchedHashCache(student_submission_path)
                            if cache.is_cached(student_submission_path):
                                local_hash = cache.get_hash(student_submission_path)
                            else:
                                local_hash = git_head_hash(student_submission_path)
                                cache.set_hash(student_submission_path,local_hash)

                    server_hash = self.infoDict.student_assignment_hash(class_name, assignment, username)

                    if submission == 0:
                        current_cell.setBackground(red_brush)
                    elif local_hash != server_hash:
                        current_cell.setBackground(blue_brush)
                    else:
                        current_cell.setBackground(green_brush)


class StudentWindow(QWidget):

    def __init__(self, class_name: str, username: str):

        super().__init__()

        self.class_name = class_name
        self.username = username

        self.setWindowTitle('Student')
        self.layout = QVBoxLayout()
        self.studentDetails = QVBoxLayout()

        self.buttonLayout = QHBoxLayout()
        self.backButton = QToolButton(self)
        self.backButton.setArrowType(Qt.LeftArrow)
        self.backButton.setCheckable(True)
        self.backButton.setFixedSize(30, 30)
        self.buttonLayout.addWidget(self.backButton, alignment=Qt.AlignLeft)
        self.layout.addLayout(self.buttonLayout)
        self.layout.addLayout(self.studentDetails)
        self.setLayout(self.layout)

        self.infoDict = global_info.info
        self.student_details()

    def student_details(self):
        first = self.infoDict.student_first_name(self.class_name, self.username)
        first_name_text = QLabel('First Name: {0}'.format(first))
        last = self.infoDict.student_last_name(self.class_name, self.username)
        last_name_text = QLabel('Last Name: {0}'.format(last))
        email = self.infoDict.student_email_address(self.class_name, self.username)
        email_text = QLabel('Email: {0}'.format(email))
        average_submission = self.infoDict.average_student_submission_count(self.class_name, self.username)
        average_submission_text = QLabel('Average Submission Count: {0}'.format(average_submission))
        self.studentDetails.addWidget(first_name_text, 0, Qt.AlignTop)
        self.studentDetails.addWidget(last_name_text, 0, Qt.AlignTop)
        self.studentDetails.addWidget(email_text, 0, Qt.AlignTop)
        self.studentDetails.addWidget(average_submission_text, 10, Qt.AlignTop)

        self.backButton.clicked.connect(self.back_button_clicked)

    @pyqtSlot(bool)
    def back_button_clicked(self, checked: bool):
        if checked:
            parent_widget = self.parentWidget()
            self.destroy()
            parent_widget.show_class_window()


class AssignmentWindow(QWidget):

    def __init__(self, class_name: str, assignment: str):

        super().__init__()
        self.class_name = class_name
        self.assignment = assignment
        self.setWindowTitle("Assignment")
        self.infoDict = global_info.info
        self.layout = QVBoxLayout()
        self.backButton = QToolButton(self)
        self.backButton.setArrowType(Qt.LeftArrow)
        self.backButton.setCheckable(True)
        self.backButton.setFixedSize(30, 30)
        self.layout.addWidget(self.backButton, alignment=Qt.AlignLeft)

        self.submissionTable = QTableWidget(self.infoDict.student_count(self.class_name), 4, self)
        self.layout.addWidget(self.submissionTable)

        self.setLayout(self.layout)
        self.submission_table()

    def submission_table(self):

        self.submissionTable.setHorizontalHeaderItem(0, QTableWidgetItem(
            'Student'))
        self.submissionTable.setHorizontalHeaderItem(1, QTableWidgetItem(
            'Last Submission Time'))
        self.submissionTable.setHorizontalHeaderItem(2, QTableWidgetItem(
            'Submission Count'))
        self.submissionTable.setHorizontalHeaderItem(3, QTableWidgetItem(
            'Unfetched'))

        row = 0

        for student in self.infoDict.student_list(self.class_name):
            self.submissionTable.setItem(row, 0, QTableWidgetItem(student))
            self.submissionTable.setItem(row, 1, QTableWidgetItem(self.infoDict.submission_time_string(self.class_name, self.assignment, student)))
            self.submissionTable.setItem(row, 2, QTableWidgetItem(str(self.infoDict.student_submission_count(self.class_name, self.assignment, student))))
            self.submissionTable.setItem(row, 3, QTableWidgetItem(1))

            row += 1

        self.submissionTable.setSortingEnabled(True)
        self.submissionTable.setCornerButtonEnabled(False)
        self.submissionTable.resizeColumnsToContents()

        for row in range(self.submissionTable.rowCount()):
            self.submissionTable.item(row, 0).setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

        self.backButton.clicked.connect(self.back_button_clicked)

    @pyqtSlot(bool)
    def back_button_clicked(self, checked: bool):
        if checked:
            parent_widget = self.parentWidget()
            self.destroy()
            parent_widget.show_class_window()