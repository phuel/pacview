#! /usr/bin/env python3

import os
import sys
import re
import argparse

import kivy
kivy.require('2.0.0')

from app_settings import AppSettings
settings = AppSettings('pacview')
ws = settings.get_window_settings()

from kivy.config import Config
if ws is not None:
    Config.set('graphics', 'position', 'custom')
    Config.set('graphics', 'left', ws['left'])
    Config.set('graphics', 'top', ws['top'])
    Config.set('graphics', 'width', ws['width'])
    Config.set('graphics', 'height', ws['height'])

Config.set('graphics', 'resizable', True)
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.set('kivy', 'exit_on_escape', '0')

from kivy.logger import Logger

from pacmandb import PacManDb
from pacviewmodel import PacViewModel
from pacview_app import PacViewApp

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("remote", nargs="?", help="the remote address")
    
    args = parser.parse_args()

    remote = args.remote
    # Either 'ssh://user@host:port' or 'user@host' is allowed as ssh destination.
    if not re.match(r'ssh://(\w+@)?\w+(:\d{1,5})?', remote) and not re.match(r'(\w+@)?\w+', remote):
        Logger.error("Invalid remote address: '" +  remote + "'")
        return

    db = PacManDb(args.remote)
    Logger.info("pacview: Number of packages: {0}".format(len(db.package_names)))
    Logger.info("pacview: Explicitly installed: {0}".format(len(db.installed)))
    Logger.info("pacview: Obsolete: {0}".format(len(db.obsolete)))
    Logger.info("pacview: Not Required: {0}".format(len(db.not_required)))
    viewmodel = PacViewModel(db)
    PacViewApp(settings, viewmodel).run()

if __name__ == '__main__':
    main()
