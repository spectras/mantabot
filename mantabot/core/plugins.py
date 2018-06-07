import importlib
from mantabot import conf

AUTO_IMPORT = ('commands', 'models')

class Plugin(object):
    def __init__(self, path):
        self.path = path
        self.module = importlib.import_module(path)

        for submodule in AUTO_IMPORT:
            try:
                importlib.import_module('%s.%s' % (path, submodule))
            except ImportError:
                pass


class Registry(object):
    plugins = None

    def __iter__(self):
        assert self.plugins is not None, 'plugins must be loaded before'
        return iter(self.plugins)

    def load(self):
        assert self.plugins is None, 'plugins have already been loaded'
        try:
            plugin_paths = conf.settings['plugins']
        except KeyError:
            raise conf.ConfigurationError('Missing plugin list')
        self.plugins = [Plugin(path) for path in plugin_paths]

registry = Registry()
