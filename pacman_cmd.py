import subprocess
import re

class PacmanCmd():
    def __init__(self, remote):
        self.remote = remote
        if self.remote is not None and not self.remote.startswith('ssh://'):
            self.remote = 'ssh://' + self.remote

    def exec(self, pacman_args):
        """Call pacman and return the lines output by pacman."""
        command = []
        if self.remote is not None:
            command.extend([ 'ssh', self.remote ])
        command.append('pacman')
        command.extend(pacman_args)
        process = subprocess.Popen(command, stdout=subprocess.PIPE, text=True, encoding='utf-8')
        result = process.communicate()[0]
        return result.splitlines()

    def delete(self, packages):
        # To allow pacview to delete packages the 'pacman' must be allowed to be executed by sudo without a password.
        # This can be done by adding the line
        #   username ALL = (root) NOPASSWD: /usr/bin/pacman
        # to /etc/sudoers using visudo.
        command = self._create_command(['sudo', '-n', 'pacman', '-R', '--noconfirm', '--noprogressbar'])
        packages.reverse()
        command.extend(packages)
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        return process.communicate()

    def can_delete(self):
        """Return a value indicating whether the script is available that is needed to delete packages."""
        command = self._create_command(['sudo', '-n', 'pacman', '-V'])
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        result = process.communicate()
        return result[1] == ''

    def _create_command(self, command):
        if self.remote is not None:
            command = [ 'ssh', self.remote ] + command
        return command
