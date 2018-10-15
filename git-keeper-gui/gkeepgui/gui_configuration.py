import json
import os


class Config:
    def __init__(self):
        # red, green, blue
        self.submission_color = ((255, 192, 203), (208, 240, 192),
                                 (240, 248, 255))


gui_config = Config()
