import string

settings = None

class ConfigurationError(RuntimeError):
    pass


def load(path, context):
    """ Load configuration from a yaml file """
    global settings
    with open(path, 'r') as sf:
        template = string.Template(sf.read())

    # do this here to avoid keeping a ref to yaml module
    import yaml
    class Loader(yaml.Loader):
        pass
    Loader.add_constructor('tag:yaml.org,2002:seq', Loader.construct_python_tuple)

    loader = Loader(template.safe_substitute(**context))
    try:
        settings = loader.get_single_data()
    finally:
        loader.dispose()
