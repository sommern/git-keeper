# Copyright 2018 Nathan Sommer and Ben Coleman
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from enum import Enum

from gkeepcore.shell_command import run_command
from tempfile import TemporaryDirectory
from robot.api import logger

from gkeeprobot.control.SSHInterface import SSHInterface

"""Provides methods to execute commands on gkclient and gkserver
during testing."""


class VMControl:

    temp_dir = TemporaryDirectory(prefix='temp_ssh_keys', dir='.')
    ssh_interface = SSHInterface()

    def run_vm_python_script(self, username, script, port, *args):
        base = 'python3 /vagrant/vm_scripts/' + script
        cmd = ' '.join([base] + list(args))
        return self.run(username, port, cmd).strip()

    def run_vm_bash_script(self, username, script, port, *args):
        base = 'bash /vagrant/vm_scripts/' + script
        cmd = ' '.join([base] + list(args))
        return self.run(username, port, cmd).strip()

    def run(self, username, port, cmd):
        logger.console(cmd)
        return VMControl.ssh_interface.run(cmd, username, port)

    def copy(self, username, port, filename, target_filename):
        logger.console('{} -> {}'.format(filename, target_filename))
        return VMControl.ssh_interface.copy_file(filename, target_filename, username, port)
