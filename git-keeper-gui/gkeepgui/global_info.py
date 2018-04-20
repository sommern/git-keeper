import sys

import os

from gkeepclient.client_configuration import config
from gkeepclient.server_interface import server_interface
# from gkeepgui.mock_server_interface import server_interface, config


class GlobalInfo:

    def __init__(self):
        self._connected = False
        if len(sys.argv) < 2:
            path = os.path.expanduser('~/.config/git-keeper/client.cfg')
        else:
            path = os.path.expanduser(sys.argv[1])

        config.set_config_path(path)
        config.parse()

    def refresh(self):
        self.info = server_interface.get_info(freshness_threshold=0)

    def connect(self):
        # just use the error message in server_interface
        server_interface.connect()
        self._connected = True
        self.refresh()

    def is_connected(self):
        return self._connected


global_info = GlobalInfo()