# -*- coding: utf-8 -*-

from config import *

APP_NAME = 'EGA - pgAdmin4'

# Debug mode
DEBUG = True
SERVER_MODE = False
CONSOLE_LOG_LEVEL = DEBUG
FILE_LOG_LEVEL = DEBUG

# Misc
LOG_FILE = '/var/log/pgadmin4/pgadmin4.log'
SQLITE_PATH = '/var/lib/pgadmin4/pgadmin4.db'
SESSION_DB_PATH = '/var/lib/pgadmin4/sessions'
STORAGE_DIR = '/var/lib/pgadmin4/storage'

# Binding
DEFAULT_SERVER = '0.0.0.0'
DEFAULT_SERVER_PORT = 5050

# Extra
MODULE_BLACKLIST.remove('test')
UPGRADE_CHECK_ENABLED = False
DESKTOP_USER = 'ega@nbis.se'
