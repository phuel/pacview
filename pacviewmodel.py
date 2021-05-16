import json

from kivy.utils import escape_markup

class PackageViewModel():
    def __init__(self, package):
        self.package = package

    def to_dict(self):
        data = self.package
        result = {}
        for key in ['Name', 'Description', 'Packager', 'InstallDate']:
            result[key] = PackageViewModel.get_prop(data, key)
        result['URL'] = PackageViewModel.make_ref('URL', data['URL']) if data is not None and 'URL' in data else ''
        for key in ['DependsOn', 'RequiredBy']:
            result[key] = PackageViewModel.make_ref_list(data, key)
        result['InstalledSize'] = PackageViewModel.get_size(data, 'InstalledSize')
        result['InstalledOptions'] = PackageViewModel.get_optional_deps(data, True)
        result['UninstalledOptions'] = PackageViewModel.get_optional_deps(data, False)
        return result

    @staticmethod
    def get_prop(data, key):
        return data[key] if data is not None and key in data else ''

    @staticmethod
    def make_ref(id, text):
        return '[u][ref={0}]{1}[/ref][/u]'.format(escape_markup(id), escape_markup(text))

    @staticmethod
    def make_ref_list_from_list(refs):
        if len(refs) == 0 or refs[0] == 'None':
            return '—'
        return " ".join([PackageViewModel.make_ref(dep, dep) for dep in refs])

    @staticmethod
    def make_ref_list(data, key):
        if data is None:
            return ''
        if key not in data or data[key][0] == 'None':
            return '—'
        return PackageViewModel.make_ref_list_from_list(data[key])

    @staticmethod
    def get_size(data, key):
        size = PackageViewModel.get_prop(data, key)
        if size != '':
            size = PackageViewModel.format_size(int(size))
        return size

    @staticmethod
    def format_size(size):
        if size < 1024:
            return f'{size} B'
        if size < (1024 * 1024):
            size = size / 1024
            return f'{size:.2f} KiB'
        size = size / (1024 * 1024)
        return f'{size:.2f} MiB'

    @staticmethod
    def get_optional_deps(data, installed):
        if data is None:
            return ''
        key = 'OptionalDeps'
        if key not in data or data[key][0] == 'None':
            return '—'
        deps = []
        for dep in data[key]:
            if ('[installed]' in dep) == installed:
                deps.append(dep.split(':')[0])
        return PackageViewModel.make_ref_list_from_list(deps)


class ListViewModel():
    def __init__(self, names, database):
        self.names = names
        self.packages = database.packages
        self.database = database

    def get_list(self):
        for name in self.names:
            yield self.packages[name]

    def get_package(self, name):
        if name in self.packages:
            return self.packages[name]
        for package in self.packages.values():
            if 'Provides' in package and name in package['Provides']:
                return package
        return self.database.get_not_installed_package_info(name)

class PacViewModel():
    def __init__(self, database):
        self.database = database

    def get_installed(self):
        return ListViewModel(self.database.installed, self.database)

    def get_all(self):
        return ListViewModel(self.database.package_names, self.database)

    def get_obsolete(self):
        return ListViewModel(self.database.obsolete, self.database)

    def get_not_required(self):
        return ListViewModel(sorted(self.database.not_required), self.database)

    def can_delete_package(self, package):
        return self.database.can_delete_package(package)

    def delete_package(self, packages):
        return self.database.delete_package(packages)

    def get_dependent(self, name):
        return self.database.get_dependent(name)
