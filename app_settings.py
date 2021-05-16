import os
import json

from pathlib import Path

from kivy.logger import Logger

class AppSettings:
    def __init__(self, app_name):
        self.app_name = app_name
        self._data = None

    def get_window_settings(self):
        if self._data is None:
            self._read()

        if 'window' in self._data:
            return self._data['window']
        return None

    def set_window_settings(self, ws):
        if self._data is None:
            self._read()
        self._data['window'] = ws
        self._write()

    def _get_store_path(self):
        home = Path.home()
        config_path = os.path.join(home, '.config')
        if not os.path.isdir(config_path):
            os.mkdir(config_path)
        return os.path.join(config_path, self.app_name + '.json')

    def _read(self):
        try:
            store_path = self._get_store_path()
            with open(store_path, 'r') as fp:
                self._data = json.load(fp)
        except:
            self._data = {}

    def _write(self):
        try:
            store_path = self._get_store_path()
            with open(store_path, 'w') as fp:
                json.dump(self._data, fp, indent=2)
        except Exception:
            Logger.exception("pacview: Could not write settings!")
