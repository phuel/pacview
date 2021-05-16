from pacman_cmd import PacmanCmd

class PacManDb():
    """Wrapper around pacman calls to retrieve package information."""
    def __init__(self, remote):
        self.remote = remote
        self.cmd = PacmanCmd(remote)
        self.packages = self.get_all_packages()
        self.package_names = sorted([p for p in self.packages.keys()])
        self.installed = self.get_package_list(['-Qe'])
        self.obsolete = self.get_package_list(['-Qtd'])
        self.not_required = []
        self._get_not_required()

    def get_all_packages(self):
        """Get information about all installed packages."""
        packages = {}
        package_lines = []
        for line in self._read_from_pacman(['-Qi']):
            if line == '':
                if len(package_lines) > 0:
                    package = self.__parse_package(package_lines)
                    packages[package['Name']] = package
                package_lines = []
            else:
                package_lines.append(line)
        return packages

    def get_package_list(self, pacman_args):
        """Get a list of packages"""
        names = []
        for line in self._read_from_pacman(pacman_args):
            names.append(line.split()[0])
        return names

    def _read_from_pacman(self, pacman_args):
        """Call pacman and return the lines output by pacman."""
        return self.cmd.exec(pacman_args)

    def can_delete_package(self, package):
        """Return a value indicating if the specified package can be deleted."""
        if not self._has_pacdel_script():
            return False            
        if package is None:
            return False
        if 'RequiredBy' not in package:
            return False
        if not self._is_required(package):
            return True
        return False

    def delete_package(self, packages):
        """Deletes the specified packages."""
        result = self.cmd.delete(packages)

        self.package_names = self.get_package_list(['-Q'])
        self.installed = self.get_package_list(['-Qe'])
        self.obsolete = self.get_package_list(['-Qtd'])

        packages_to_delete = []
        for name in self.packages.keys():
            if not name in self.package_names:
                packages_to_delete.append(name)
        for name in packages_to_delete:
            del self.packages[name]
        for name in self.package_names:
            if name not in self.packages:
                package_lines = self._read_from_pacman(['-Qi', name])
                self.packages[name] = self.__parse_package(package_lines)

        for package_name in packages:
            if package_name not in self.package_names and package_name in self.not_required:
                self._remove_package_from_lists(package_name)
        self._get_not_required()

        return result

    def _has_pacdel_script(self):
        """Return a value indicating whether the script is available that is needed to delete packages."""
        return self.cmd.can_delete()

    def get_not_installed_package_info(self, name):
        """Gets info about a package that is not installed."""
        package_lines = self._read_from_pacman(['-Si', name])
        return self.__parse_package(package_lines)

    def get_dependent(self, root_name):
        """Gets all packages that depend on the specified package."""
        dependent = []
        self._get_dependent(root_name, dependent)
        return dependent

    def _remove_package_from_lists(self, name):
        """Remove a package from all 'RequiredBy' lists after it was uninstalled."""
        self.not_required.remove(name)
        for package in self.packages.values():
            if 'RequiredBy' in package and name in package['RequiredBy']:
                package['RequiredBy'].remove(name)
                # Replace an empty list with a list with one 'None' entry
                # because that is what pacman normally does.
                if len(package['RequiredBy']) == 0:
                    package['RequiredBy'] = [ 'None' ]
    
    def _get_dependent(self, root_name, dependent):
        """Internal recursove function that gets all packages that depend on the specified package."""
        for name in self.not_required:
            if name in dependent:
                continue
            package = self.packages[name]
            if len(package['DependsOn']) == 1 and package['DependsOn'][0] == 'None':
                continue
            if root_name in package['DependsOn']:
                dependent.append(name)
                self._get_dependent(name, dependent)

    def _get_not_required(self):
        """Get packages that are not required by any explicitely installed package."""
        package_added = True
        while package_added:
            package_added = False
            for name, package in self.packages.items():
                if package['InstallReason']:
                    continue
                if name in self.not_required:
                    continue
                if not self._is_required(package) and not self.packages[name]['InstallReason']:
                    self.not_required.append(name)
                    package_added = True

    def _is_required(self, package):
        """Returns a value indicating whether the specified package is required by any installed package."""
        if len(package['RequiredBy']) == 1 and package['RequiredBy'][0] == 'None':
            return False
        for required in package['RequiredBy']:
            if required in self.package_names and required not in self.not_required:
                return True
        return False

    def __parse_package(self, lines):
        """Parses the package information printed by pacman."""
        package = {}
        current_key = None
        for line in lines:
            if line.startswith('    '):
                package[current_key].append(line.strip())
                continue
            if line.strip() == '':
                continue
            key,value = line.split(':', maxsplit=1)
            key = key.strip().replace(' ', '')
            current_key = key
            value = value.strip()
            if key in ['ConflictsWith', 'DependsOn', 'Groups', 'Licenses',
                       'OptionalFor', 'Provides', 'Replaces', 'RequiredBy']:
                package[key] = value.split()
            elif key == 'OptionalDeps':
                package[key] = [ value ]
            elif key == 'InstallReason':
                package[key] = 'Explicitly' in value
            elif key == 'InstalledSize':
                size, unit = value.split()
                size = float(size)
                if unit == 'KiB':
                    size *= 1024
                elif unit == 'MiB':
                    size *= 1024 * 1024
                package[key] = size
            else:
                package[key] = value

        return package
