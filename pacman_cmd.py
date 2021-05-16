import subprocess
import re

class PacmanCmd():
    def __init__(self, remote):
        self.remote = remote

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
        # To enable pacview to delete packages the script 'pacdel.sh' must be
        # found via the PATH and it must be allowed to be executed by sudo
        # without a password.
        # This can be done by adding the line
        #   username ALL = (root) NOPASSWD: /path/to/pacdel.sh
        # to /etc/sudoers using visudo.
        command = self._create_command(['sudo', '-n', 'pacdel.sh'])
        packages.reverse()
        command.extend(packages)
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        return process.communicate()

    def can_delete(self):
        """Return a value indicating whether the script is available that is needed to delete packages."""
        command = self._create_command(['whereis', 'pacdel.sh'])
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        result = process.communicate()
        return re.match(r"pacdel:\s/\w+", result[0])

    def _create_command(self, command):
        if self.remote is not None:
            # Source the .bashrc to externd the PATH before file before executing the pacdel script.
            command = [ 'ssh', '-t', self.remote, '.', '.bashrc', ';' ] + command
        return command
