import json
import os

from gkeepclient.fetch_submissions import FetchedHashCache
from gkeepclient.server_interface import ServerInterfaceError
from gkeepcore.git_commands import git_head_hash
from gkeepgui.global_info import global_info
from gkeepgui.gui_configuration import gui_config
from gkeepgui.gui_exception import GuiException


class FacultyClass:
    """
    Stores the attributes of a class.

    Attributes stored:
        name
        student_count
        student_list
        assignment_count
        assignment_list
    """
    def __init__(self, class_name: str):
        """
        Constructor.

        Set the attributes.

        :param class_name: name of the class
        """
        try:
            self._info = global_info.info
        except ServerInterfaceError:
            pass

        self.name = class_name
        self.student_count = self._info.student_count(class_name)
        self.assignment_count = self._info.assignment_count(class_name)
        self._student_list = None
        self._assignment_list = None

    def get_student_list(self) -> list:
        """
        Get the list of students in the class.

        :return: list of Student objects
        """
        if self._student_list is None:
            self._student_list = []
            for student in self._info.student_list(self.name):
                self._student_list.append(Student(self, student))

        return self._student_list

    def get_assignment_list(self) -> list:
        """
        Get the list of assignments for the class.

        :return: list of Assignment objects
        """
        if self._assignment_list is None:
            self._assignment_list = []

            for assignment in self._info.assignment_list(self.name):
                self._assignment_list.append(Assignment(self, assignment))

        return self._assignment_list

    def print_info(self):
        print('Class name:', self.name)
        print()


class Student:
    """
    Stores the attributes of a student.

    Attributes stored:
        parent_class: FacultyClass object representing the parent class
        username
        email
        first_name
        last_name
        last_first_username
        home_dir
        average_submission_count
        submission_list
    """
    def __init__(self, a_class: FacultyClass, username: str):
        """
        Constructor.

        Set the attributes.

        :param a_class: student's class
        :param username: student's username
        """
        try:
            self._info = global_info.info
        except ServerInterfaceError:
            pass

        self.parent_class = a_class
        self.username = username
        class_and_username = (self.parent_class.name, self.username)
        self.email = self._info.student_email_address(*class_and_username)
        self.first_name = self._info.student_first_name(*class_and_username)
        self.last_name = self._info.student_last_name(*class_and_username)
        self.last_first_username = \
            self._info.student_last_first_username(*class_and_username)
        self.home_dir = self._info.student_home_dir(*class_and_username)
        self.average_submission_count = \
            self._info.average_student_submission_count(*class_and_username)
        self._submission_list = None

    def get_submission_list(self) -> list:
        """
        Get the list of submissions by the student.

        :return: list of Submission objects
        """
        if self._submission_list is None:
            self._submission_list = []

            for assignment in self.parent_class._assignment_list:
                for submission in assignment.get_submission_list():
                    if submission.student.username == self.username:
                        self._submission_list.append(submission)

        return self._submission_list

    def _print_info(self):
        print('Username:', self.username)
        print()


class Assignment:
    """
    Stores the attribute of an assignment.

    Attributes stored:
        parent_class: FacultyClass object representing the parent class
        name
        is_published
        reports_hash
        reports_path
        students_submitted_count
        students_submitted_list
        fetched_path
        no_submission_list
    """
    def __init__(self, a_class: FacultyClass, assignment: str):
        """
        Constructor.

        Set the attributes.

        :param a_class: assignment's class
        :param assignment: assignment's name
        """
        try:
            self._info = global_info.info
        except ServerInterfaceError:
            pass

        self.parent_class = a_class
        self.name = assignment
        class_and_assignment = [self.parent_class.name, self.name]
        self.is_published = self._info.is_published(*class_and_assignment)
        self.reports_hash = self._info.reports_hash(*class_and_assignment)
        self.reports_path = self._info.reports_path(*class_and_assignment)
        self.students_submitted_count = \
            self._info.student_submitted_count(*class_and_assignment)
        self.fetched_path = ''
        self._submission_list = None
        self.students_submitted_list = None
        self.no_submission_list = None
        self.update_submissions()

    def get_submission_list(self) -> list:
        """
        Get the list of all submissions, including those that have not been
        submitted.

        :return: list of Submission objects
        """
        if self._submission_list is None:
            self._submission_list = []
            for student in self.parent_class.get_student_list():
                self._submission_list.append(Submission(student, self))

        return self._submission_list

    def update_submissions(self):
        """
        Update the students_submitted_list and the no_submission_list.

        :return: None
        """
        self.students_submitted_list = []
        self.no_submission_list = []

        for submission in self.get_submission_list():
            if submission.submission_count > 0:
                self.students_submitted_list.append(submission)
            else:
                self.no_submission_list.append(submission)

    def get_path_from_json(self):
        with open(gui_config.json_path, 'r') as f:
            paths = json.load(f)

        if self.parent_class.name in paths.keys():

            if self.name in paths[self.parent_class.name].keys():
                return paths[self.parent_class.name][self.name]
        else:
            return None

    def set_fetched_path(self, path: str):
        """
        Set the path to which the submissions for the assignment were fetched.

        :param path: path of fetched submissions
        :return: None
        """
        self.fetched_path = path
        for submission in self.get_submission_list():
            submission.set_fetched_path()

    def fetched_list(self) -> list:
        """
        Get the list of fetched submissions.

        :return: List of Submission objects for fetched submissions.
        """
        fetched_list = []
        for submission in self.students_submitted_list:
            if submission.is_fetched():
                fetched_list.append(submission)

        return fetched_list

    def _print_info(self):
        print('Assignment', self.name)
        print()


class Submission:
    """
    Store the attributes of a submission.

    Attributes stored:
        assignment: Assignment object representing the parent assignment
        student: Student object representing the owner of the submission
        parent_class: FacultyClass object representing the parent class
        server_hash
        student_path: path to student's assignment
        submission_count
        time: submission time in the format 'year/day/month hour:minute:second'
        fetched_path: path to fetched submission
    """
    def __init__(self, student: Student, assignment: Assignment):
        """
        Constructor.

        Set the attribute.

        :param a_class: student's class
        :param student: owner of submission
        :param assignment: assignment of submission
        """
        self._info = global_info.info
        self.assignment = assignment
        self.student = student
        self.parent_class = self.assignment.parent_class
        class_assignment_username = (self.parent_class.name, self.assignment.name,
                self.student.username)
        self.server_hash = \
            self._info.student_assignment_hash(*class_assignment_username)
        self.student_path = \
            self._info.student_assignment_path(*class_assignment_username)
        self.submission_count = \
            self._info.student_submission_count(*class_assignment_username)
        self.time = \
            self._info.submission_time_string(*class_assignment_username)
        self.fetched_path = ''
        self.set_fetched_path()

    def set_fetched_path(self):
        if self.assignment.fetched_path != '':
            self.fetched_path = \
                os.path.join(self.assignment.fetched_path, self.assignment.name, 'submissions',
                             self.student.last_first_username)
        else:
            self.fetched_path = ''

    def is_fetched(self) -> bool:
        """
        Determine if a submission has been fetched.

        :return: True if fetched, False otherwise.
        """
        if self.fetched_path == '':
            is_fetched = False
        else:
            local_hash = None
            cache = FetchedHashCache(self.fetched_path)

            if cache.is_cached(self.fetched_path):
                local_hash.get_hash(self.fetched_path)
            else:
                local_hash = git_head_hash(self.fetched_path)
                cache.set_hash(self.fetched_path, local_hash)

            if local_hash != self.server_hash:
                is_fetched = False
            else:
                is_fetched = True

        return is_fetched

    def _print_info(self):
        print('Fetched submission by:', self.student.username)
        print()
