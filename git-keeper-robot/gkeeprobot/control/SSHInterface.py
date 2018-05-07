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


"""
Provides a globally accessible interface for interacting with a git-keeper
server through a paramiko SSH connection.

This module stores a SeverInterface instance in the module-level instance
variable named server_interface. Call connect() on this instance as early as
possible, probably in main() or whatever your entry point function is.
Attempting to call connect() a second time will raise a ServerInterfaceError
exception.

Any other modules that import the config will have access to the same instance
without having to call connect().

Before calling connect, be sure that you have called parse() on the global
ClientConfiguration object.

Example usage::

    import sys
    from gkeepclient.client_configuration import config
    from gkeepclient.server_interface import server_interface

    def main():
        try:
            config.parse()
            server_interface.connect()
        except ClientConfigurationError, ServerInterfaceError as e:
            sys.exit(e)

        # Now call methods such as server_interface.is_file(file_path)
"""

import os
from shlex import quote

from paramiko import SSHClient, AutoAddPolicy, SSHException

from gkeepcore.gkeep_exception import GkeepException
from gkeeprobot.control.VagrantInfo import VagrantInfo
from gkeeprobot.vm_type import VMType

vagrant_info = VagrantInfo()


class SSHInterfaceError(GkeepException):
    """Raised by ServerInterface methods."""
    pass


class ServerCommandExitFailure(SSHInterfaceError):
    """Raised when a command has a non-zero exit code."""
    pass


class SSHInterface:
    """
    Provides methods for interacting with the server over a paramiko SSH
    connection.

    All methods raise a ServerInterfaceError exception on errors.
    """

    clients_by_user_and_port = {}

    def _connect(self, username, port, key_dir='ssh_keys'):
        key_filename = '{}/{}_rsa'.format(key_dir, username)
        hostname = 'localhost'

        # connect the SSH client and open an SFTP client
        try:
            ssh_client = SSHClient()
            ssh_client.set_missing_host_key_policy(AutoAddPolicy())
            ssh_client.connect(hostname=hostname,
                               username=username,
                               port=port,
                               key_filename=key_filename,
                               timeout=5,
                               compress=True)
            sftp_client = ssh_client.open_sftp()
        except Exception as e:
            error = ('Error connecting to {0} on port {1}: {2}'
                     .format(hostname, port, e))
            raise SSHInterfaceError(error)

        SSHInterface.clients_by_user_and_port[(username, port)] = \
            (ssh_client, sftp_client)

    def run(self, command, username, port, key_dir='/vagrant/ssh_keys'):
        if port not in SSHInterface.clients_by_user_and_port:
            self._connect(username, port)

        ssh_client, _ = SSHInterface.clients_by_user_and_port[(username, port)]

        # join the command into a single string if it is a list
        if isinstance(command, list):
            # quote all the arguments in case of special characters
            command = ' '.join([quote(arg) for arg in command])

        # open a channel and run the command
        try:
            transport = ssh_client.get_transport()
            channel = transport.open_session()
            channel.get_pty()
            f = channel.makefile()
            channel.exec_command(command)
            output = f.read()

            exit_status = channel.recv_exit_status()
        except Exception as e:
            error = ('Error running command "{0}" on the server: {1}'
                     .format(command, e))
            raise SSHInterfaceError(error)

        if exit_status != 0:
            raise ServerCommandExitFailure('Non-zero exit code running {}. Output: {}'.format(command, output.decode('utf-8')))

        # output is bytes, we want a utf-8 string
        return output.decode('utf-8')

    def copy_file(self, local_path: str, remote_path: str, username, port):
        """
        Copy a local file to the server.

        It is the responsibility of the caller to ensure the local path exists
        and that the remote path does not exist.

        The remote_path is the full destination file path. After a
        successful copy, local_path and remote_path will be the same file.

        :param local_path: path to the local file
        :param remote_path: full destination path on the server
        """

        if (username, port) not in SSHInterface.clients_by_user_and_port:
            self._connect(username, port)

        _, sftp_client = SSHInterface.clients_by_user_and_port[(username, port)]

        try:
            sftp_client.put(local_path, remote_path)
        except Exception as e:
            raise SSHInterfaceError(e)
