#!/usr/bin/env python
import logging.config
import os.path
import sys
from mantabot import conf
from mantabot.core import management, plugins
from mantabot.util import native

logger = logging.Logger(__name__)

if __name__ == '__main__':
    # Load settings
    logging.basicConfig(level=logging.INFO)
    settings_path = os.environ.get('SETTINGS')
    if not settings_path:
        logger.critical('Environment variable SETTINGS missing')
        sys.exit(1)

    # Apply settings: logging and modules
    conf.load(settings_path, context={
        'conf': os.path.dirname(os.path.realpath(settings_path)),
        'root': os.path.dirname(os.path.realpath(__file__)),
    })
    if 'logging' in conf.settings:
        logging.config.dictConfig(conf.settings['logging'])
    native.set_proc_name(conf.settings.get('process_name', 'mantabot'))
    plugins.registry.load()

    sys.exit(management.run_command(sys.argv[1:]))
