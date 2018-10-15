"""
Stores the information and attributes for implementing a graphical user
interface to interact with git-keeper. Includes classes that represent the
main windows and tables used by the GUI.
"""


import json

import os

from gkeepclient import fetch_submissions
from gkeepclient.server_interface import ServerInterfaceError
from gkeepgui.class_information import FacultyClass, Assignment, Submission
from gkeepgui.gui_configuration import gui_config

from gkeepgui.global_info import global_info
from gkeepgui.gui_exception import GuiException, GuiFileException
from gkeepgui.submissions_json import submissions_paths


class ClassWindowInfo:
    """
    Stores information for making the main window in the graphical user
    interface. Provides functionality for viewing classes, assignments,and
    fetching submissions.
    """

    def __init__(self):
        """
        Constructor.

        Set the attributes.
        """

        self.class_list = []
        self.connect()

        self.title = 'Class Window'
        self.current_class = None
        self.current_assignments_table = None
        self.current_submissions_table = None

        self.config = gui_config
        self.create_classes()
        self.change_class(0)
        self.set_description()

    def connect(self):
        """
        Connect to the server interface and stores FacultyClassInfo as an
        attribute.

        :return: none
        """
        if not global_info.is_connected():
            global_info.connect()

        self.info = global_info.info

    def refresh(self):
        """
        Fetch info from the server and refreshes the attributes and
        information stored.
        :return: none
        """
        global_info.refresh()
        self.info = global_info.info
        self.create_classes()

        if self.current_assignments_table.selected_row is not None:
            current_row = self.current_assignments_table.selected_row
        else:
            current_row = None

        self.current_assignments_table = AssignmentTable(self.current_class)

        if self.current_submissions_table is not None:
            self.current_assignments_table.select_row(current_row)
            self.current_submissions_table = SubmissionsTable(
                self.current_assignments_table.current_assignment[0])

    def create_classes(self):
        """
        Add classes.

        :return: none
        """

        self.class_list = []

        for a_class in self.info.class_list():
            self.class_list.append(FacultyClass(a_class))

    def change_class(self, index: int):
        """
        Change the current assignment table when the class view changes to
        another class.

        :param index: index of the class in the list
        :return:
        """
        self.current_class = self.class_list[index]
        self.current_assignments_table = AssignmentTable(self.current_class)
        self.current_submissions_table = None

    def select_assignment(self, rows):
        """
        Select an assignment when the row containing the column is selected.
        Creates the submissions table.

        If no assignment is selected, sets current submissions table to None.

        :param rows: index of the row. None if no row is selected.
        :return: none
        """
        self.current_assignments_table.select_row(rows)
        assignment = self.current_assignments_table.current_assignment[0]

        if assignment is not None and assignment.is_published:
            self.current_submissions_table = SubmissionsTable(assignment)
        else:
            self.current_submissions_table = None

    def select_submission(self, row):
        """
        Select a submission when the row containing the submission is
        selected.

        :param row: index of the row
        :return: none
        """
        self.current_submissions_table.select_row(row)

    def set_description(self):
        """
        Set the description text of the class.

        :return: none
        """

        student_count = self.current_class.student_count
        assignment_count = self.current_class.assignment_count
        description = ('Number of students: {} \n' +
                       'Number of assignments: {}').format(student_count,
                                                          assignment_count)
        return description

    def fetch_assignment(self, assignment: Assignment):
        """
        Grab the path where the assignment is to be fetched to. If fetched
        directory exists, fetch the submissions for that assignment.

        :return: none
        """

        path = submissions_paths.get_path(assignment.name,
                                          self.current_class.name)
        path = os.path.join(path, self.current_class.name)

        fetch_submissions.fetch_submissions(self.current_class.name,
                                        assignment.name, path)
        assignment.set_fetched_path(path)

    def fetch_assignments(self):
        """
        Fetch all assignments.

        :return: none
        """

        for assignment in self.current_class.get_assignment_list():
            if assignment.is_published:
                self.fetch_assignment(assignment)

    def fetch(self, assignment_selected=False):
        """
        Get the current assignment and fetch it or fetch all if none is
        selected.

        Refresh the state of the window.

        :return: none
        """

        if assignment_selected:
            for assignment in self.current_assignments_table.current_assignment:
                self.fetch_assignment(assignment)
        else:
            self.fetch_assignments()

        self.refresh()

    def change_submissions_sorting_order(self, col: int):
        """
        Sort the submissions table by the given column. If the current order
        is ascending, switch to descending, and vice versa.

        0: ascending
        1: descending

        :param col: index of the column
        :return: current sorting order
        """
        current_col = self.current_submissions_table.sorting_order[0]
        current_order = self.current_submissions_table.sorting_order[1]
        if current_col == col:
            if current_order == 0:
                self.current_submissions_table.set_sorting_order(col, 1)
            else:
                self.current_submissions_table.set_sorting_order(col, 0)
        else:
            self.current_submissions_table.set_sorting_order(col, 0)

        return self.current_submissions_table.sorting_order

    def change_assignments_sorting_order(self, col):
        """
        Sort the assignments table by the given column. If the current order
        is ascending, switch to descending, and vice versa.

        :param col: index of the column
        :return: none
        """
        current_col = self.current_assignments_table.sorting_order[0]
        current_order = self.current_assignments_table.sorting_order[1]

        if current_col == col:
            if current_order == 0:
                self.current_assignments_table.set_sorting_order(col, 1)
            else:
                self.current_assignments_table.set_sorting_order(col, 0)
        else:
            self.current_assignments_table.set_sorting_order(col, 0)


class StudentWindowInfo:
    """
    Stores information for making the student window in the graphical user
    interface.
    """

    def __init__(self, a_class: str, student: str):
        """
        Constructor.

        Set the attributes. Store FacultyClassInfo as a class attribute.

        :param a_class: name of the class
        :param student: name of the student
        """

        global_info.refresh()
        self.info = global_info.info

        self.title = 'Student Window'
        self.class_name = a_class
        self.username = student

    def set_description(self):
        """
        Set the description text.

        :return: description text
        """

        first_name = self.info.student_first_name(self.class_name,
                                                  self.username)
        last_name = self.info.student_last_name(self.class_name, self.username)
        email = self.info.student_email_address(self.class_name, self.username)
        average_submission_count = \
            self.info.average_student_submission_count(self.class_name,
                                                       self.username)
        description = \
            ('First Name: {} \n' +
             'Last Name: {} \n' +
             'Email: {} \n'
             'Average Submission Count: {}').format(first_name, last_name,
                                                    email,
                                                    average_submission_count)

        return description


class AssignmentWindowInfo:
    """
    Stores information for making the assignment window in the graphical user
    interface.
    """

    def __init__(self, a_class: str, assignment: str):
        """
        Set the attributes. Store FacultyClassInfo as a class attribute.

        :param a_class: name of the class
        :param assignment: name of the assignment
        """

        try:
            global_info.connect()
            self.info = global_info.info
        except ServerInterfaceError:
            pass

        self.title = 'Assignment Window'
        self.class_name = a_class
        self.assignment = assignment


class Table:
    """
    Table is a base class which stores attributes and methods for the table
    representation of information. This is used to draw tables in the graphical
    or command line interfaces.

    Attributes stored:
        row_count: row count
        col_count: column count
        col_headers: list of all column headers
        rows_content: list of all the rows including their contents
        selected_row: index of the selected row
        sorting_order: tuple storing current sorting order
    """

    def __init__(self):
        """
        Constructor.

        Declare all attributes and set their values to 0 or None.
        """
        self.row_count = 0
        self.col_count = 0
        self.col_headers = []
        self.rows_content = []
        self.selected_row = None
        self.sorting_order = None

    def set_row_count(self, count: int):
        """
        Set row count.

        :param count: number of rows
        :return: none
        """
        self.row_count = count

        for row in range(self.row_count):
            self.rows_content.append([])

    def set_column_count(self, count: int):
        """
        Set column count. Set all column headers to None, all rows' contents to
        None, and all columns' sorting orders to ascending.

        :param count: number of columns
        :return: none
        """
        self.col_count = count

        for col in range(self.col_count):
            self.col_headers.append('')

        for row in self.rows_content:
            for cell in range(self.col_count):
                row.append('')

    def set_column_headers(self, headers: list):
        """
        Set the headers of all columns.

        :param headers: list of all headers in its correct order
        :return: none
        """
        if len(headers) != self.col_count:
            raise GuiException('Number of headers do not match number of '
                               'columns')

        for index in range(self.col_count):
            self.set_column_header(index, headers[index])

    def set_column_header(self, col: int, header: str):
        """
        Set the header of the column with index col.

        :param col: index of the column
        :param header: string of new header
        :return: none
        """
        self.col_headers[col] = header

    def set_rows_content(self, contents: list):
        """
        Set the contents of all rows.

        :return: none
        """
        pass

    def set_row_content(self, row: int, content_list: list):
        """
        Set the content of a row.

        :param row: index of row
        :param content_list: list of each cell's contents in its correct order
        :return: none
        """
        if len(content_list) != self.col_count:
            raise GuiException('Number of cells in this row do not match'
                               'number of columns')

        for col in range(self.col_count):
            self.rows_content[row][col] = content_list[col]

    def select_row(self, row: int):
        """
        Select a row.

        :param row: index of selected row, None if no row is selected
        :return: none
        """
        pass

    def set_sorting_order(self, col: int, order: int):
        """
        Set the sorting order. Sort the table by the designated column and
        order.
            0: ascending
            1: descending

        :param col: column to be sorted by
        :param order: sorting order

        :return: none
        """
        pass

    def __repr__(self):
        """
        Change the __repr__ of the class to represent the table.

        :return: content of the table
        """
        table = ''

        for col in self.col_headers:
            table += col + '        '

        table += '\n'

        for row in self.rows_content:
            for cell in row:
                table += cell + '       '
            table += '\n'

        return table


class AssignmentTable(Table):
    """
    This Table provides the table representation of all the assignments for
    a class. Set the sorting order of the table to sort by the first column in
    ascending order.

    An example visual representation of the table:
        Assignment Name | Students Submitted
        ------------------------------------
          homework_1    |       20
          homework_2    |    Unpublished
    """

    def __init__(self, a_class: FacultyClass):
        """
        Constructor.

        Set all attributes. Set the type of
        selection to all the cells of a row. Sort the table by the 'Assignment
        Name' column in ascending order.

        Attributes stored:
            _class: Faculty Class object representing the class
            current_assignment: Assignment object representing the selected
            assignment

        :param a_class: parent class of the assignment
        """

        super().__init__()
        self._class = a_class
        self.current_assignment = None
        self.sorting_order = None
        self.set_row_count(a_class.assignment_count)
        self.set_column_count(2)
        self.set_column_headers(['Assignment Name', 'Students Submitted'])
        self.set_sorting_order(0, 0)

    def set_rows_content(self, assignments: list):
        """
        Set all the rows' contents to their matching values. Set the 'Students
        Submitted' cell to 'Unpublished' if the assignment has not been
        published.

        :return: none
        """
        for row in range(self.row_count):
            assignment = assignments[row]

            if assignment.is_published:
                content = [assignment.name,
                           str(assignment.students_submitted_count)]
            else:
                content = [assignment.name, 'Unpublished']

            self.set_row_content(row, content)

    def select_row(self, rows: list):
        """
        Select a row. Set the current assignment to match the selected row.
        If no row is selected, set current assignment to None.

        :param rows: index of selected row
        :return: none
        """
        self.selected_row = rows
        self.current_assignment = []

        if rows is not None:
            for row in rows:
                for assignment in self._class.get_assignment_list():
                    if assignment.name == self.rows_content[row][0]:
                        self.current_assignment.append(assignment)
                        break
        else:
            self.current_assignment = None

    def set_sorting_order(self, col: int, order: int):
        """
        Set the sorting order. Sort the table by the designated column and
        order.
            0: ascending
            1: descending

        :param col: column to be sorted by
        :param order: sorting order

        :return: none
        """

        self.sorting_order = (col, order)

        if col == 0:
            if order == 0:
                assignments = sorted(self._class.get_assignment_list(),
                                     key=lambda assignment: assignment.name)
            else:
                assignments = sorted(self._class.get_assignment_list(),
                                     key=lambda assignment: assignment.name,
                                     reverse=True)

        else:
            if order == 0:
                assignments = sorted(
                    self._class.get_assignment_list(),
                    key=lambda assignment: assignment.students_submitted_count)
            else:
                assignments = sorted(
                    self._class.get_assignment_list(),
                    key=lambda assignment: assignment.students_submitted_count,
                    reverse=True)

        self.set_rows_content(assignments)


class SubmissionsTable(Table):
    """
    This Table provides the table representation of all the submissions for an
    assignment.

    An example visual representation of the table:
          Student   | Last Submission Time | Submission Count
        -----------------------------------------------------
        'alovelace' |    18/2/3 13:37:25   |        2
        'igrant'    |    18/3/3 7:0:1      |        0
    """

    def __init__(self, assignment: Assignment):
        """
        Constructor.

        Set all attributes. Set the sorting order of the table to sort by the
        first column in ascending order.
        Attributes stored:
            _assignment: Assignment object
            row_color: a dictionary with students' usernames as keys and the
                       corresponding color indicator for fetching status as
                       values
            current_student: Student object representing selected student
            sorting_order: a tuple of type
                (column by which table is sorted, current sorting order)

        :param assignment: parent assignment of the submission
        """
        super().__init__()
        self._assignment = assignment
        self.row_color = {}
        self.current_student = None
        self.sorting_order = None
        self.set_row_count(assignment.parent_class.student_count)
        self.set_column_count(3)
        self.set_column_headers(['Student', 'Last Submission Time',
                                 'Submission Count'])
        self.set_sorting_order(0, 0)

    def set_rows_content(self, submissions):
        """
        Set all the rows' contents to their matching values.

        :return: none
        """

        if not self._assignment.is_published:
            pass
        else:
            for row in range(self.row_count):
                submission = submissions[row]
                content = [submission.student.username,
                           submission.time, str(submission.submission_count)]
                self.set_row_content(row, content)
                self.set_row_color(submission)

    def set_row_color(self, submission: Submission):
        """
        Sets the color of the row to match its fetched status.
            0: has not submitted
            1: submission has been fetched
            2: submission has not been fetched

        All rows' colors are stored in a list whose indices match the indices
        of the row.

        :param submission: submission to set row color
        :return: none
        """
        if submission.submission_count == 0:
            self.row_color[submission.student.username] = 0 # red
        elif submission.is_fetched():
            self.row_color[submission.student.username] = 1 # green
        else:
            self.row_color[submission.student.username] = 2 # blue

    def set_sorting_order(self, col: int, order: int):
        """
        Set the sorting order. Sort the table by the designated column and
        order.
            0: ascending
            1: descending

        :param col: column to be sorted by
        :param order: sorting order

        :return: none
        """
        self.sorting_order = (col, order)

        if col == 0:
            if order == 0:
                submissions = sorted(
                    self._assignment.get_submission_list(),
                    key=lambda submission: submission.student.username)
            else:
                submissions = sorted(
                    self._assignment.get_submission_list(),
                    key=lambda submission: submission.student.username,
                    reverse=True)
        elif col == 1:
            if order == 0:
                submissions = sorted(
                    self._assignment.get_submission_list(),
                    key=lambda submission: submission.time)
            else:
                submissions = sorted(
                    self._assignment.get_submission_list(),
                    key=lambda submission: submission.time, reverse=True)
        else:
            if order == 0:
                submissions = sorted(
                    self._assignment.get_submission_list(),
                    key=lambda submission: submission.submission_count)
            else:
                submissions = sorted(
                    self._assignment.get_submission_list(),
                    key=lambda submission: submission.submission_count,
                    reverse=True)

        self.set_rows_content(submissions)

    def select_row(self, row: int):
        """
        Select a row. Set the current student to match the selected row.
        If no row is selected, set current student to None.

        :param row: index of selected row
        :return: none
        """
        self.selected_row = row

        if row is not None:
            for student in self._assignment.parent_class.get_student_list():
                if self.rows_content[row][0] == student.username:
                    self.current_student = student
                    break
        else:
            self.current_student = None
