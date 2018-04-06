import json
import os


class Config:
    def __init__(self):
        # red, green, blue
        self.submission_color = ((255, 192, 203), (208, 240, 192),
                                 (240, 248, 255))
        self.json_path = \
            os.path.expanduser('~/.config/git-keeper/submissions_path.json')
        self.create_json()

    def create_json(self):
        if not os.path.isfile(self.json_path):
            with open(self.json_path, 'w'):
                pass

        if os.path.getsize(self.json_path) == 0:
            paths = {}
            with open(self.json_path, 'w') as f:
                json.dump(paths, f)


gui_config = Config()
