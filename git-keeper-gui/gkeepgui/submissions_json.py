import json
import os


class SubmissionsPaths:
    def __init__(self):
        self.json_path = \
            os.path.expanduser('~/.config/git-keeper/submissions_path.json')
        self.create_json()

    def create_json(self):
        if not self.json_exists():
            with open(self.json_path, 'w'):
                pass

        if os.path.getsize(self.json_path) == 0:
            paths = {}
            with open(self.json_path, 'w') as f:
                json.dump(paths, f)

    def json_exists(self):
        return os.path.isfile(self.json_path)

    def get_path(self, assignment: str, class_name: str):
        """
        Get the path of the directory where the assignments are fetched from
        the json file in '~/.config/git-keeper'.

        :return: Path to fetched directory. None if fetched path is not in the
        file
        """

        with open(self.json_path, 'r') as f:
            paths = json.load(f)

        if class_name in paths.keys():

            if assignment in paths[class_name].keys():
                path = paths[class_name][assignment]

                return path
        else:
            return None

    def set_path(self, assignment: str, class_name: str, path):
        """
        Set submissions path in the json file at
        '~/.config/git-keeper/submissions_path.json'.

        :param assignment: name of the assignment
        :param path: fetched path

        :return: none
        """

        with open(self.json_path, 'r') as f:
            paths = json.load(f)

        if class_name not in paths.keys():
            paths[class_name] = {}

        paths[class_name][assignment] = path

        with open(self.json_path, 'w') as f:
            json.dump(paths, f)


submissions_paths = SubmissionsPaths()