import sys

import os

from gkeepclient.client_configuration import config
from gkeepclient.server_interface import server_interface


class GlobalInfo:

    def __init__(self):
        if len(sys.argv) < 2:
            path = os.path.expanduser('~/.config/git-keeper/client.cfg')
        else:
            path = os.path.expanduser(sys.argv[1])

        config.set_config_path(path)
        config.parse()

        server_interface.connect()
        self.refresh()

    def refresh(self):
        self.info = server_interface.get_info(freshness_threshold=0)


global_info = GlobalInfo()