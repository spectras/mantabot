import argparse, sys

# ==============================================================

REGISTRY = {}

class Command(object):
    help = None

    def add_arguments(self, parser):
        pass

    def handle(self, **kwargs):
        raise NotImplementedError()

    def write(self, *args, **kwargs):
        print(*args, **kwargs)

    @staticmethod
    def register(klass):
        global REGISTRY
        REGISTRY[getattr(klass, 'name', klass.__name__).lower()] = klass
        return klass

def run_command(args):
    if not args or args[0] == 'help':
        longest = max(len(name) for name in REGISTRY.keys())
        print('\n'.join(sorted('%s -- %s' % (name.ljust(longest), command.help)
                               for name, command in REGISTRY.items())))
        return 0

    try:
        klass = REGISTRY[args[0].lower()]
    except KeyError:
        print('No such command "%s"' % args[0], file=sys.stderr)
        return 1

    command = klass()
    parser = argparse.ArgumentParser()
    command.add_arguments(parser)
    result = parser.parse_args(args[1:])
    return command.handle(**vars(result))

# hardcode core management commands
import mantabot.core.run
import mantabot.core.managedb
