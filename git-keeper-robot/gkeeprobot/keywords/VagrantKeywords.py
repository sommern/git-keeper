from robot.api import logger
from gkeepcore.shell_command import run_command_in_directory
from gkeeprobot.control.VagrantControl import VagrantControl
from gkeeprobot.control.ServerControl import ServerControl
from gkeeprobot.control.ClientControl import ClientControl

vagrant_control = VagrantControl()
server_control = ServerControl()
client_control = ClientControl()

class VagrantKeywords:

    server_was_running = False
    client_was_running = False

    def make_boxes_if_missing(self):
        names = [box.name for box in vagrant_control.v.box_list()]

        if 'gkserver' not in names:
            logger.console('Making gkserver.box.  This can take up to 30 minutes.')
            run_command_in_directory('gkserver_base', 'bash -c ./make_box.sh')
            vagrant_control.v.box_add('gkserver', 'gkserver_base/gkserver.box')

        if 'gkclient' not in names:
            logger.console('Making gkclient.box.  This can take up to 30 minutes.')
            run_command_in_directory('gkclient_base', 'bash -c ./make_box.sh')
            vagrant_control.v.box_add('gkclient', 'gkclient_base/gkclient.box')

    def start_vagrant_if_not_running(self):
        if vagrant_control.is_server_running():
            logger.console('Using existing gkserver VM...')
            VagrantKeywords.server_was_running = True
        else:
            logger.console('Start gkserver VM...')
            vagrant_control.v.up(vm_name='gkserver')
        if vagrant_control.is_client_running():
            logger.console('Using existing gkclient VM...')
            VagrantKeywords.client_was_running = True
        else:
            logger.console('Start gkclient VM...')
            vagrant_control.v.up(vm_name='gkclient')

    def stop_vagrant_if_not_originally_running(self):
        if VagrantKeywords.server_was_running:
            logger.console('Leaving gkserver VM running...')
        else:
            logger.console('Destroying gkserver VM...')
            vagrant_control.v.destroy(vm_name='gkserver')
        if VagrantKeywords.client_was_running:
            logger.console('Leaving gkclient VM running...')
        else:
            logger.console('Destroying gkclient VM...')
            vagrant_control.v.destroy(vm_name='gkclient')

    def set_key_permissions(self):
        run_command_in_directory('ssh_keys', 'chmod 600 *')

    def verify_systems_ready(self):
        assert server_control.run_vm_python_script('keeper', 'check_sudo.py') == 'True'
        assert client_control.run_vm_python_script('keeper', 'check_sudo.py') == 'True'
        assert server_control.run_vm_python_script('keeper', 'check_base_user_list.py') == 'True'
        assert client_control.run_vm_python_script('keeper', 'check_base_user_list.py') == 'True'
        assert server_control.run_vm_python_script('keeper', 'server_terminated.py') == 'True'
        assert server_control.run_vm_python_script('keeper', 'check_keeper_files.py') == 'True'
        assert server_control.run_vm_python_script('keeper', 'check_email_empty.py') == 'True'
